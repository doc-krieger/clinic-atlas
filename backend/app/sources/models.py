from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.notes.models import NoteSource


class RawSource(SQLModel, table=True):
    __tablename__ = "raw_sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    file_path: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    content: str = Field(default="")
    content_hash: Optional[str] = Field(default=None, index=True)
    mime_type: Optional[str] = None
    parse_status: str = Field(default="pending")  # pending, parsed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # search_vector is GENERATED ALWAYS AS -- NOT modeled in SQLModel

    note_sources: list["NoteSource"] = Relationship(back_populates="raw_source")
