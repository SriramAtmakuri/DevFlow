import sqlite3
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    def __init__(self, db_path: str = "devflow.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                path TEXT,
                name TEXT,
                status TEXT DEFAULT 'pending',
                indexed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                source_id INTEGER,
                title TEXT,
                url TEXT,
                content_preview TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES sources (id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                results_count INTEGER,
                cached BOOLEAN DEFAULT 0,
                model TEXT DEFAULT 'gemini-flash',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS source_collections (
                source_id INTEGER,
                collection_id INTEGER,
                PRIMARY KEY (source_id, collection_id),
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE,
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS index_jobs (
                id TEXT PRIMARY KEY,
                filename TEXT,
                status TEXT DEFAULT 'pending',
                chunks INTEGER DEFAULT 0,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # Migrate existing search_history — add columns if missing
        for col, definition in [("cached", "BOOLEAN DEFAULT 0"), ("model", "TEXT DEFAULT 'gemini-flash'")]:
            try:
                conn.execute(f"ALTER TABLE search_history ADD COLUMN {col} {definition}")
            except Exception:
                pass

        conn.commit()
        conn.close()

    # ── Sources ───────────────────────────────────────────────────────────────

    def add_source(self, source_type: str, path: str = None, name: str = None) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO sources (type, path, name, status) VALUES (?, ?, ?, 'indexing')",
                  (source_type, path, name))
        source_id = c.lastrowid
        conn.commit()
        conn.close()
        return source_id

    def update_source_status(self, source_id: int, status: str):
        conn = self.get_connection()
        conn.execute("UPDATE sources SET status=?, indexed_at=? WHERE id=?",
                     (status, datetime.now().isoformat(), source_id))
        conn.commit()
        conn.close()

    def add_document(self, doc_id: str, source_id: int, title: str, url: str = None, content_preview: str = None):
        conn = self.get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO documents (id, source_id, title, url, content_preview) VALUES (?,?,?,?,?)",
            (doc_id, source_id, title, url, content_preview))
        conn.commit()
        conn.close()

    def get_sources(self, collection_id: Optional[int] = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        conn = self.get_connection()
        if collection_id:
            rows = conn.execute("""
                SELECT s.*, COUNT(d.id) as doc_count FROM sources s
                JOIN source_collections sc ON s.id = sc.source_id
                LEFT JOIN documents d ON s.id = d.source_id
                WHERE sc.collection_id = ?
                GROUP BY s.id ORDER BY s.created_at DESC LIMIT ? OFFSET ?
            """, (collection_id, limit, offset)).fetchall()
        else:
            rows = conn.execute("""
                SELECT s.*, COUNT(d.id) as doc_count FROM sources s
                LEFT JOIN documents d ON s.id = d.source_id
                GROUP BY s.id ORDER BY s.created_at DESC LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()
        result = [dict(r) for r in rows]
        conn.close()
        return result

    def delete_source(self, source_id: int):
        conn = self.get_connection()
        conn.execute("DELETE FROM documents WHERE source_id=?", (source_id,))
        conn.execute("DELETE FROM source_collections WHERE source_id=?", (source_id,))
        conn.execute("DELETE FROM sources WHERE id=?", (source_id,))
        conn.commit()
        conn.close()

    # ── Search history ────────────────────────────────────────────────────────

    def add_search(self, query: str, results_count: int, cached: bool = False, model: str = "gemini-flash"):
        conn = self.get_connection()
        conn.execute(
            "INSERT INTO search_history (query, results_count, cached, model) VALUES (?,?,?,?)",
            (query, results_count, int(cached), model))
        conn.commit()
        conn.close()

    def get_search_history(self, limit: int = 50) -> List[Dict]:
        conn = self.get_connection()
        rows = conn.execute(
            "SELECT * FROM search_history ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        result = [dict(r) for r in rows]
        conn.close()
        return result

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        conn = self.get_connection()
        sources = conn.execute("SELECT COUNT(*) FROM sources WHERE status='indexed'").fetchone()[0]
        docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        searches = conn.execute("SELECT COUNT(*) FROM search_history").fetchone()[0]
        conn.close()
        return {"sources": sources, "documents": docs, "searches": searches}

    def get_analytics(self) -> Dict:
        conn = self.get_connection()

        # Top 10 queries
        top_queries = [dict(r) for r in conn.execute("""
            SELECT query, COUNT(*) as count FROM search_history
            GROUP BY query ORDER BY count DESC LIMIT 10
        """).fetchall()]

        # Searches per day (last 7 days)
        searches_by_day = [dict(r) for r in conn.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count,
                   SUM(cached) as cache_hits
            FROM search_history
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at) ORDER BY date
        """).fetchall()]

        # Source types breakdown
        source_types = [dict(r) for r in conn.execute("""
            SELECT type, COUNT(*) as count FROM sources GROUP BY type
        """).fetchall()]

        # Cache hit rate
        cache_row = conn.execute(
            "SELECT COUNT(*) as total, SUM(cached) as hits FROM search_history").fetchone()
        total, hits = cache_row[0], cache_row[1] or 0
        cache_rate = round((hits / total * 100) if total > 0 else 0, 1)

        # Model usage
        model_usage = [dict(r) for r in conn.execute("""
            SELECT model, COUNT(*) as count FROM search_history GROUP BY model
        """).fetchall()]

        conn.close()
        return {
            "top_queries": top_queries,
            "searches_by_day": searches_by_day,
            "source_types": source_types,
            "cache_hit_rate": cache_rate,
            "model_usage": model_usage,
        }

    # ── Collections ───────────────────────────────────────────────────────────

    def create_collection(self, name: str, description: str = None) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO collections (name, description) VALUES (?,?)", (name, description))
        cid = c.lastrowid
        conn.commit()
        conn.close()
        return cid

    def get_collections(self) -> List[Dict]:
        conn = self.get_connection()
        rows = conn.execute("""
            SELECT c.*, COUNT(sc.source_id) as source_count
            FROM collections c
            LEFT JOIN source_collections sc ON c.id = sc.collection_id
            GROUP BY c.id ORDER BY c.created_at DESC
        """).fetchall()
        result = [dict(r) for r in rows]
        conn.close()
        return result

    def delete_collection(self, collection_id: int):
        conn = self.get_connection()
        conn.execute("DELETE FROM source_collections WHERE collection_id=?", (collection_id,))
        conn.execute("DELETE FROM collections WHERE id=?", (collection_id,))
        conn.commit()
        conn.close()

    def add_source_to_collection(self, source_id: int, collection_id: int):
        conn = self.get_connection()
        try:
            conn.execute("INSERT INTO source_collections (source_id, collection_id) VALUES (?,?)",
                         (source_id, collection_id))
            conn.commit()
        except Exception:
            pass
        conn.close()

    def remove_source_from_collection(self, source_id: int, collection_id: int):
        conn = self.get_connection()
        conn.execute("DELETE FROM source_collections WHERE source_id=? AND collection_id=?",
                     (source_id, collection_id))
        conn.commit()
        conn.close()

    # ── Index jobs ────────────────────────────────────────────────────────────

    def create_job(self, job_id: str, filename: str):
        conn = self.get_connection()
        conn.execute("INSERT INTO index_jobs (id, filename, status) VALUES (?,?,'pending')",
                     (job_id, filename))
        conn.commit()
        conn.close()

    def update_job(self, job_id: str, status: str, chunks: int = 0, error: str = None):
        conn = self.get_connection()
        conn.execute(
            "UPDATE index_jobs SET status=?, chunks=?, error=?, completed_at=? WHERE id=?",
            (status, chunks, error, datetime.now().isoformat() if status != 'pending' else None, job_id))
        conn.commit()
        conn.close()

    def get_job(self, job_id: str) -> Optional[Dict]:
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM index_jobs WHERE id=?", (job_id,)).fetchone()
        result = dict(row) if row else None
        conn.close()
        return result
