from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.notes.models import NoteSource


class RawSource(SQLModel, table=True):
    __tablename__ = "raw_sources"

    id: int | None = Field(default=None, primary_key=True)
    file_path: str | None = None
    url: str | None = None
    title: str | None = None
    content: str = Field(default="")
    content_hash: str | None = Field(default=None, index=True)
    mime_type: str | None = None
    parse_status: str = Field(default="pending")  # pending, parsed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # search_vector is GENERATED ALWAYS AS -- NOT modeled in SQLModel

    note_sources: list["NoteSource"] = Relationship(back_populates="raw_source")
