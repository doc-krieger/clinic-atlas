from fastapi import APIRouter

from app.config import Settings
from app.sources.registry import load_source_registry

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("/registry")
def get_registry():
    settings = Settings()
    registry = load_source_registry(settings.clinic_atlas_sources_file)
    return {
        "sources": [s.model_dump() for s in registry.all_sources],
        "count": len(registry.all_sources),
    }
