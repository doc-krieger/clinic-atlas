import enum
from datetime import datetime
from typing import TYPE_CHECKING

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

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(max_length=255, unique=True, index=True)
    title: str
    content: str = Field(default="")
    type: NoteType
    status: NoteStatus = Field(default=NoteStatus.draft)
    tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String), default=[]))
    version: int = Field(default=1)  # D-09
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # search_vector is GENERATED ALWAYS AS -- NOT modeled in SQLModel (Pitfall 3)
    # Created via raw SQL in Alembic migration

    note_sources: list["NoteSource"] = Relationship(back_populates="note")


class NoteSource(SQLModel, table=True):
    """Junction table linking notes to raw sources with citation metadata (D-03)."""

    __tablename__ = "note_sources"

    id: int | None = Field(default=None, primary_key=True)
    note_id: int = Field(foreign_key="notes.id", index=True)
    raw_source_id: int = Field(foreign_key="raw_sources.id", index=True)
    page_number: int | None = None
    section_heading: str | None = None
    quote_excerpt: str | None = None

    note: Note | None = Relationship(back_populates="note_sources")
    raw_source: "RawSource | None" = Relationship(back_populates="note_sources")
