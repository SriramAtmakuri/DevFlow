from sqlalchemy import (
    Table, Column, Integer, String, Boolean, Text,
    DateTime, MetaData, ForeignKey, Index, func,
)

metadata = MetaData()

sources = Table(
    "sources", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("type", String(50), nullable=False),
    Column("path", Text),
    Column("name", Text),
    Column("status", String(20), default="pending"),
    Column("indexed_at", DateTime),
    Column("created_at", DateTime, server_default=func.now()),
    Index("idx_sources_status", "status"),
    Index("idx_sources_created", "created_at"),
)

documents = Table(
    "documents", metadata,
    Column("id", String, primary_key=True),
    Column("source_id", Integer, ForeignKey("sources.id")),
    Column("title", Text),
    Column("url", Text),
    Column("content_preview", Text),
    Column("indexed_at", DateTime, server_default=func.now()),
    Index("idx_documents_source", "source_id"),
)

search_history = Table(
    "search_history", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("query", Text, nullable=False),
    Column("results_count", Integer),
    Column("cached", Integer, default=0),
    Column("model", String(50), default="gemini-flash"),
    Column("created_at", DateTime, server_default=func.now()),
    Index("idx_history_created", "created_at"),
    Index("idx_history_model", "model"),
)

collections = Table(
    "collections", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("created_at", DateTime, server_default=func.now()),
)

source_collections = Table(
    "source_collections", metadata,
    Column("source_id", Integer, ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True),
    Column("collection_id", Integer, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
)

index_jobs = Table(
    "index_jobs", metadata,
    Column("id", String, primary_key=True),
    Column("filename", Text),
    Column("status", String(20), default="pending"),
    Column("chunks", Integer, default=0),
    Column("error", Text),
    Column("created_at", DateTime, server_default=func.now()),
    Column("completed_at", DateTime),
)

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("username", String(255), unique=True, nullable=False),
    Column("hashed_password", Text, nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)
