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
    message_key: str


@dataclass
class IMAPFeedbackClient:
    host: str
    port: int
    username: str
    password: str
    subject_prefix: str
    allowed_senders: List[str]

    def fetch_recent_items(self, *, limit: int = 200) -> List[InboxItem]:
        if not all([self.host, self.port, self.username, self.password]):
            raise ValueError("IMAP config is incomplete")

        items: List[InboxItem] = []
        normalized_allowed = {self._normalize_email(sender) for sender in self.allowed_senders if sender.strip()}

        with imaplib.IMAP4_SSL(self.host, self.port) as client:
            client.login(self.username, self.password)
            client.select("INBOX")

            typ, data = client.search(None, "ALL")
            if typ != "OK" or not data or not data[0]:
                return []

            msg_ids = data[0].split()
            msg_ids = msg_ids[-limit:]

            for msg_id in msg_ids:
                typ, msg_data = client.fetch(msg_id, "(RFC822)")
                if typ != "OK" or not msg_data:
                    continue

                raw_bytes = msg_data[0][1]
                msg = email.message_from_bytes(raw_bytes)
                subject = self._decode_header_value(msg.get("Subject", ""))
                sender = parseaddr(msg.get("From", ""))[1].lower().strip()
                sender_norm = self._normalize_email(sender)

                if self.subject_prefix and self.subject_prefix not in subject:
                    continue
                if normalized_allowed and sender_norm not in normalized_allowed:
                    continue

                body = self._extract_text_body(msg)
                message_id_header = str(msg.get("Message-ID", "")).strip()
                message_key = message_id_header or f"imap-{msg_id.decode(errors='ignore')}"

                items.append(
                    InboxItem(
                        msg_id=msg_id,
                        subject=subject,
                        sender=sender,
                        body=body,
                        message_key=message_key,
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

    def _normalize_email(self, email_value: str) -> str:
        email_value = email_value.strip().lower()
        if "@" not in email_value:
            return email_value
        local, domain = email_value.split("@", 1)
        if domain in {"gmail.com", "googlemail.com"}:
            local = local.split("+", 1)[0].replace(".", "")
        return f"{local}@{domain}"
