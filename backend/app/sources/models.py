from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, JSON
from sqlmodel import Field, Relationship, SQLModel

from app.notes.models import NoteSource


class RawSource(SQLModel, table=True):
    __tablename__ = "raw_sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    file_path: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    content: str = Field(default="")
    content_hash: Optional[str] = Field(
        default=None,
        sa_column=Column(String, unique=True, index=True, nullable=True),
    )
    mime_type: Optional[str] = None
    parse_status: str = Field(default="pending")  # pending, parsed, failed
    page_count: Optional[int] = None  # D-04: PDF page count
    source_type: str = Field(default="pdf")  # "pdf" | "url" | "search"
    author: Optional[str] = None  # D-04: extracted from PDF metadata
    quality_flags: list[str] = Field(
        default=[],
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )
    # Persisted warnings: ["scanned_pdf", "thin_content", "js_fallback_used"]
    # Addresses review HIGH: quality flags must not be transient SSE-only state
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # NOTE: onupdate only fires for ORM-level updates (SQLAlchemy unit-of-work).
    # Raw SQL or bulk operations will NOT update this field automatically.
    # Add a database trigger if non-ORM write paths are introduced.
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    # search_vector is GENERATED ALWAYS AS -- NOT modeled in SQLModel

    note_sources: list["NoteSource"] = Relationship(back_populates="raw_source")
