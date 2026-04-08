"""Tests for database schema integrity -- tables, columns, indexes."""

from sqlalchemy import text
from sqlmodel import Session

from app.notes.models import Note, NoteStatus, NoteType
from app.sources.models import RawSource


def test_notes_table_has_expected_columns(session: Session):
    """Notes table exists with all required columns."""
    result = session.exec(
        text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'notes'
            ORDER BY column_name
        """)
    )
    columns = {row[0] for row in result}
    expected = {
        "id",
        "slug",
        "title",
        "content",
        "type",
        "status",
        "tags",
        "version",
        "created_at",
        "updated_at",
        "search_vector",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_raw_sources_table_has_expected_columns(session: Session):
    """Raw sources table exists with all required columns."""
    result = session.exec(
        text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'raw_sources'
            ORDER BY column_name
        """)
    )
    columns = {row[0] for row in result}
    expected = {
        "id",
        "file_path",
        "url",
        "title",
        "content",
        "content_hash",
        "mime_type",
        "parse_status",
        "page_count",
        "source_type",
        "author",
        "quality_flags",
        "created_at",
        "updated_at",
        "search_vector",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_note_sources_table_has_expected_columns(session: Session):
    """Note sources junction table exists with all required columns."""
    result = session.exec(
        text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'note_sources'
            ORDER BY column_name
        """)
    )
    columns = {row[0] for row in result}
    expected = {
        "id",
        "note_id",
        "raw_source_id",
        "page_number",
        "section_heading",
        "quote_excerpt",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_gin_indexes_exist(session: Session):
    """GIN indexes exist on search_vector columns."""
    result = session.exec(
        text("""
            SELECT indexname, indexdef FROM pg_indexes
            WHERE indexname IN ('idx_notes_search', 'idx_raw_sources_search')
        """)
    )
    indexes = {row[0]: row[1] for row in result}
    assert "idx_notes_search" in indexes, "Missing GIN index on notes.search_vector"
    assert "idx_raw_sources_search" in indexes, (
        "Missing GIN index on raw_sources.search_vector"
    )
    assert "using gin" in indexes["idx_notes_search"].lower(), (
        "idx_notes_search is not a GIN index"
    )
    assert "using gin" in indexes["idx_raw_sources_search"].lower(), (
        "idx_raw_sources_search is not a GIN index"
    )


def test_research_sessions_table_has_expected_columns(session: Session):
    """Research sessions table exists with all required columns."""
    result = session.exec(
        text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'research_sessions'
            ORDER BY column_name
        """)
    )
    columns = {row[0] for row in result}
    expected = {
        "id",
        "query",
        "messages",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_insert_note_via_sqlmodel(session: Session):
    """Insert a Note record via SQLModel succeeds."""
    note = Note(
        slug="test-insert",
        title="Test Insert",
        content="Test content for insertion",
        type=NoteType.topic_note,
        status=NoteStatus.draft,
    )
    session.add(note)
    session.flush()
    assert note.id is not None


def test_insert_raw_source_via_sqlmodel(session: Session):
    """Insert a RawSource record via SQLModel succeeds."""
    source = RawSource(
        title="Test Source",
        url="https://example.com/test",
        content="Test source content",
        mime_type="text/html",
    )
    session.add(source)
    session.flush()
    assert source.id is not None
