import sqlite3
from datetime import datetime
from typing import List, Dict

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
        cursor = conn.cursor()
        
        cursor.execute("""
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
        
        cursor.execute("""
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                results_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_source(self, source_type: str, path: str = None, name: str = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sources (type, path, name, status)
            VALUES (?, ?, ?, 'indexing')
        """, (source_type, path, name))
        source_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return source_id
    
    def update_source_status(self, source_id: int, status: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sources 
            SET status = ?, indexed_at = ?
            WHERE id = ?
        """, (status, datetime.now().isoformat(), source_id))
        conn.commit()
        conn.close()
    
    def add_document(self, doc_id: str, source_id: int, title: str, url: str = None, content_preview: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO documents (id, source_id, title, url, content_preview)
            VALUES (?, ?, ?, ?, ?)
        """, (doc_id, source_id, title, url, content_preview))
        conn.commit()
        conn.close()
    
    def get_sources(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, COUNT(d.id) as doc_count
            FROM sources s
            LEFT JOIN documents d ON s.id = d.source_id
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """)
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sources
    
    def delete_source(self, source_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE source_id = ?", (source_id,))
        cursor.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        conn.commit()
        conn.close()
    
    def add_search(self, query: str, results_count: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO search_history (query, results_count)
            VALUES (?, ?)
        """, (query, results_count))
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM sources WHERE status = 'indexed'")
        sources_count = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM documents")
        docs_count = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM search_history")
        searches_count = cursor.fetchone()['total']
        conn.close()
        return {
            "sources": sources_count,
            "documents": docs_count,
            "searches": searches_count
        }