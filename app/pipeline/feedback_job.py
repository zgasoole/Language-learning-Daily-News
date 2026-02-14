from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.services.feedback.imap_client import IMAPFeedbackClient
from app.services.feedback.parser import parse_feedback_commands
from app.services.state.repository import StateRepository


@dataclass
class FeedbackJob:
    settings: Settings

    def run(self) -> int:
        if not all([self.settings.imap_host, self.settings.imap_user, self.settings.imap_password]):
            print("Feedback ingest skipped: IMAP config missing")
            return 0

        allowed_senders = self.settings.feedback_allowed_senders if self.settings.feedback_strict_sender else []
        client = IMAPFeedbackClient(
            host=self.settings.imap_host,
            port=self.settings.imap_port,
            username=self.settings.imap_user,
            password=self.settings.imap_password,
            subject_prefix=self.settings.feedback_subject_prefix,
            allowed_senders=allowed_senders,
        )
        state_repo = StateRepository(data_dir=self.settings.data_dir)

        processed_keys = state_repo.get_processed_feedback_message_keys()
        items = client.fetch_recent_items(limit=240)
        processed_ids: list[bytes] = []
        applied = 0

        for item in items:
            if item.message_key in processed_keys:
                continue

            commands = parse_feedback_commands(item.body, token=self.settings.feedback_token)
            if not commands:
                state_repo.record_feedback_event(
                    {
                        "type": "skip",
                        "reason": "no_valid_commands_or_token_mismatch",
                        "subject": item.subject,
                        "sender": item.sender,
                    }
                )
                state_repo.mark_feedback_message_processed(item.message_key)
                processed_keys.add(item.message_key)
                processed_ids.append(item.msg_id)
                continue

            for command in commands:
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
                    state_repo.set_grammar_status(command.topic, command.grammar_status)
                    state_repo.record_feedback_event(
                        {
                            "type": "grammar",
                            "lesson_id": command.lesson_id,
                            "language": command.language,
                            "topic": command.topic,
                            "status": command.grammar_status,
                            "sender": item.sender,
                        }
                    )
                    applied += 1

            state_repo.mark_feedback_message_processed(item.message_key)
            processed_keys.add(item.message_key)
            processed_ids.append(item.msg_id)

        client.mark_seen(processed_ids)
        print(f"Feedback processed: {applied}/{len(items)}")
        return applied
