import logging
import os

import httpx
from fastapi import APIRouter, Depends
from sqlmodel import Session, text

from app.config import Settings
from app.database import get_session
from app.notes.service import reindex_from_disk

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["health"])

# Short timeout for health probes (addresses review concern: health endpoint timeouts)
HEALTH_PROBE_TIMEOUT = 3.0


@router.get("/health")
async def health(session: Session = Depends(get_session)):
    settings = Settings()
    checks: dict = {}

    # Postgres
    try:
        session.exec(text("SELECT 1"))
        checks["postgres"] = {"status": "ok"}
    except Exception as e:
        checks["postgres"] = {"status": "error", "detail": str(e)}

    # Ollama -- short timeout, reports "unavailable" not "error" for startup lag
    try:
        async with httpx.AsyncClient(timeout=HEALTH_PROBE_TIMEOUT) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            checks["ollama"] = {
                "status": "ok" if resp.status_code == 200 else "degraded"
            }
    except httpx.TimeoutException:
        checks["ollama"] = {
            "status": "unavailable",
            "detail": "timeout after 3s",
        }
    except Exception:
        checks["ollama"] = {"status": "unavailable"}

    # SearXNG -- short timeout, reports "unavailable" not "error" for startup lag
    try:
        async with httpx.AsyncClient(timeout=HEALTH_PROBE_TIMEOUT) as client:
            resp = await client.get(f"{settings.searxng_url}/healthz")
            checks["searxng"] = {
                "status": "ok" if resp.status_code == 200 else "degraded"
            }
    except httpx.TimeoutException:
        checks["searxng"] = {
            "status": "unavailable",
            "detail": "timeout after 3s",
        }
    except Exception:
        checks["searxng"] = {"status": "unavailable"}

    # Disk volumes
    for name, path in [
        ("notes", settings.clinic_atlas_notes_dir),
        ("sources", settings.clinic_atlas_sources_dir),
    ]:
        checks[f"disk_{name}"] = {
            "status": "ok" if os.path.isdir(path) else "error",
            "path": path,
        }

    # Overall: "ok" if postgres is up, "degraded" if postgres up but optional
    # services down, "error" if postgres is down
    postgres_ok = checks.get("postgres", {}).get("status") == "ok"
    if not postgres_ok:
        overall = "error"
    elif all(
        checks[k].get("status") in ("ok", None)
        for k in checks
        if k != "postgres"
    ):
        overall = "ok"
    else:
        overall = "degraded"

    return {"status": overall, "checks": checks}


@router.post("/reindex")
def reindex(session: Session = Depends(get_session)):
    """Rebuild notes table from disk markdown files.

    NOTE: This only syncs the `notes` table. Raw sources (PDFs, URLs) in
    data/sources/ are managed by the ingestion pipeline, not reindex.
    """
    settings = Settings()
    stats = reindex_from_disk(session, settings.clinic_atlas_notes_dir)
    return {"status": "ok", "stats": stats}
