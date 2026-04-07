import logging
import os
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings

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
            # Don't crash -- let health endpoint report degraded status
    except FileNotFoundError:
        logger.warning("Alembic not found -- skipping auto-migration (dev without uv?)")

    # D-21: Auto-create directories on startup
    for dir_path in [
        os.path.join(settings.clinic_atlas_notes_dir, "topics"),
        os.path.join(settings.clinic_atlas_notes_dir, "sources"),
        os.path.join(settings.clinic_atlas_notes_dir, "logs"),
        settings.clinic_atlas_sources_dir,
    ]:
        os.makedirs(dir_path, exist_ok=True)
        logger.info("Ensured directory exists: %s", dir_path)
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


# Minimal health endpoint (expanded in Plan 02)
@app.get("/api/health")
async def health():
    return {"status": "ok"}
