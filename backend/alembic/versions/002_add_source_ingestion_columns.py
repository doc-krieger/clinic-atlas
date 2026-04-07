"""Add ingestion columns and content_hash unique constraint

Revision ID: 002
Revises: 001
Create Date: 2026-04-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to raw_sources
    op.add_column("raw_sources", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column(
        "raw_sources",
        sa.Column(
            "source_type",
            sa.String(),
            nullable=False,
            server_default="pdf",
        ),
    )
    op.add_column("raw_sources", sa.Column("author", sa.String(), nullable=True))
    op.add_column(
        "raw_sources",
        sa.Column(
            "quality_flags",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
    )

    # Add UNIQUE constraint on content_hash (T-02-08: prevents duplicate rows at DB level)
    # Drop existing index first since we'll create a unique constraint that implies an index
    op.drop_index("ix_raw_sources_content_hash", table_name="raw_sources")
    op.create_unique_constraint(
        "uq_raw_sources_content_hash", "raw_sources", ["content_hash"]
    )
    # Re-create as unique index for query performance
    op.create_index(
        "ix_raw_sources_content_hash",
        "raw_sources",
        ["content_hash"],
        unique=True,
    )


def downgrade() -> None:
    # Drop unique index and constraint
    op.drop_index("ix_raw_sources_content_hash", table_name="raw_sources")
    op.drop_constraint("uq_raw_sources_content_hash", "raw_sources", type_="unique")
    # Re-create original non-unique index
    op.create_index("ix_raw_sources_content_hash", "raw_sources", ["content_hash"])

    # Drop columns in reverse order
    op.drop_column("raw_sources", "quality_flags")
    op.drop_column("raw_sources", "author")
    op.drop_column("raw_sources", "source_type")
    op.drop_column("raw_sources", "page_count")
