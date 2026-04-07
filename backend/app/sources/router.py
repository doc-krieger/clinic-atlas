from functools import lru_cache

from fastapi import APIRouter, Depends

from app.config import Settings
from app.sources.registry import SourceRegistry, load_source_registry

router = APIRouter(prefix="/api/sources", tags=["sources"])


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def _load_registry(sources_file: str) -> SourceRegistry:
    return load_source_registry(sources_file)


def get_registry(settings: Settings = Depends(get_settings)) -> SourceRegistry:
    return _load_registry(settings.clinic_atlas_sources_file)


@router.get("/registry")
def get_registry_endpoint(registry: SourceRegistry = Depends(get_registry)):
    return {
        "sources": [s.model_dump() for s in registry.all_sources],
        "count": len(registry.all_sources),
    }
