"""Initial schema with FTS and medical thesaurus

Revision ID: 001
Revises:
Create Date: 2026-04-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel  # noqa: F401
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- Idempotent FTS configuration creation ----
    # This also exists in scripts/init-postgres.sql for Docker environments.
    # Having it here ensures non-Docker environments (e.g., tests) also get FTS config.
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_ts_dict WHERE dictname = 'medical_thesaurus') THEN
            EXECUTE 'CREATE TEXT SEARCH DICTIONARY medical_thesaurus (
              TEMPLATE = thesaurus,
              DictFile = medical_thesaurus,
              Dictionary = english_stem
            )';
          END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'medical') THEN
            CREATE TEXT SEARCH CONFIGURATION medical (COPY = english);
            ALTER TEXT SEARCH CONFIGURATION medical
              ALTER MAPPING FOR asciiword, asciihword, hword_asciipart
              WITH medical_thesaurus, english_stem;
          END IF;
        END $$;
        """
    )

    # ---- Notes table (D-01, D-04) ----
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "type",
            sa.String(),
            nullable=False,
            comment="source_note, topic_note, research_log",
        ),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("tags", sa.ARRAY(sa.String()), server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "type IN ('source_note', 'topic_note', 'research_log')",
            name="ck_notes_type",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'archived')",
            name="ck_notes_status",
        ),
    )

    # ---- Raw Sources table (D-02) ----
    op.create_table(
        "raw_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_hash", sa.String(), nullable=True, index=True),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column(
            "parse_status",
            sa.String(),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ---- Note Sources junction table (D-03) ----
    op.create_table(
        "note_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("notes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "raw_source_id",
            sa.Integer(),
            sa.ForeignKey("raw_sources.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_heading", sa.String(), nullable=True),
        sa.Column("quote_excerpt", sa.Text(), nullable=True),
    )

    # ---- Research Sessions table (D-07) ----
    op.create_table(
        "research_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column(
            "messages",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ---- tsvector GENERATED ALWAYS AS columns with GIN indexes (D-05, D-06) ----
    # Notes: weighted search -- title at weight A, content at weight D
    op.execute(
        """
        ALTER TABLE notes ADD COLUMN search_vector TSVECTOR
        GENERATED ALWAYS AS (
            setweight(to_tsvector('medical', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('medical', coalesce(content, '')), 'D')
        ) STORED;
        """
    )
    op.execute(
        "CREATE INDEX idx_notes_search ON notes USING GIN (search_vector);"
    )

    # Raw sources: single-weight search
    op.execute(
        """
        ALTER TABLE raw_sources ADD COLUMN search_vector TSVECTOR
        GENERATED ALWAYS AS (
            to_tsvector('medical', coalesce(title, '') || ' ' || coalesce(content, ''))
        ) STORED;
        """
    )
    op.execute(
        "CREATE INDEX idx_raw_sources_search ON raw_sources USING GIN (search_vector);"
    )


def downgrade() -> None:
    op.drop_index("idx_raw_sources_search", table_name="raw_sources")
    op.drop_index("idx_notes_search", table_name="notes")
    op.drop_table("research_sessions")
    op.drop_table("note_sources")
    op.drop_table("raw_sources")
    op.drop_table("notes")

    # Drop FTS configuration and dictionary
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS medical;")
    op.execute("DROP TEXT SEARCH DICTIONARY IF EXISTS medical_thesaurus;")
