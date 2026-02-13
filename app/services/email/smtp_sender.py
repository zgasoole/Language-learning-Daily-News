from __future__ import annotations

import mimetypes
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Optional


@dataclass
class SMTPSender:
    host: str
    port: int
    username: str
    password: str
    sender: str

    def send_html(
        self,
        *,
        to_address: str,
        subject: str,
        html_body: str,
        audio_attachment: Optional[Path] = None,
    ) -> None:
        if not all([self.host, self.port, self.username, self.password, self.sender, to_address]):
            raise ValueError("SMTP config is incomplete")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = to_address
        msg.set_content("HTML email is required to view this content.")
        msg.add_alternative(html_body, subtype="html")

        if audio_attachment and audio_attachment.exists():
            ctype, _ = mimetypes.guess_type(str(audio_attachment))
            maintype, subtype = (ctype or "audio/mpeg").split("/", 1)
            with audio_attachment.open("rb") as fh:
                msg.add_attachment(
                    fh.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=audio_attachment.name,
                )

        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(self.username, self.password)
            smtp.send_message(msg)
