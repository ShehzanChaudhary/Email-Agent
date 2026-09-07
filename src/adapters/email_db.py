import os 
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'data', 'email_agent.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS processed_emails (
    uid             TEXT PRIMARY KEY,
    sender_name     TEXT,
    sender_email    TEXT,
    subject         TEXT,
    body            TEXT,
    received_at     TEXT NOT NULL,
    classification  TEXT,
    confidence      REAL,
    status          TEXT NOT NULL,
    thought_process TEXT,
    suggested_reply TEXT,
    reply_sent      INTEGER NOT NULL DEFAULT 0,
    error           TEXT,
    processed_at    TEXT NOT NULL
);
"""

# reply_sent is deliberately left out of the upsert's UPDATE clause -- a
# re-processed email (e.g. a retried failure) should never stomp on a
# reply-sent flag a future "send" feature has already set.
UPSERT = """
INSERT INTO processed_emails (
    uid, sender_name, sender_email, subject, body, received_at,
    classification, confidence, status, thought_process,
    suggested_reply, reply_sent, error, processed_at
) VALUES (
    :uid, :sender_name, :sender_email, :subject, :body, :received_at,
    :classification, :confidence, :status, :thought_process,
    :suggested_reply, 0, :error, :processed_at
)
ON CONFLICT(uid) DO UPDATE SET
    sender_name     = excluded.sender_name,
    sender_email    = excluded.sender_email,
    subject         = excluded.subject,
    body            = excluded.body,
    received_at     = excluded.received_at,
    classification  = excluded.classification,
    confidence      = excluded.confidence,
    status          = excluded.status,
    thought_process = excluded.thought_process,
    suggested_reply = excluded.suggested_reply,
    error           = excluded.error,
    processed_at    = excluded.processed_at
"""

class EmailDB:
    """Stores every agent run against a mailbox message, keyed by IMAP uid, for the dashboard to read."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def upsert(self, record: dict) -> None:
        """Inserts a new row, or updates the existing one for that uid (agent results, not reply_sent)."""
        conn = self._connect()
        try:
            conn.execute(UPSERT, record)
            conn.commit()
        finally:
            conn.close()

    def list_emails(self, limit: int = 200) -> list[dict]:
        """Most recently received emails first."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM processed_emails ORDER BY received_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()


email_db = EmailDB()