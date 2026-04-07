import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import ARRAY, Column, Field, Relationship, SQLModel, String

if TYPE_CHECKING:
    from app.sources.models import RawSource


class NoteType(str, enum.Enum):
    source_note = "source_note"
    topic_note = "topic_note"
    research_log = "research_log"


class NoteStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    archived = "archived"


class Note(SQLModel, table=True):
    __tablename__ = "notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(max_length=255, unique=True, index=True)
    title: str
    content: str = Field(default="")
    type: NoteType
    status: NoteStatus = Field(default=NoteStatus.draft)
    tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    version: int = Field(default=1)  # D-09
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    # search_vector is GENERATED ALWAYS AS -- NOT modeled in SQLModel (Pitfall 3)
    # Created via raw SQL in Alembic migration

    note_sources: list["NoteSource"] = Relationship(back_populates="note")


class NoteSource(SQLModel, table=True):
    """Junction table linking notes to raw sources with citation metadata (D-03)."""

    __tablename__ = "note_sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    note_id: int = Field(foreign_key="notes.id", index=True)
    raw_source_id: int = Field(foreign_key="raw_sources.id", index=True)
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    quote_excerpt: Optional[str] = None

    note: Optional["Note"] = Relationship(back_populates="note_sources")
    raw_source: Optional["RawSource"] = Relationship(back_populates="note_sources")
