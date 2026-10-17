"""
KİRVE AI OS - SQLite Memory Module
"""
import sqlite3
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from kirve.config import DEFAULT_DB_PATH

class KirveMemory:
    """
    SQLite-backed memory store for KİRVE AI OS.
    Manages conversation history, patron preferences, and session context.
    """
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        if db_path is None:
            self.db_path = str(DEFAULT_DB_PATH)
        else:
            self.db_path = str(db_path)
            
        self._shared_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:")
            self._shared_conn.row_factory = sqlite3.Row
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes tables with proper schemas and indexes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_time ON conversations (session_id, timestamp)")
            
            # Patron preferences table (Key-Value preference store)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # System activity logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_message(self, role: str, content: str, session_id: str = "default", metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Saves a chat message into memory.
        Roles: 'user', 'assistant', 'system'
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (session_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, role, content, now, meta_str))
            conn.commit()
            return cursor.lastrowid

    def get_history(self, session_id: str = "default", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches the most recent conversation history for a given session.
        Returned in chronological order (oldest to newest within the limit window).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_id, role, content, timestamp, metadata
                FROM conversations
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (session_id, limit))
            rows = cursor.fetchall()
            
        history = []
        for row in reversed(rows):
            meta = {}
            if row["metadata"]:
                try:
                    meta = json.loads(row["metadata"])
                except Exception:
                    meta = {}
            history.append({
                "id": row["id"],
                "session_id": row["session_id"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"],
                "metadata": meta
            })
        return history

    def set_preference(self, key: str, value: Any) -> None:
        """
        Saves or updates a patron preference.
        """
        val_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO preferences (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """, (key, val_str, now))
            conn.commit()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a patron preference.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row:
                return default
            val = row["value"]
            try:
                return json.loads(val)
            except Exception:
                return val

    def clear_history(self, session_id: Optional[str] = None) -> int:
        """
        Clears conversation history. If session_id is provided, only clears that session.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if session_id:
                cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            else:
                cursor.execute("DELETE FROM conversations")
            conn.commit()
            return cursor.rowcount

    def log_event(self, level: str, message: str) -> None:
        """Logs internal system events."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO system_logs (level, message, timestamp) VALUES (?, ?, ?)", (level, message, now))
            conn.commit()

    def close(self) -> None:
        """Closes any persistent shared connection."""
        if self._shared_conn is not None:
            self._shared_conn.close()
            self._shared_conn = None

