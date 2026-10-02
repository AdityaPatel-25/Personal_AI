"""Database & Chat History Persistence Module using SQLite.

Manages persistent storage for:
- conversations (id, title, created_at)
- messages (id, conversation_id, role, content, created_at)
"""

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Resolve default DB path relative to the backend directory
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "personal_ai.db")
DB_PATH = os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH)


def get_db_connection() -> sqlite3.Connection:
    """Creates and returns a SQLite connection with row access and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Initializes the database schema if tables do not already exist."""
    with get_db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
            ON messages(conversation_id, created_at);
            """
        )


def _current_timestamp() -> str:
    """Returns ISO 8601 formatted UTC timestamp with timezone offset."""
    return datetime.now(timezone.utc).isoformat()


def create_conversation(title: str = "New Chat", conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new conversation record and returns it."""
    init_db()
    conv_id = conversation_id or str(uuid.uuid4())
    clean_title = (title or "New Chat").strip()
    created_at = _current_timestamp()

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)",
            (conv_id, clean_title, created_at),
        )
        conn.commit()

    return {
        "id": conv_id,
        "title": clean_title,
        "created_at": created_at,
    }


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single conversation by its ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT id, title, created_at FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)


def list_conversations() -> List[Dict[str, Any]]:
    """Returns all conversations ordered by creation date descending (newest first)."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT c.id, c.title, c.created_at,
                   COUNT(m.id) AS message_count,
                   MAX(m.created_at) AS last_message_at
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
            ORDER BY COALESCE(MAX(m.created_at), c.created_at) DESC
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_conversation_title(conversation_id: str, title: str) -> bool:
    """Updates the title of an existing conversation."""
    init_db()
    clean_title = (title or "New Chat").strip()
    with get_db_connection() as conn:
        cursor = conn.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (clean_title, conversation_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_conversation(conversation_id: str) -> bool:
    """Deletes a conversation and all its cascaded messages."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def add_message(
    conversation_id: str,
    role: str,
    content: str,
    message_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Adds a message to the specified conversation, auto-creating conversation if needed."""
    init_db()
    if role not in ("user", "assistant"):
        raise ValueError(f"Invalid message role '{role}'. Must be 'user' or 'assistant'.")

    # Ensure conversation exists
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not cursor.fetchone():
            # Derive initial title from content if user message
            title = content[:40].strip() + ("..." if len(content) > 40 else "") if role == "user" else "New Chat"
            conn.execute(
                "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)",
                (conversation_id, title or "New Chat", _current_timestamp()),
            )

        msg_id = message_id or str(uuid.uuid4())
        created_at = _current_timestamp()

        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (msg_id, conversation_id, role, content, created_at),
        )
        conn.commit()

    return {
        "id": msg_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "created_at": created_at,
    }


def get_messages(conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves messages for a conversation in chronological order.
    
    If limit is provided, retrieves the *latest* N messages ordered chronologically (oldest to newest).
    """
    init_db()
    with get_db_connection() as conn:
        if limit and limit > 0:
            cursor = conn.execute(
                """
                SELECT id, conversation_id, role, content, created_at
                FROM (
                    SELECT id, conversation_id, role, content, created_at
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
                ORDER BY created_at ASC
                """,
                (conversation_id, limit),
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, conversation_id, role, content, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
                """,
                (conversation_id,),
            )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_conversation_with_messages(
    conversation_id: str,
    limit: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves conversation metadata along with its messages."""
    conv = get_conversation(conversation_id)
    if not conv:
        return None
    conv["messages"] = get_messages(conversation_id, limit=limit)
    return conv


# Initialize database automatically on module import
init_db()
