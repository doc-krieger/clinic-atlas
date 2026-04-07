import logging
import os
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.health.router import router as health_router
from app.search.router import router as search_router
from app.sources.registry import load_source_registry
from app.sources.router import router as sources_router

logger = logging.getLogger(__name__)
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Alembic migrations on startup
    # This ensures schema is always up-to-date after `docker compose up`
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),  # backend/ directory
        )
        if result.returncode == 0:
            logger.info("Alembic migrations applied successfully")
        else:
            logger.error("Alembic migration failed: %s", result.stderr)
            raise RuntimeError(f"Alembic migration failed: {result.stderr}")
    except FileNotFoundError:
        logger.error("Alembic not found -- cannot verify database schema")
        raise

    # D-21: Auto-create directories on startup
    for dir_path in [
        os.path.join(settings.clinic_atlas_notes_dir, "topics"),
        os.path.join(settings.clinic_atlas_notes_dir, "sources"),
        os.path.join(settings.clinic_atlas_notes_dir, "logs"),
        settings.clinic_atlas_sources_dir,
    ]:
        os.makedirs(dir_path, exist_ok=True)
        logger.info("Ensured directory exists: %s", dir_path)

    # Load source registry at startup
    try:
        registry = load_source_registry(settings.clinic_atlas_sources_file)
        logger.info("Loaded %d trusted sources from registry", len(registry.all_sources))
    except Exception as e:
        logger.warning("Failed to load source registry: %s", e)

    yield


app = FastAPI(title="Clinic Atlas", lifespan=lifespan)

# D-42: CORS for direct frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(search_router)
app.include_router(sources_router)
