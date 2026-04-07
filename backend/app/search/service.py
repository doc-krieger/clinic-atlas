from sqlalchemy import text
from sqlmodel import Session


def search_notes(session: Session, query: str, limit: int = 20) -> list[dict]:
    """Full-text search on notes using medical thesaurus configuration."""
    result = session.exec(
        text("""
            SELECT id, slug, title, type, status,
                   ts_rank(search_vector, query) AS rank
            FROM notes,
                 plainto_tsquery('medical', :q) AS query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT :limit
        """),
        params={"q": query, "limit": limit},
    )
    return [dict(row._mapping) for row in result]


def search_raw_sources(session: Session, query: str, limit: int = 20) -> list[dict]:
    """Full-text search on raw sources using medical thesaurus configuration."""
    result = session.exec(
        text("""
            SELECT id, title, url, mime_type,
                   ts_rank(search_vector, query) AS rank
            FROM raw_sources,
                 plainto_tsquery('medical', :q) AS query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT :limit
        """),
        params={"q": query, "limit": limit},
    )
    return [dict(row._mapping) for row in result]
