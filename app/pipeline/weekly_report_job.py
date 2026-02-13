from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.services.email.renderer import EmailRenderer
from app.services.email.smtp_sender import SMTPSender
from app.services.state.repository import StateRepository


@dataclass
class WeeklyReportJob:
    settings: Settings

    def run(self, dry_run: bool = False) -> None:
        state_repo = StateRepository(data_dir=self.settings.data_dir)
        report = self._build_report(state_repo)

        renderer = EmailRenderer(template_dir=self.settings.template_dir)
        html = renderer.render_weekly_report(report=report)

        if dry_run:
            output = self.settings.data_dir / "logs" / "latest_weekly_report_preview.html"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(html, encoding="utf-8")
            print(f"[DRY-RUN] Weekly report HTML saved to: {output}")
            return

        sender = SMTPSender(
            host=self.settings.smtp_host,
            port=self.settings.smtp_port,
            username=self.settings.smtp_user,
            password=self.settings.smtp_password,
            sender=self.settings.email_from,
        )
        sender.send_html(
            to_address=self.settings.email_to,
            subject=f"[LLDN Weekly] {report['range_label']}",
            html_body=html,
        )
        print(f"Weekly report sent to {self.settings.email_to}")

    def _build_report(self, state_repo: StateRepository) -> dict:
        now = datetime.utcnow()
        since = now - timedelta(days=7)

        sent_log = state_repo.load_json(state_repo.sent_log_path, {"lessons": []})
        feedback_log = state_repo.load_json(state_repo.feedback_log_path, {"events": []})
        vocab = state_repo.load_json(state_repo.vocab_path, {"words": {}})
        grammar = state_repo.load_json(state_repo.grammar_path, {"topics": {}})

        recent_lessons = [
            lesson
            for lesson in sent_log.get("lessons", [])
            if self._parse_ts(lesson.get("created_at", "")) >= since
        ]

        recent_feedback = [
            event
            for event in feedback_log.get("events", [])
            if self._parse_ts(event.get("timestamp", "")) >= since
        ]

        word_events = [event for event in recent_feedback if event.get("type") == "word"]
        grammar_events = [event for event in recent_feedback if event.get("type") == "grammar"]

        word_action_counts = Counter(str(event.get("status", "")) for event in word_events)
        unknown_words = Counter(
            str(event.get("word", "")).strip()
            for event in word_events
            if str(event.get("status", "")) == "unknown"
        )
        fuzzy_words = Counter(
            str(event.get("word", "")).strip()
            for event in word_events
            if str(event.get("status", "")) == "fuzzy"
        )

        vocab_status_counts = Counter(vocab.get("words", {}).values())

        grammar_topics_raw = grammar.get("topics", {})
        grammar_topics = {
            topic: self._normalize_grammar_status(value)
            for topic, value in grammar_topics_raw.items()
        }
        grammar_status_counts = Counter(grammar_topics.values())

        grammar_marked_this_week = sum(
            1
            for event in grammar_events
            if self._normalize_grammar_status(event.get("status", event.get("mastered", ""))) == "mastered"
        )

        return {
            "range_label": f"{since.date()} ~ {now.date()}",
            "lessons_count": len(recent_lessons),
            "feedback_count": len(recent_feedback),
            "word_unknown": word_action_counts.get("unknown", 0),
            "word_fuzzy": word_action_counts.get("fuzzy", 0),
            "word_known": word_action_counts.get("known", 0),
            "top_unknown_words": unknown_words.most_common(8),
            "top_fuzzy_words": fuzzy_words.most_common(8),
            "vocab_total": len(vocab.get("words", {})),
            "vocab_known_total": vocab_status_counts.get("known", 0),
            "vocab_fuzzy_total": vocab_status_counts.get("fuzzy", 0),
            "vocab_unknown_total": vocab_status_counts.get("unknown", 0),
            "grammar_total": len(grammar_topics),
            "grammar_mastered_total": grammar_status_counts.get("mastered", 0),
            "grammar_review_total": grammar_status_counts.get("review", 0),
            "grammar_marked_this_week": grammar_marked_this_week,
            "recent_lessons": sorted(
                recent_lessons,
                key=lambda item: item.get("created_at", ""),
                reverse=True,
            )[:7],
        }

    def _normalize_grammar_status(self, value: object) -> str:
        if isinstance(value, bool):
            return "mastered" if value else "review"

        text = str(value).strip().lower()
        if text in {"mastered", "review", "unknown"}:
            return text
        if text in {"1", "true", "yes", "on"}:
            return "mastered"
        if text in {"0", "false", "no", "off"}:
            return "review"
        return "unknown"

    def _parse_ts(self, value: str) -> datetime:
        if not value:
            return datetime(1970, 1, 1)
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime(1970, 1, 1)

        if parsed.tzinfo is None:
            return parsed
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
