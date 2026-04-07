from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.search.service import search_notes, search_raw_sources

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    notes = search_notes(session, q, limit)
    sources = search_raw_sources(session, q, limit)
    return {"query": q, "notes": notes, "sources": sources}
