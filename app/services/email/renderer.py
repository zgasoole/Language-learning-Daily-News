from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote, urlencode

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.schemas import DailyLesson


WORD_STATUS_LABELS: Dict[str, str] = {
    "unknown": "完全不懂",
    "fuzzy": "隐约懂点",
    "known": "熟悉",
}

GRAMMAR_STATUS_LABELS: Dict[str, str] = {
    "unknown": "未标记",
    "review": "需要再学习",
    "mastered": "已掌握",
}


@dataclass
class EmailRenderer:
    template_dir: Path
    feedback_email: str = ""
    feedback_subject_prefix: str = "[LLDN]"
    feedback_token: str = ""

    def render_daily_lesson(
        self,
        *,
        lesson: DailyLesson,
        audio_url: Optional[str],
        has_audio_attachment: bool,
    ) -> str:
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        word_cards = []
        for idx, item in enumerate(lesson.keywords, start=1):
            status = item.mastery_level if item.mastery_level in WORD_STATUS_LABELS else "unknown"
            word_cards.append(
                {
                    "idx": idx,
                    "word": item,
                    "status": status,
                    "status_label": WORD_STATUS_LABELS.get(status, "未标记"),
                }
            )

        grammar_status = lesson.grammar_point.status if lesson.grammar_point.status in GRAMMAR_STATUS_LABELS else "unknown"

        template = env.get_template("daily_email.html.j2")
        return template.render(
            lesson=lesson,
            sentence_pairs=lesson.sentence_pairs,
            word_cards=word_cards,
            grammar_status=grammar_status,
            grammar_status_label=GRAMMAR_STATUS_LABELS.get(grammar_status, "未标记"),
            feedback_form_action=self._feedback_form_action(lesson.lesson_id),
            feedback_fallback_link=self._feedback_fallback_link(lesson),
            feedback_token=self.feedback_token,
            audio_url=audio_url,
            has_audio_attachment=has_audio_attachment,
            today=datetime.utcnow().strftime("%Y-%m-%d"),
        )

    def render_weekly_report(self, report: Dict[str, object]) -> str:
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template("weekly_report.html.j2")
        return template.render(
            report=report,
            today=datetime.utcnow().strftime("%Y-%m-%d"),
        )

    def _feedback_form_action(self, lesson_id: str) -> str:
        if not self.feedback_email:
            return "#"
        subject = f"{self.feedback_subject_prefix} batch feedback {lesson_id}"
        query = urlencode({"subject": subject}, quote_via=quote)
        return f"mailto:{self.feedback_email}?{query}"

    def _feedback_fallback_link(self, lesson: DailyLesson) -> str:
        body_lines = [
            "LLDN_FEEDBACK",
            f"token={self.feedback_token}",
            "type=batch",
            "lln_feedback=1",
            f"lesson_id={lesson.lesson_id}",
            f"language={lesson.language}",
        ]

        for idx, item in enumerate(lesson.keywords, start=1):
            current = item.mastery_level if item.mastery_level in WORD_STATUS_LABELS else "unknown"
            body_lines.append(f"word_{idx}_text={item.word}")
            body_lines.append(f"word_{idx}_status={current}")

        body_lines.append(f"grammar_topic={lesson.grammar_point.topic}")
        body_lines.append("grammar_status=review")

        subject = f"{self.feedback_subject_prefix} batch feedback {lesson.lesson_id}"
        query = urlencode({"subject": subject, "body": "\n".join(body_lines)}, quote_via=quote)
        return f"mailto:{self.feedback_email}?{query}" if self.feedback_email else "#"
