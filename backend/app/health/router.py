import asyncio
import functools
import logging
import os

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session, text

from app.config import Settings
from app.database import get_session
from app.notes.service import reindex_from_disk

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["health"])


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()

# Short timeout for health probes — combined must stay under container's 5s budget
HEALTH_PROBE_TIMEOUT = 2.0

# Services where status=="error" means overall health is "error"
REQUIRED_SERVICES = {"postgres", "disk_notes", "disk_sources"}


@router.get("/health")
async def health(session: Session = Depends(get_session)):
    settings = get_settings()
    checks: dict = {}

    # Postgres
    try:
        session.exec(text("SELECT 1"))
        checks["postgres"] = {"status": "ok"}
    except Exception as e:
        checks["postgres"] = {"status": "error", "detail": str(e)}

    # Ollama + SearXNG — run concurrently to stay within probe budget
    async def probe_ollama() -> dict:
        try:
            async with httpx.AsyncClient(timeout=HEALTH_PROBE_TIMEOUT) as client:
                resp = await client.get(f"{settings.ollama_base_url}/api/tags")
                return {"status": "ok" if resp.status_code == 200 else "degraded"}
        except httpx.TimeoutException:
            return {"status": "unavailable", "detail": "timeout after 2s"}
        except Exception:
            return {"status": "unavailable"}

    async def probe_searxng() -> dict:
        try:
            async with httpx.AsyncClient(timeout=HEALTH_PROBE_TIMEOUT) as client:
                resp = await client.get(f"{settings.searxng_url}/healthz")
                return {"status": "ok" if resp.status_code == 200 else "degraded"}
        except httpx.TimeoutException:
            return {"status": "unavailable", "detail": "timeout after 2s"}
        except Exception:
            return {"status": "unavailable"}

    ollama_result, searxng_result = await asyncio.gather(
        probe_ollama(), probe_searxng()
    )
    checks["ollama"] = ollama_result
    checks["searxng"] = searxng_result

    # Disk volumes
    for name, path in [
        ("notes", settings.clinic_atlas_notes_dir),
        ("sources", settings.clinic_atlas_sources_dir),
    ]:
        checks[f"disk_{name}"] = {
            "status": "ok" if os.path.isdir(path) else "error",
        }

    # Overall: "error" if any required service reports error,
    # "degraded" if optional services are down, "ok" if all green
    required_ok = all(
        checks[k].get("status") == "ok"
        for k in checks
        if k in REQUIRED_SERVICES
    )
    all_ok = all(checks[k].get("status") == "ok" for k in checks)

    if not required_ok:
        overall = "error"
    elif all_ok:
        overall = "ok"
    else:
        overall = "degraded"

    body = {"status": overall, "checks": checks}
    status_code = 503 if overall == "error" else 200
    return JSONResponse(content=body, status_code=status_code)


@router.post("/reindex")
def reindex(session: Session = Depends(get_session)):
    """Rebuild notes table from disk markdown files.

    NOTE: This only syncs the `notes` table. Raw sources (PDFs, URLs) in
    data/sources/ are managed by the ingestion pipeline, not reindex.
    """
    settings = get_settings()
    stats = reindex_from_disk(session, settings.clinic_atlas_notes_dir)
    return {"status": "ok", "stats": stats}
