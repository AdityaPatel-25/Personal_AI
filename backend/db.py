"""Database & Chat History Persistence Module using SQLite.

Manages persistent storage for:
- conversations (id, title, created_at)
- messages (id, conversation_id, role, content, created_at)
"""

import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Resolve default DB path relative to the backend directory
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "personal_ai.db")
DB_PATH = os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH)


def get_db_connection() -> sqlite3.Connection:
    """Creates and returns a SQLite connection with row access and foreign keys enabled."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        logger.error("Failed to connect to SQLite database at '%s': %s", DB_PATH, e, exc_info=True)
        raise


def init_db() -> None:
    """Initializes the database schema if tables do not already exist."""
    try:
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

                CREATE TABLE IF NOT EXISTS submissions (
                    id TEXT PRIMARY KEY,
                    problem TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_submissions_created_at 
                ON submissions(created_at);
                """
            )
    except sqlite3.Error as e:
        logger.error("Failed to initialize SQLite database schema: %s", e, exc_info=True)
        raise


def _current_timestamp() -> str:
    """Returns ISO 8601 formatted UTC timestamp with timezone offset."""
    return datetime.now(timezone.utc).isoformat()


def create_conversation(title: str = "New Chat", conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new conversation record and returns it."""
    init_db()
    conv_id = conversation_id or str(uuid.uuid4())
    clean_title = (title or "New Chat").strip()
    created_at = _current_timestamp()

    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)",
                (conv_id, clean_title, created_at),
            )
            conn.commit()

        logger.info("Created conversation %s: '%s'", conv_id, clean_title)
        return {
            "id": conv_id,
            "title": clean_title,
            "created_at": created_at,
        }
    except sqlite3.Error as e:
        logger.error("Failed to create conversation %s in SQLite: %s", conv_id, e, exc_info=True)
        raise


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single conversation by its ID."""
    init_db()
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT id, title, created_at FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)
    except sqlite3.Error as e:
        logger.error("Failed to query conversation %s from SQLite: %s", conversation_id, e, exc_info=True)
        raise


def list_conversations() -> List[Dict[str, Any]]:
    """Returns all conversations ordered by creation date descending (newest first)."""
    init_db()
    try:
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
    except sqlite3.Error as e:
        logger.error("Failed to list conversations from SQLite: %s", e, exc_info=True)
        raise


def update_conversation_title(conversation_id: str, title: str) -> bool:
    """Updates the title of an existing conversation."""
    init_db()
    clean_title = (title or "New Chat").strip()
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "UPDATE conversations SET title = ? WHERE id = ?",
                (clean_title, conversation_id),
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error("Failed to update title for conversation %s: %s", conversation_id, e, exc_info=True)
        raise


def delete_conversation(conversation_id: str) -> bool:
    """Deletes a conversation and all its cascaded messages."""
    init_db()
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("Deleted conversation %s and associated messages", conversation_id)
            return deleted
    except sqlite3.Error as e:
        logger.error("Failed to delete conversation %s from SQLite: %s", conversation_id, e, exc_info=True)
        raise


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

    msg_id = message_id or str(uuid.uuid4())
    created_at = _current_timestamp()

    try:
        # Ensure conversation exists
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
            if not cursor.fetchone():
                title = content[:40].strip() + ("..." if len(content) > 40 else "") if role == "user" else "New Chat"
                conn.execute(
                    "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)",
                    (conversation_id, title or "New Chat", created_at),
                )

            conn.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (msg_id, conversation_id, role, content, created_at),
            )
            conn.commit()

        logger.debug("Saved message %s (role=%s) for conversation %s", msg_id, role, conversation_id)
        return {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": created_at,
        }
    except sqlite3.Error as e:
        logger.error("Failed to insert message into SQLite for conversation %s: %s", conversation_id, e, exc_info=True)
        raise


def get_messages(conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves messages for a conversation in chronological order.
    
    If limit is provided, retrieves the *latest* N messages ordered chronologically (oldest to newest).
    """
    init_db()
    try:
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
    except sqlite3.Error as e:
        logger.error("Failed to retrieve messages for conversation %s: %s", conversation_id, e, exc_info=True)
        raise


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


# ============================================================================
# Submissions Management
# ============================================================================


def add_submission(
    problem: str,
    topic: str,
    verdict: str,
    submission_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Inserts a new problem submission record into the submissions table."""
    init_db()
    clean_problem = problem.strip()
    clean_topic = topic.strip()
    clean_verdict = verdict.strip()
    if not clean_problem:
        raise ValueError("Problem cannot be empty.")

    sub_id = submission_id or str(uuid.uuid4())
    created_at = _current_timestamp()

    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO submissions (id, problem, topic, verdict, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sub_id, clean_problem, clean_topic, clean_verdict, created_at),
            )
            conn.commit()

        logger.info("Saved submission %s: Problem='%s', Verdict='%s'", sub_id, clean_problem, clean_verdict)
        return {
            "id": sub_id,
            "problem": clean_problem,
            "topic": clean_topic,
            "verdict": clean_verdict,
            "created_at": created_at,
        }
    except sqlite3.Error as e:
        logger.error("Failed to add submission to SQLite: %s", e, exc_info=True)
        raise


def list_submissions(limit: Optional[int] = 50) -> List[Dict[str, Any]]:
    """Retrieves recent problem submissions ordered newest first."""
    init_db()
    try:
        with get_db_connection() as conn:
            query = "SELECT id, problem, topic, verdict, created_at FROM submissions ORDER BY created_at DESC"
            if limit and limit > 0:
                query += f" LIMIT {int(limit)}"
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error("Failed to list submissions from SQLite: %s", e, exc_info=True)
        raise


def get_all_messages_content() -> List[str]:
    """Retrieves all message contents from the database for weakness and topic analysis."""
    init_db()
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT content FROM messages ORDER BY created_at DESC")
            return [row["content"] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error("Failed to retrieve message contents from SQLite: %s", e, exc_info=True)
        raise


# Initialize database automatically on module import
try:
    init_db()
except Exception as e:
    logger.error("Database initialization on import failed: %s", e)

