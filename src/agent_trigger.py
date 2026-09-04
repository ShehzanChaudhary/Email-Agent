from src.adapters.logger import logger
from src.model import EmailMessage


def trigger_agent(email_msg: EmailMessage) -> None:
    """
    Entry point the mailbox poller calls for every unread email.

    Placeholder until the ReAct agent (intent detection + reply/action) is
    built -- for now it just confirms the message was read successfully.
    """
    logger.info(
        f"STATUS: Agent triggered for uid={email_msg.uid} from={email_msg.sender} "
        f"subject={email_msg.subject!r} body_len={len(email_msg.body)}"
    )
