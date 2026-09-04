"""
Polls the configured mailbox for unread mail and triggers the agent on each
new message.

Usage:
    python main.py            # poll forever, every POLL_INTERVAL_SECONDS
    python main.py --once     # single pass, then exit (useful for testing)
"""
import sys
import time

from config.config import Config
from src.adapters.logger import logger
from src.adapters.email_reader import email_reader
from src.agent_trigger import trigger_agent


def poll_forever() -> None:
    logger.info(f"STATUS: Watching {Config.EMAIL_ADDRESS or '<unset>'} ({Config.IMAP_FOLDER}) every {Config.POLL_INTERVAL_SECONDS}s")
    while True:
        try:
            count = email_reader.poll_once(trigger_agent)
            if count:
                logger.info(f"STATUS: Processed {count} new email(s)")
        except Exception as ex:
            logger.error(f"Poll cycle failed: {ex}", exc_info=True)
        time.sleep(Config.POLL_INTERVAL_SECONDS)


def main() -> None:
    if "--once" in sys.argv:
        count = email_reader.poll_once(trigger_agent)
        logger.info(f"STATUS: Processed {count} new email(s)")
        return

    try:
        poll_forever()
    except KeyboardInterrupt:
        logger.info("STATUS: Stopped by user")


if __name__ == "__main__":
    main()
