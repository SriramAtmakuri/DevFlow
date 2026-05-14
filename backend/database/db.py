from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database.engine import engine
from database.models import metadata


class Database:
    def __init__(self):
        metadata.create_all(engine)

    @contextmanager
    def _conn(self):
        with engine.begin() as conn:
            yield conn

    @staticmethod
    def _rows(result) -> List[Dict]:
        return [dict(r._mapping) for r in result.fetchall()]

    @staticmethod
    def _row(result) -> Optional[Dict]:
        r = result.fetchone()
        return dict(r._mapping) if r else None

    # ── Sources ───────────────────────────────────────────────────────────────

    def add_source(self, source_type: str, path: str = None, name: str = None) -> int:
        with self._conn() as conn:
            result = conn.execute(
                text("INSERT INTO sources (type, path, name, status) VALUES (:type, :path, :name, 'indexing') RETURNING id"),
                {"type": source_type, "path": path, "name": name},
            )
            return result.scalar()

    def update_source_status(self, source_id: int, status: str):
        with self._conn() as conn:
            conn.execute(
                text("UPDATE sources SET status=:status, indexed_at=:now WHERE id=:id"),
                {"status": status, "now": datetime.now().isoformat(), "id": source_id},
            )

    def add_document(self, doc_id: str, source_id: int, title: str, url: str = None, content_preview: str = None):
        with self._conn() as conn:
            conn.execute(
                text("""
                    INSERT INTO documents (id, source_id, title, url, content_preview)
                    VALUES (:id, :source_id, :title, :url, :preview)
                    ON CONFLICT (id) DO UPDATE SET
                        source_id=EXCLUDED.source_id, title=EXCLUDED.title,
                        url=EXCLUDED.url, content_preview=EXCLUDED.content_preview
                """),
                {"id": doc_id, "source_id": source_id, "title": title, "url": url, "preview": content_preview},
            )

    def get_sources(self, collection_id: Optional[int] = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        with self._conn() as conn:
            if collection_id:
                result = conn.execute(text("""
                    SELECT s.*, COUNT(d.id) as doc_count FROM sources s
                    JOIN source_collections sc ON s.id = sc.source_id
                    LEFT JOIN documents d ON s.id = d.source_id
                    WHERE sc.collection_id = :cid
                    GROUP BY s.id ORDER BY s.created_at DESC LIMIT :limit OFFSET :offset
                """), {"cid": collection_id, "limit": limit, "offset": offset})
            else:
                result = conn.execute(text("""
                    SELECT s.*, COUNT(d.id) as doc_count FROM sources s
                    LEFT JOIN documents d ON s.id = d.source_id
                    GROUP BY s.id ORDER BY s.created_at DESC LIMIT :limit OFFSET :offset
                """), {"limit": limit, "offset": offset})
            return self._rows(result)

    def delete_source(self, source_id: int):
        with self._conn() as conn:
            conn.execute(text("DELETE FROM documents WHERE source_id=:id"), {"id": source_id})
            conn.execute(text("DELETE FROM source_collections WHERE source_id=:id"), {"id": source_id})
            conn.execute(text("DELETE FROM sources WHERE id=:id"), {"id": source_id})

    # ── Search history ────────────────────────────────────────────────────────

    def add_search(self, query: str, results_count: int, cached: bool = False, model: str = "gemini-flash"):
        with self._conn() as conn:
            conn.execute(
                text("INSERT INTO search_history (query, results_count, cached, model) VALUES (:q, :rc, :cached, :model)"),
                {"q": query, "rc": results_count, "cached": int(cached), "model": model},
            )
            conn.execute(text("""
                DELETE FROM search_history WHERE id NOT IN (
                    SELECT id FROM search_history ORDER BY created_at DESC LIMIT 5000
                )
            """))

    def get_search_history(self, limit: int = 50) -> List[Dict]:
        with self._conn() as conn:
            result = conn.execute(
                text("SELECT * FROM search_history ORDER BY created_at DESC LIMIT :limit"),
                {"limit": limit},
            )
            return self._rows(result)

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        with self._conn() as conn:
            sources = conn.execute(text("SELECT COUNT(*) FROM sources WHERE status='indexed'")).scalar()
            docs = conn.execute(text("SELECT COUNT(*) FROM documents")).scalar()
            searches = conn.execute(text("SELECT COUNT(*) FROM search_history")).scalar()
            return {"sources": sources, "documents": docs, "searches": searches}

    def get_analytics(self) -> Dict:
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        with self._conn() as conn:
            top_queries = self._rows(conn.execute(text("""
                SELECT query, COUNT(*) as count FROM search_history
                GROUP BY query ORDER BY count DESC LIMIT 10
            """)))

            searches_by_day = self._rows(conn.execute(text("""
                SELECT DATE(created_at) as date, COUNT(*) as count,
                       SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cache_hits
                FROM search_history
                WHERE created_at >= :cutoff
                GROUP BY DATE(created_at) ORDER BY date
            """), {"cutoff": cutoff}))

            source_types = self._rows(conn.execute(text(
                "SELECT type, COUNT(*) as count FROM sources GROUP BY type"
            )))

            cache_row = conn.execute(
                text("SELECT COUNT(*) as total, SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as hits FROM search_history")
            ).fetchone()
            total = cache_row[0] or 0
            hits = cache_row[1] or 0
            cache_rate = round((hits / total * 100) if total > 0 else 0, 1)

            model_usage = self._rows(conn.execute(text(
                "SELECT model, COUNT(*) as count FROM search_history GROUP BY model"
            )))

            return {
                "top_queries": top_queries,
                "searches_by_day": searches_by_day,
                "source_types": source_types,
                "cache_hit_rate": cache_rate,
                "model_usage": model_usage,
            }

    # ── Collections ───────────────────────────────────────────────────────────

    def create_collection(self, name: str, description: str = None) -> int:
        with self._conn() as conn:
            result = conn.execute(
                text("INSERT INTO collections (name, description) VALUES (:name, :desc) RETURNING id"),
                {"name": name, "desc": description},
            )
            return result.scalar()

    def get_collections(self) -> List[Dict]:
        with self._conn() as conn:
            result = conn.execute(text("""
                SELECT c.*, COUNT(sc.source_id) as source_count
                FROM collections c
                LEFT JOIN source_collections sc ON c.id = sc.collection_id
                GROUP BY c.id ORDER BY c.created_at DESC
            """))
            return self._rows(result)

    def delete_collection(self, collection_id: int):
        with self._conn() as conn:
            conn.execute(text("DELETE FROM source_collections WHERE collection_id=:id"), {"id": collection_id})
            conn.execute(text("DELETE FROM collections WHERE id=:id"), {"id": collection_id})

    def add_source_to_collection(self, source_id: int, collection_id: int):
        with self._conn() as conn:
            conn.execute(text("""
                INSERT INTO source_collections (source_id, collection_id) VALUES (:sid, :cid)
                ON CONFLICT (source_id, collection_id) DO NOTHING
            """), {"sid": source_id, "cid": collection_id})

    def remove_source_from_collection(self, source_id: int, collection_id: int):
        with self._conn() as conn:
            conn.execute(
                text("DELETE FROM source_collections WHERE source_id=:sid AND collection_id=:cid"),
                {"sid": source_id, "cid": collection_id},
            )

    # ── Index jobs ────────────────────────────────────────────────────────────

    def create_job(self, job_id: str, filename: str):
        with self._conn() as conn:
            conn.execute(
                text("INSERT INTO index_jobs (id, filename, status) VALUES (:id, :fn, 'pending')"),
                {"id": job_id, "fn": filename},
            )

    def update_job(self, job_id: str, status: str, chunks: int = 0, error: str = None):
        with self._conn() as conn:
            completed_at = datetime.now().isoformat() if status != "pending" else None
            conn.execute(
                text("UPDATE index_jobs SET status=:status, chunks=:chunks, error=:error, completed_at=:completed_at WHERE id=:id"),
                {"status": status, "chunks": chunks, "error": error, "completed_at": completed_at, "id": job_id},
            )

    def get_job(self, job_id: str) -> Optional[Dict]:
        with self._conn() as conn:
            result = conn.execute(text("SELECT * FROM index_jobs WHERE id=:id"), {"id": job_id})
            return self._row(result)
