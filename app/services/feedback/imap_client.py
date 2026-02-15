from __future__ import annotations

import email
import imaplib
import re
from dataclasses import dataclass
from email.message import Message
from email.utils import parseaddr
from html import unescape
from typing import List, Tuple


@dataclass
class InboxItem:
    msg_id: bytes
    mailbox: str
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
    mailboxes: List[str]

    def fetch_recent_items(self, *, limit: int = 200) -> List[InboxItem]:
        if not all([self.host, self.port, self.username, self.password]):
            raise ValueError("IMAP config is incomplete")

        items: List[InboxItem] = []
        seen_keys: set[str] = set()
        normalized_allowed = {self._normalize_email(sender) for sender in self.allowed_senders if sender.strip()}

        with imaplib.IMAP4_SSL(self.host, self.port) as client:
            client.login(self.username, self.password)

            for mailbox in self._resolve_mailboxes():
                if not self._select_mailbox(client, mailbox):
                    continue

                typ, data = client.search(None, "ALL")
                if typ != "OK" or not data or not data[0]:
                    continue

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
                    fallback_key = f"{mailbox}:imap-{msg_id.decode(errors='ignore')}"
                    message_key = message_id_header or fallback_key

                    if message_key in seen_keys:
                        continue

                    seen_keys.add(message_key)
                    items.append(
                        InboxItem(
                            msg_id=msg_id,
                            mailbox=mailbox,
                            subject=subject,
                            sender=sender,
                            body=body,
                            message_key=message_key,
                        )
                    )

        return items

    def mark_seen(self, marks: List[Tuple[str, bytes]]) -> None:
        if not marks:
            return

        grouped: dict[str, List[bytes]] = {}
        for mailbox, msg_id in marks:
            grouped.setdefault(mailbox, []).append(msg_id)

        with imaplib.IMAP4_SSL(self.host, self.port) as client:
            client.login(self.username, self.password)
            for mailbox, msg_ids in grouped.items():
                if not self._select_mailbox(client, mailbox):
                    continue
                for msg_id in msg_ids:
                    client.store(msg_id, "+FLAGS", "\\Seen")

    def _resolve_mailboxes(self) -> List[str]:
        if self.mailboxes:
            seen: set[str] = set()
            ordered: List[str] = []
            for item in self.mailboxes:
                name = item.strip()
                if not name:
                    continue
                key = name.lower()
                if key in seen:
                    continue
                seen.add(key)
                ordered.append(name)
            if ordered:
                return ordered
        return ["INBOX"]

    def _select_mailbox(self, client: imaplib.IMAP4_SSL, mailbox: str) -> bool:
        typ, _ = client.select(f'"{mailbox}"')
        if typ == "OK":
            return True
        typ, _ = client.select(mailbox)
        return typ == "OK"

    def _extract_text_body(self, msg: Message) -> str:
        if msg.is_multipart():
            # Prefer plain text; if absent use HTML fallback.
            html_candidate = ""
            for part in msg.walk():
                disposition = str(part.get("Content-Disposition", "")).lower()
                if "attachment" in disposition:
                    continue

                content_type = part.get_content_type()
                text = self._decode_part(part)
                if not text:
                    continue
                if content_type == "text/plain":
                    return text
                if content_type == "text/html" and not html_candidate:
                    html_candidate = text

            return self._html_to_text(html_candidate) if html_candidate else ""

        content_type = msg.get_content_type()
        text = self._decode_part(msg)
        if content_type == "text/html":
            return self._html_to_text(text)
        return text

    def _decode_part(self, part: Message) -> str:
        payload = part.get_payload(decode=True)
        if payload is None:
            raw = part.get_payload()
            return raw if isinstance(raw, str) else ""

        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except LookupError:
            return payload.decode("utf-8", errors="replace")

    def _html_to_text(self, value: str) -> str:
        if not value:
            return ""
        text = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", " ", value)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = unescape(text)
        text = text.replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n", text)
        return text.strip()

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
