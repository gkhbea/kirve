"""
KİRVE AI OS - PostgreSQL + pgvector Memory Module
Stores user conversations and documents with vector embeddings.
Includes cosine similarity vector search and resilient local fallback.
"""
import os
import json
import datetime
from typing import List, Dict, Any, Optional
from kirve.embedding import EmbeddingEngine, EMBEDDING_DIM
from kirve.config import DEFAULT_DB_PATH

# PostgreSQL and pgvector driver
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    from pgvector.psycopg2 import register_vector
    PG_AVAILABLE = True
except ImportError:
    PG_AVAILABLE = False

# Database URL (Default localhost or env)
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = int(os.getenv("PGPORT", "5432"))
PG_DB = os.getenv("PGDATABASE", "kirve_db")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASSWORD = os.getenv("PGPASSWORD", "postgres")

class VectorMemory:
    """
    Hybrid Vector Memory for KİRVE:
    - Primary: PostgreSQL with pgvector extension (<=> cosine distance).
    - Resilient Fallback: Local vector store when PostgreSQL is offline.
    """
    def __init__(self, dsn: Optional[str] = None, embedding_engine: Optional[EmbeddingEngine] = None, fallback_sqlite_path: Optional[str] = None):
        self.dsn = dsn or os.getenv("DATABASE_URL", f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")
        self.embedder = embedding_engine or EmbeddingEngine()
        self.fallback_db_path = fallback_sqlite_path or str(DEFAULT_DB_PATH)
        self.is_pg_active = False
        
        # Test and initialize PostgreSQL + pgvector
        self._init_pg_storage()
        
        # Always prepare fallback tables in SQLite
        self._init_fallback_storage()

    def _get_pg_connection(self):
        if not PG_AVAILABLE:
            raise ConnectionError("psycopg2 veya pgvector kütüphanesi eksik.")
        conn = psycopg2.connect(self.dsn, connect_timeout=2)
        register_vector(conn)
        return conn

    def _init_pg_storage(self) -> None:
        """Initializes pgvector extension and schemas in PostgreSQL."""
        if not PG_AVAILABLE:
            self.is_pg_active = False
            return

        try:
            with self._get_pg_connection() as conn:
                with conn.cursor() as cur:
                    # Enable pgvector extension
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    
                    # Conversations vector table
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS vector_conversations (
                            id SERIAL PRIMARY KEY,
                            session_id VARCHAR(64) NOT NULL,
                            role VARCHAR(32) NOT NULL,
                            content TEXT NOT NULL,
                            embedding vector({EMBEDDING_DIM}),
                            metadata JSONB,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                    """)
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_session ON vector_conversations (session_id);")

                    # Documents vector table (RAG documents & notes)
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS vector_documents (
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(255) NOT NULL,
                            content TEXT NOT NULL,
                            embedding vector({EMBEDDING_DIM}),
                            tags TEXT[],
                            metadata JSONB,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                    """)
                conn.commit()
            self.is_pg_active = True
        except Exception:
            self.is_pg_active = False

    def _init_fallback_storage(self) -> None:
        """Initializes fallback vector tables in SQLite."""
        import sqlite3
        with sqlite3.connect(self.fallback_db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vector_conversations_fallback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vector_documents_fallback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    tags TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    # --- SOHBET VE VEKTÖR KAYDI ---

    def add_message(self, role: str, content: str, session_id: str = "default", metadata: Optional[Dict[str, Any]] = None) -> int:
        """Embeds and saves a message into vector memory."""
        embedding = self.embedder.embed_text(content)
        meta = metadata or {}

        if self.is_pg_active:
            try:
                with self._get_pg_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO vector_conversations (session_id, role, content, embedding, metadata)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id;
                        """, (session_id, role, content, embedding, Json(meta)))
                        msg_id = cur.fetchone()[0]
                        conn.commit()
                        return msg_id
            except Exception:
                self.is_pg_active = False  # Switch to fallback

        # Fallback local insert
        import sqlite3
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with sqlite3.connect(self.fallback_db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO vector_conversations_fallback (session_id, role, content, embedding, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, role, content, json.dumps(embedding), json.dumps(meta, ensure_ascii=False), now))
            conn.commit()
            return cur.lastrowid

    # --- BELGE (DOCUMENT) VEKTÖR KAYDI ---

    def add_document(self, title: str, content: str, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> int:
        """Embeds and indexes a document for semantic retrieval."""
        embedding = self.embedder.embed_text(f"{title} {content}")
        tag_list = tags or []
        meta = metadata or {}

        if self.is_pg_active:
            try:
                with self._get_pg_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO vector_documents (title, content, embedding, tags, metadata)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id;
                        """, (title, content, embedding, tag_list, Json(meta)))
                        doc_id = cur.fetchone()[0]
                        conn.commit()
                        return doc_id
            except Exception:
                self.is_pg_active = False

        # Fallback local insert
        import sqlite3
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with sqlite3.connect(self.fallback_db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO vector_documents_fallback (title, content, embedding, tags, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, content, json.dumps(embedding), json.dumps(tag_list, ensure_ascii=False), json.dumps(meta, ensure_ascii=False), now))
            conn.commit()
            return cur.lastrowid

    # --- SEMANTİK VEKTÖR ARAMASI (Similarity Search) ---

    def search_similar_messages(self, query: str, limit: int = 5, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Cosine distance vector similarity search over conversation history.
        """
        query_embedding = self.embedder.embed_text(query)

        if self.is_pg_active:
            try:
                with self._get_pg_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        if session_id:
                            cur.execute("""
                                SELECT id, session_id, role, content, metadata,
                                       1 - (embedding <=> %s) AS similarity
                                FROM vector_conversations
                                WHERE session_id = %s
                                ORDER BY embedding <=> %s
                                LIMIT %s;
                            """, (query_embedding, session_id, query_embedding, limit))
                        else:
                            cur.execute("""
                                SELECT id, session_id, role, content, metadata,
                                       1 - (embedding <=> %s) AS similarity
                                FROM vector_conversations
                                ORDER BY embedding <=> %s
                                LIMIT %s;
                            """, (query_embedding, query_embedding, limit))
                        return [dict(row) for row in cur.fetchall()]
            except Exception:
                self.is_pg_active = False

        # Fallback cosine calculation
        import sqlite3
        results = []
        with sqlite3.connect(self.fallback_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if session_id:
                cur.execute("SELECT * FROM vector_conversations_fallback WHERE session_id = ?", (session_id,))
            else:
                cur.execute("SELECT * FROM vector_conversations_fallback")
            rows = cur.fetchall()

        for row in rows:
            vec = json.loads(row["embedding"])
            sim = self.embedder.cosine_similarity(query_embedding, vec)
            results.append({
                "id": row["id"],
                "session_id": row["session_id"],
                "role": row["role"],
                "content": row["content"],
                "similarity": round(sim, 4),
                "created_at": row["created_at"]
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Cosine distance vector similarity search over indexed documents.
        """
        query_embedding = self.embedder.embed_text(query)

        if self.is_pg_active:
            try:
                with self._get_pg_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute("""
                            SELECT id, title, content, tags, metadata,
                                   1 - (embedding <=> %s) AS similarity
                            FROM vector_documents
                            ORDER BY embedding <=> %s
                            LIMIT %s;
                        """, (query_embedding, query_embedding, limit))
                        return [dict(row) for row in cur.fetchall()]
            except Exception:
                self.is_pg_active = False

        # Fallback cosine search
        import sqlite3
        results = []
        with sqlite3.connect(self.fallback_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM vector_documents_fallback")
            rows = cur.fetchall()

        for row in rows:
            vec = json.loads(row["embedding"])
            sim = self.embedder.cosine_similarity(query_embedding, vec)
            tags = json.loads(row["tags"]) if row["tags"] else []
            results.append({
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "tags": tags,
                "similarity": round(sim, 4),
                "created_at": row["created_at"]
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
