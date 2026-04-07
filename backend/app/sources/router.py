"""Source ingestion API endpoints: upload, fetch, search, list, registry."""

import json
import os
from collections.abc import AsyncGenerator
from functools import lru_cache
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.routing import format_sse_event
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlmodel import Session, desc, select

from app.config import Settings
from app.database import get_session
from app.sources.models import RawSource
from app.sources.registry import SourceRegistry, load_source_registry
from app.sources.schemas import (
    SearchRequest,
    SourceListItem,
    UrlFetchRequest,
)
from app.sources.searxng import search_searxng
from app.sources.service import fetch_and_parse_url, parse_pdf

router = APIRouter(prefix="/api/sources", tags=["sources"])


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def _load_registry(sources_file: str) -> SourceRegistry:
    return load_source_registry(sources_file)


def get_registry(settings: Settings = Depends(get_settings)) -> SourceRegistry:
    return _load_registry(settings.clinic_atlas_sources_file)


def _sse_to_bytes(event: ServerSentEvent) -> bytes:
    """Convert a ServerSentEvent to wire-format bytes for StreamingResponse.

    When returning EventSourceResponse(generator), FastAPI treats it as a plain
    StreamingResponse, so we must format SSE events ourselves.
    """
    data_str = None
    if event.data is not None:
        if isinstance(event.data, str):
            data_str = event.data
        else:
            data_str = json.dumps(event.data)
    return format_sse_event(
        data_str=data_str,
        event=event.event,
        id=event.id,
        retry=event.retry,
        comment=event.comment,
    )


# ---------------------------------------------------------------------------
# GET /api/sources -- List indexed sources (addresses review HIGH)
# ---------------------------------------------------------------------------


@router.get("")
def list_sources(session: Session = Depends(get_session)):
    """Return all ingested sources, most recent first."""
    sources = session.exec(
        select(RawSource).order_by(desc(RawSource.created_at))
    ).all()
    return {
        "sources": [
            SourceListItem(
                id=s.id,
                title=s.title,
                author=s.author,
                source_type=s.source_type,
                parse_status=s.parse_status,
                quality_flags=s.quality_flags,
                page_count=s.page_count,
                url=s.url,
                created_at=s.created_at.isoformat(),
            ).model_dump()
            for s in sources
        ],
        "count": len(sources),
    }


# ---------------------------------------------------------------------------
# POST /api/sources/upload -- PDF upload with SSE progress (SRCI-01, D-14)
# ---------------------------------------------------------------------------


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """Upload a PDF file. Returns SSE stream with progress, complete, or error events.

    Validation happens before SSE streaming starts so errors return proper HTTP codes.
    """
    # Validate file extension (T-02-01)
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Validate MIME type (T-02-01)
    if file.content_type and not file.content_type.startswith("application/pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF (application/pdf).")

    # Validate file size (D-03)
    if file.size and file.size > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"This file exceeds the {settings.max_upload_size_mb} MB limit.",
        )

    # Save uploaded file to temp path
    sources_dir = settings.clinic_atlas_sources_dir
    os.makedirs(sources_dir, exist_ok=True)
    tmp_filename = f".tmp_{uuid4()}.pdf"
    tmp_path = os.path.join(sources_dir, tmp_filename)

    try:
        content = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.")

    # Double-check size after reading (in case file.size was not set)
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"This file exceeds the {settings.max_upload_size_mb} MB limit.",
        )

    with open(tmp_path, "wb") as f:
        f.write(content)

    async def generate() -> AsyncGenerator[bytes, None]:
        try:
            async for event in parse_pdf(
                file_path=tmp_path,
                filename=file.filename or "upload.pdf",
                session=session,
                settings=settings,
            ):
                yield _sse_to_bytes(event)
        except Exception as e:
            yield _sse_to_bytes(ServerSentEvent(data={"error": str(e)}, event="error"))
        finally:
            # Clean up temp file if it still exists (atomic write in service moves it)
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except OSError:
                pass

    return EventSourceResponse(generate())


# ---------------------------------------------------------------------------
# POST /api/sources/fetch -- URL fetch with SSE progress (SRCI-02, D-14)
# ---------------------------------------------------------------------------


@router.post("/fetch")
async def fetch_url(
    request: UrlFetchRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """Fetch a URL, extract content. Returns SSE stream with progress events."""

    async def generate() -> AsyncGenerator[bytes, None]:
        try:
            async for event in fetch_and_parse_url(
                url=str(request.url),
                session=session,
                settings=settings,
            ):
                yield _sse_to_bytes(event)
        except Exception as e:
            yield _sse_to_bytes(ServerSentEvent(data={"error": str(e)}, event="error"))

    return EventSourceResponse(generate())


# ---------------------------------------------------------------------------
# POST /api/sources/search -- SearXNG search (SRCI-05, D-14)
# ---------------------------------------------------------------------------


@router.post("/search")
async def search_sources(
    request: SearchRequest,
    registry: SourceRegistry = Depends(get_registry),
    settings: Settings = Depends(get_settings),
):
    """Search trusted source domains via SearXNG. Returns JSON (not SSE -- search is fast)."""
    domains = [s.domain for s in registry.all_sources]
    results = await search_searxng(
        query=request.query,
        domains=domains,
        searxng_url=settings.searxng_url,
        limit=request.limit,
    )
    return {"results": [r.model_dump() for r in results]}


# ---------------------------------------------------------------------------
# GET /api/sources/registry -- Existing endpoint (preserved)
# ---------------------------------------------------------------------------


@router.get("/registry")
def get_registry_endpoint(registry: SourceRegistry = Depends(get_registry)):
    return {
        "sources": [s.model_dump() for s in registry.all_sources],
        "count": len(registry.all_sources),
    }
