import json
from datetime import datetime, timezone

from src.adapters.email_db import email_db
from src.adapters.logger import logger
from src.model import EmailMessage
from src.react_agent import run_agent


def _status_for(stopped_reason: str) -> str:
    # The agent finished cleanly -> processed. It ran out of turns without a
    # final answer -> flag for human review rather than guessing.
    return "processed" if stopped_reason == "final_answer" else "pending"


def _base_record(email_msg: EmailMessage) -> dict:
    return {
        "uid": email_msg.uid,
        "sender_name": email_msg.sender_name,
        "sender_email": email_msg.sender_email,
        "subject": email_msg.subject,
        "body": email_msg.body,
        "received_at": email_msg.received_at,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


def trigger_agent(email_msg: EmailMessage) -> dict:
    """
    Entry point the mailbox poller calls for every unread email. Runs the
    ReAct agent (classify -> draft a reply if warranted), persists the
    outcome to SQLite for the dashboard to read, and returns it.
    """
    try:
        result = run_agent(email_msg)
    except Exception as ex:
        logger.error(f"Agent run failed for uid={email_msg.uid}: {ex}", exc_info=True)
        email_db.upsert({
            **_base_record(email_msg),
            "classification": None,
            "confidence": None,
            "status": "failed",
            "thought_process": "[]",
            "suggested_reply": "",
            "error": str(ex),
        })
        raise  # let the poller's retry-while-in-window behavior still apply

    email_db.upsert({
        **_base_record(email_msg),
        "classification": result["classification"],
        "confidence": result["confidence"],
        "status": _status_for(result["stopped_reason"]),
        "thought_process": json.dumps(result["thought_process"]),
        "suggested_reply": result["suggested_reply"],
        "error": None,
    })

    logger.info(
        f"STATUS: Agent finished for uid={email_msg.uid} from={email_msg.sender_email} "
        f"classification={result['classification']} confidence={result['confidence']} "
        f"turns={result['turns']} stopped_reason={result['stopped_reason']}"
    )
    logger.info(f"Suggested reply for uid={email_msg.uid}:\n{result['suggested_reply']}")
    return result
