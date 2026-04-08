from pydantic import BaseModel, Field, HttpUrl
from typing import Optional


# SSE event models (D-12)
class IngestionProgress(BaseModel):
    status: str  # "uploading" | "parsing" | "fetching" | "extracting" | "indexing" | "complete" | "error"
    page: Optional[int] = None
    total: Optional[int] = None
    message: Optional[str] = None


class IngestionComplete(BaseModel):
    id: int
    title: Optional[str] = None
    author: Optional[str] = None  # D-04: extracted from PDF metadata
    parse_status: str
    page_count: Optional[int] = None
    content_preview: str  # First 500 chars (D-13)
    source_type: str
    quality_flags: list[
        str
    ] = []  # Persisted: ["scanned_pdf", "thin_content", "js_fallback_used"]


# Request models (D-14)
class UrlFetchRequest(BaseModel):
    url: HttpUrl


class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)


# SearXNG result model (D-10)
class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    domain: str


class IngestSelectedRequest(BaseModel):
    urls: list[HttpUrl]


# Error response (D-02)
class DuplicateSourceResponse(BaseModel):
    detail: str
    existing_source_id: int


# Source list response (addresses review HIGH: missing GET /api/sources)
class SourceListItem(BaseModel):
    id: int
    title: Optional[str] = None
    author: Optional[str] = None
    source_type: str
    parse_status: str
    quality_flags: list[str] = []
    page_count: Optional[int] = None
    url: Optional[str] = None
    created_at: str  # ISO format
