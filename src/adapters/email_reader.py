from __future__ import annotations

import email
import imaplib
import re
import time
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parseaddr
from typing import Callable

from config.config import Config
from src.adapters.logger import logger
from src.model import EmailMessage


def _decode(value: str | None) -> str:
    """Decodes a possibly RFC 2047 encoded header (e.g. '=?UTF-8?B?...?=') into plain text."""
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded += text.decode(charset or "utf-8", errors="replace")
        else:
            decoded += text
    return decoded


class IMAPEmailReader:
    """
    Reads recently-arrived mail over IMAP (Gmail by default) and hands each
    message to a handler function -- the eventual entry point into the agent.

    "Recent" means received within the last Config.LOOKBACK_MINUTES minutes,
    regardless of read/unread status -- read state is never touched, and old
    backlog mail is ignored entirely. Since polling happens more often than
    the lookback window, an in-memory set of already-handled UIDs stops the
    same email being handled twice; entries fall out of that set on their
    own once the message ages out of the window.
    """

    def __init__(self):
        self._host = Config.IMAP_HOST
        self._port = Config.IMAP_PORT
        self._address = Config.EMAIL_ADDRESS
        self._password = Config.EMAIL_PASSWORD
        self._folder = Config.IMAP_FOLDER
        self._lookback_seconds = Config.POLL_INTERVAL_SECONDS * 60
        self._processed_uids: set[str] = set()

    def _connect(self) -> imaplib.IMAP4_SSL:
        if not self._address or not self._password:
            raise RuntimeError(
                "EMAIL_ADDRESS / EMAIL_PASSWORD are not set. For Gmail, EMAIL_PASSWORD "
                "must be a 16-character App Password, not your normal login password."
            )
        conn = imaplib.IMAP4_SSL(self._host, self._port)
        conn.login(self._address, self._password)
        conn.select(self._folder)
        return conn

    @staticmethod
    def _extract_body(msg: email.message.Message) -> str:
        """Prefers the plain-text part; falls back to a stripped-down version of HTML."""
        if msg.is_multipart():
            html_fallback = ""
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition") or "")
                if "attachment" in disposition:
                    continue
                if content_type == "text/plain":
                    return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace").strip()
                if content_type == "text/html" and not html_fallback:
                    html_fallback = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
            return re.sub(r"<[^>]+>", " ", html_fallback).strip()

        payload = msg.get_payload(decode=True)
        if payload is None:
            return ""
        text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
        if msg.get_content_type() == "text/html":
            text = re.sub(r"<[^>]+>", " ", text)
        return text.strip()

    @staticmethod
    def _extract_attachments(msg: email.message.Message) -> list[str]:
        names = []
        if msg.is_multipart():
            for part in msg.walk():
                if "attachment" in str(part.get("Content-Disposition") or ""):
                    filename = part.get_filename()
                    if filename:
                        names.append(_decode(filename))
        return names

    def _parse_message(self, uid: str, raw: bytes, received_at: str) -> EmailMessage:
        msg = email.message_from_bytes(raw)
        sender_name, sender_email = parseaddr(_decode(msg.get("From")))
        return EmailMessage(
            uid=uid,
            sender_name=sender_name,
            sender_email=sender_email,
            subject=_decode(msg.get("Subject")),
            body=self._extract_body(msg),
            received_at=received_at,
            attachments=self._extract_attachments(msg),
        )

    def poll_once(self, handler: Callable[[EmailMessage], None]) -> int:
        """
        Connects, fetches every message received within the lookback window
        that hasn't already been handled, and calls `handler` on each one.
        Returns how many messages were handled this call.
        """
        conn = self._connect()
        processed = 0
        try:
            cutoff_epoch = time.time() - self._lookback_seconds
            # SINCE only has day-granularity, so this just bounds the candidate
            # set to ~today's mail -- the real filtering happens below by
            # comparing each message's actual INTERNALDATE to cutoff_epoch.
            since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            status, data = conn.search(None, f'(SINCE "{since_date}")')
            if status != "OK":
                logger.error(f"IMAP search failed: {status}")
                return 0

            uids = data[0].split()
            current_uids = {uid.decode() for uid in uids}

            for uid_str in current_uids:
                if uid_str in self._processed_uids:
                    continue

                # BODY.PEEK[] fetches the message without the server marking it \Seen.
                status, msg_data = conn.fetch(uid_str, "(INTERNALDATE BODY.PEEK[])")
                if status != "OK" or not msg_data or msg_data[0] is None:
                    logger.error(f"IMAP fetch failed for uid {uid_str}: {status}")
                    continue

                meta, raw = msg_data[0]
                received_epoch = time.mktime(imaplib.Internaldate2tuple(meta))
                if received_epoch < cutoff_epoch:
                    continue  # older than the lookback window -- ignore

                received_at = datetime.fromtimestamp(received_epoch).astimezone().isoformat()
                email_msg = self._parse_message(uid_str, raw, received_at)
                logger.info(f"Read email uid={uid_str} from={email_msg.sender_email} subject={email_msg.subject!r}")

                try:
                    handler(email_msg)
                except Exception as ex:
                    logger.error(f"Handler failed for uid {uid_str}, will retry next poll: {ex}", exc_info=True)
                    continue

                self._processed_uids.add(uid_str)
                processed += 1

            # Drop tracking for anything that's fallen out of the candidate
            # window -- it can never be re-fetched as "recent" again.
            self._processed_uids &= current_uids
        finally:
            try:
                conn.close()
            finally:
                conn.logout()

        return processed


email_reader = IMAPEmailReader()
