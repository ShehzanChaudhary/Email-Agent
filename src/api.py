"""
Backend for the Email Agent dashboard. Starts the mailbox poller in a
background thread on startup (poll -> classify -> draft reply -> persist to
SQLite), and serves that SQLite data straight to the frontend, which pulls
it on load and whenever the user hits refresh.

Run with:
    python api.py
or:
    uvicorn api:app --reload
"""
from __future__ import annotations

import json
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.email_db import email_db
from src.adapters.email_reader import email_reader
from src.adapters.logger import logger
from src.agent_trigger import trigger_agent
from config.config import Config

_stop_polling = threading.Event()


def _poll_loop() -> None:
    logger.info(
        f"STATUS: Poller started -- watching {Config.EMAIL_ADDRESS or '<unset>'} "
        f"every {Config.POLL_INTERVAL_SECONDS}s"
    )
    while not _stop_polling.is_set():
        try:
            count = email_reader.poll_once(trigger_agent)
            if count:
                logger.info(f"STATUS: Processed {count} new email(s)")
        except Exception as ex:
            logger.error(f"Poll cycle failed: {ex}", exc_info=True)
        _stop_polling.wait(Config.POLL_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    threading.Thread(target=_poll_loop, daemon=True).start()
    yield
    _stop_polling.set()


app = FastAPI(title="Email Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dashboard is local-only for now
    allow_methods=["*"],
    allow_headers=["*"],
)


def _row_to_email_record(row: dict) -> dict:
    return {
        "id": row["uid"],
        "sender": row["sender_name"] or row["sender_email"],
        "senderEmail": row["sender_email"],
        "subject": row["subject"],
        "snippet": (row["body"] or "")[:160],
        "body": row["body"],
        "receivedAt": row["received_at"],
        "classification": row["classification"] or "",
        "confidence": row["confidence"] or 0,
        "status": row["status"],
        "thoughtProcess": json.loads(row["thought_process"] or "[]"),
        "suggestedReply": row["suggested_reply"] or "",
        "replySent": bool(row["reply_sent"]),
    }


@app.get("/api/emails")
def list_emails(limit: int = 200) -> list[dict]:
    rows = email_db.list_emails(limit=limit)
    return [_row_to_email_record(row) for row in rows]


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
