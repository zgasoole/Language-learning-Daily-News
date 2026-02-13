from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.services.feedback.imap_client import IMAPFeedbackClient
from app.services.feedback.parser import parse_feedback_body
from app.services.state.repository import StateRepository


@dataclass
class FeedbackJob:
    settings: Settings

    def run(self) -> int:
        if not all([self.settings.imap_host, self.settings.imap_user, self.settings.imap_password]):
            print("Feedback ingest skipped: IMAP config missing")
            return 0

        client = IMAPFeedbackClient(
            host=self.settings.imap_host,
            port=self.settings.imap_port,
            username=self.settings.imap_user,
            password=self.settings.imap_password,
            subject_prefix=self.settings.feedback_subject_prefix,
            allowed_senders=self.settings.feedback_allowed_senders,
        )
        state_repo = StateRepository(data_dir=self.settings.data_dir)

        items = client.fetch_unseen_items()
        processed_ids: list[bytes] = []
        applied = 0

        for item in items:
            command = parse_feedback_body(item.body, token=self.settings.feedback_token)
            if command is None:
                processed_ids.append(item.msg_id)
                continue

            if command.command_type == "word":
                state_repo.upsert_word_status(command.word, command.word_status)
                state_repo.record_feedback_event(
                    {
                        "type": "word",
                        "lesson_id": command.lesson_id,
                        "language": command.language,
                        "word": command.word,
                        "status": command.word_status,
                        "sender": item.sender,
                    }
                )
                applied += 1

            elif command.command_type == "grammar":
                state_repo.set_grammar_mastered(command.topic, command.mastered)
                state_repo.record_feedback_event(
                    {
                        "type": "grammar",
                        "lesson_id": command.lesson_id,
                        "language": command.language,
                        "topic": command.topic,
                        "mastered": command.mastered,
                        "sender": item.sender,
                    }
                )
                applied += 1

            processed_ids.append(item.msg_id)

        client.mark_seen(processed_ids)
        print(f"Feedback processed: {applied}/{len(items)}")
        return applied
