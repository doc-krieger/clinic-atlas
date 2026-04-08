import logging
import os

import frontmatter
from sqlmodel import Session, select

from app.notes.models import Note, NoteStatus, NoteType

logger = logging.getLogger(__name__)


def reindex_from_disk(session: Session, notes_dir: str) -> dict:
    """Rebuild Postgres note records from disk markdown files (D-23).

    Maps disk directories to note types:
      notes/topics/  -> NoteType.topic_note
      notes/sources/ -> NoteType.source_note
      notes/logs/    -> NoteType.research_log

    NOTE: This only syncs the `notes` table from disk .md files.
    The `raw_sources` table is populated by the ingestion pipeline (Phase 2),
    not by reindex. Raw uploaded files in data/sources/ are binary/PDF/HTML,
    not markdown notes.
    """
    stats: dict = {"scanned": 0, "upserted": 0, "errors": []}
    type_dirs = {
        "topics": NoteType.topic_note,
        "sources": NoteType.source_note,
        "logs": NoteType.research_log,
    }

    for subdir, note_type in type_dirs.items():
        dir_path = os.path.join(notes_dir, subdir)
        if not os.path.isdir(dir_path):
            continue
        for filename in os.listdir(dir_path):
            if not filename.endswith(".md"):
                continue
            stats["scanned"] += 1
            file_path = os.path.join(dir_path, filename)
            try:
                post = frontmatter.load(file_path)
                slug = post.metadata.get("slug", filename[:-3])
                with session.begin_nested():
                    existing = session.exec(
                        select(Note).where(Note.slug == slug)
                    ).first()
                    if existing:
                        existing.title = post.metadata.get("title", slug)
                        existing.content = post.content
                        existing.type = note_type
                        existing.status = NoteStatus(
                            post.metadata.get("status", "draft")
                        )
                        existing.tags = post.metadata.get("tags", [])
                        existing.version = post.metadata.get("version", 1)
                        session.add(existing)
                    else:
                        note = Note(
                            slug=slug,
                            title=post.metadata.get("title", slug),
                            content=post.content,
                            type=note_type,
                            status=NoteStatus(post.metadata.get("status", "draft")),
                            tags=post.metadata.get("tags", []),
                            version=post.metadata.get("version", 1),
                        )
                        session.add(note)
                    session.flush()
                stats["upserted"] += 1
            except Exception as e:
                stats["errors"].append({"file": file_path, "error": str(e)})
                logger.warning("Reindex error for %s: %s", file_path, e)
    session.commit()
    return stats
