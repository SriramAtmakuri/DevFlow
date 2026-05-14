"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("path", sa.Text),
        sa.Column("name", sa.Text),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("indexed_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_sources_status", "sources", ["status"])
    op.create_index("idx_sources_created", "sources", ["created_at"])

    op.create_table(
        "documents",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id")),
        sa.Column("title", sa.Text),
        sa.Column("url", sa.Text),
        sa.Column("content_preview", sa.Text),
        sa.Column("indexed_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_documents_source", "documents", ["source_id"])

    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("results_count", sa.Integer),
        sa.Column("cached", sa.Integer, server_default="0"),
        sa.Column("model", sa.String(50), server_default="gemini-flash"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_history_created", "search_history", ["created_at"])
    op.create_index("idx_history_model", "search_history", ["model"])

    op.create_table(
        "collections",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "source_collections",
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("collection_id", sa.Integer, sa.ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "index_jobs",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("filename", sa.Text),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("chunks", sa.Integer, server_default="0"),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("index_jobs")
    op.drop_table("source_collections")
    op.drop_table("collections")
    op.drop_index("idx_history_model", "search_history")
    op.drop_index("idx_history_created", "search_history")
    op.drop_table("search_history")
    op.drop_index("idx_documents_source", "documents")
    op.drop_table("documents")
    op.drop_index("idx_sources_created", "sources")
    op.drop_index("idx_sources_status", "sources")
    op.drop_table("sources")
