from __future__ import annotations

import email
import imaplib
from dataclasses import dataclass
from email.message import Message
from email.utils import parseaddr
from typing import List


@dataclass
class InboxItem:
    msg_id: bytes
    subject: str
    sender: str
    body: str


@dataclass
class IMAPFeedbackClient:
    host: str
    port: int
    username: str
    password: str
    subject_prefix: str
    allowed_senders: List[str]

    def fetch_unseen_items(self) -> List[InboxItem]:
        if not all([self.host, self.port, self.username, self.password]):
            raise ValueError("IMAP config is incomplete")

        items: List[InboxItem] = []
        with imaplib.IMAP4_SSL(self.host, self.port) as client:
            client.login(self.username, self.password)
            client.select("INBOX")

            typ, data = client.search(None, "UNSEEN")
            if typ != "OK":
                return []

            for msg_id in data[0].split():
                typ, msg_data = client.fetch(msg_id, "(RFC822)")
                if typ != "OK" or not msg_data:
                    continue

                raw_bytes = msg_data[0][1]
                msg = email.message_from_bytes(raw_bytes)
                subject = self._decode_header_value(msg.get("Subject", ""))
                sender = parseaddr(msg.get("From", ""))[1].lower().strip()

                if self.subject_prefix and self.subject_prefix not in subject:
                    continue
                if self.allowed_senders and sender not in self.allowed_senders:
                    continue

                body = self._extract_text_body(msg)
                items.append(
                    InboxItem(
                        msg_id=msg_id,
                        subject=subject,
                        sender=sender,
                        body=body,
                    )
                )

        return items

    def mark_seen(self, msg_ids: List[bytes]) -> None:
        if not msg_ids:
            return

        with imaplib.IMAP4_SSL(self.host, self.port) as client:
            client.login(self.username, self.password)
            client.select("INBOX")
            for msg_id in msg_ids:
                client.store(msg_id, "+FLAGS", "\\Seen")

    def _extract_text_body(self, msg: Message) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))
                if content_type == "text/plain" and "attachment" not in disposition.lower():
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
            return ""

        payload = msg.get_payload(decode=True)
        if payload is None:
            text = msg.get_payload()
            return text if isinstance(text, str) else ""
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")

    def _decode_header_value(self, value: str) -> str:
        if not value:
            return ""
        decoded = email.header.decode_header(value)
        parts: List[str] = []
        for chunk, encoding in decoded:
            if isinstance(chunk, bytes):
                parts.append(chunk.decode(encoding or "utf-8", errors="replace"))
            else:
                parts.append(chunk)
        return "".join(parts)
