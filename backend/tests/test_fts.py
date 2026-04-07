"""Full-text search tests with medical thesaurus -- HTN smoke test, spelling variants, ranking."""

from sqlalchemy import text
from sqlmodel import Session

from app.notes.models import Note, NoteStatus, NoteType
from app.search.service import search_notes


def _insert_note(
    session: Session,
    slug: str,
    title: str,
    content: str,
    note_type: NoteType = NoteType.topic_note,
) -> Note:
    """Helper to insert a note and flush so search_vector is generated."""
    note = Note(
        slug=slug,
        title=title,
        content=content,
        type=note_type,
        status=NoteStatus.draft,
    )
    session.add(note)
    session.flush()
    return note


def test_htn_expands_to_hypertension(session: Session):
    """EXPLICIT HTN SMOKE TEST: searching 'htn' finds 'hypertension' note via thesaurus."""
    _insert_note(
        session,
        slug="hypertension-mgmt",
        title="Hypertension Management",
        content="Treatment of elevated blood pressure",
    )
    results = search_notes(session, "htn")
    assert len(results) > 0, "HTN search should find hypertension note via thesaurus"
    assert any(
        "hypertension" in r["title"].lower() for r in results
    ), "Result should include hypertension note"


def test_plainto_tsquery_medical_config_htn(session: Session):
    """Verify the medical thesaurus expands HTN to hypertension at the query level."""
    result = session.exec(
        text("SELECT plainto_tsquery('medical', 'htn')::text AS query_text")
    )
    query_text = result.one()[0]
    assert "hypertens" in query_text.lower(), (
        f"Medical thesaurus should expand 'htn' to contain 'hypertens', got: {query_text}"
    )


def test_hypertension_direct_search(session: Session):
    """Searching 'hypertension' directly returns hypertension note."""
    _insert_note(
        session,
        slug="hypertension-direct",
        title="Hypertension Management",
        content="Treatment of elevated blood pressure",
    )
    results = search_notes(session, "hypertension")
    assert len(results) > 0, "Direct hypertension search should return results"


def test_anaemia_anemia_spelling_variant(session: Session):
    """Searching 'anemia' finds content with 'anaemia' (D-13 spelling variant)."""
    _insert_note(
        session,
        slug="anaemia-note",
        title="Iron Deficiency Anaemia",
        content="Management of iron deficiency anaemia in adults",
    )
    results = search_notes(session, "anemia")
    assert len(results) > 0, (
        "Searching 'anemia' should find 'anaemia' content via thesaurus/stemming"
    )


def test_title_weight_higher_than_content(session: Session):
    """Title match (weight A) should rank higher than content-only match (weight D)."""
    _insert_note(
        session,
        slug="diabetes-title",
        title="Diabetes Management Guidelines",
        content="General clinical guidelines for metabolic conditions",
    )
    _insert_note(
        session,
        slug="diabetes-content",
        title="Metabolic Conditions Overview",
        content="This guide covers diabetes mellitus type 2 management",
    )
    results = search_notes(session, "diabetes")
    assert len(results) >= 2, "Should find both notes"
    # Title match should rank first
    assert results[0]["slug"] == "diabetes-title", (
        f"Title match should rank higher, got: {results[0]['slug']}"
    )


def test_full_migration_insert_search_integration(session: Session):
    """Full integration test: migration applied, insert note, search returns it.

    Verifies the complete path: Alembic migration has been applied (tables exist),
    insert a note with clinical content, search finds it via FTS pipeline
    including generated tsvector column and GIN index.
    """
    _insert_note(
        session,
        slug="neonatal-jaundice",
        title="Neonatal Jaundice",
        content="Assessment and management of neonatal jaundice in newborns",
    )
    results = search_notes(session, "jaundice")
    assert len(results) > 0, "Search should find the jaundice note"
    assert results[0]["slug"] == "neonatal-jaundice"
