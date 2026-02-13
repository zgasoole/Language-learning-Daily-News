from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote, urlencode

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.schemas import DailyLesson


STATUS_LABELS: Dict[str, str] = {
    "unknown": "完全不懂",
    "fuzzy": "隐约懂点",
    "known": "熟悉",
}


@dataclass
class EmailRenderer:
    template_dir: Path
    feedback_email: str
    feedback_subject_prefix: str
    feedback_token: str

    def render_daily_lesson(self, *, lesson: DailyLesson, audio_url: Optional[str]) -> str:
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        word_cards = []
        for item in lesson.keywords:
            links = {
                "unknown": self._word_feedback_link(lesson.lesson_id, lesson.language, item.word, "unknown"),
                "fuzzy": self._word_feedback_link(lesson.lesson_id, lesson.language, item.word, "fuzzy"),
                "known": self._word_feedback_link(lesson.lesson_id, lesson.language, item.word, "known"),
            }
            word_cards.append(
                {
                    "word": item,
                    "links": links,
                    "mastery_label": STATUS_LABELS.get(item.mastery_level, item.mastery_level or "unknown"),
                }
            )

        grammar_master_link = self._grammar_feedback_link(
            lesson_id=lesson.lesson_id,
            language=lesson.language,
            topic=lesson.grammar_point.topic,
            mastered=True,
        )

        template = env.get_template("daily_email.html.j2")
        return template.render(
            lesson=lesson,
            word_cards=word_cards,
            grammar_master_link=grammar_master_link,
            audio_url=audio_url,
            today=datetime.utcnow().strftime("%Y-%m-%d"),
        )

    def _word_feedback_link(self, lesson_id: str, language: str, word: str, status: str) -> str:
        body = "\n".join(
            [
                "LLDN_FEEDBACK",
                f"token={self.feedback_token}",
                "type=word",
                f"lesson_id={lesson_id}",
                f"language={language}",
                f"word={word}",
                f"status={status}",
            ]
        )
        subject = f"{self.feedback_subject_prefix} word {status}"
        return self._mailto(subject=subject, body=body)

    def _grammar_feedback_link(self, lesson_id: str, language: str, topic: str, mastered: bool) -> str:
        body = "\n".join(
            [
                "LLDN_FEEDBACK",
                f"token={self.feedback_token}",
                "type=grammar",
                f"lesson_id={lesson_id}",
                f"language={language}",
                f"topic={topic}",
                f"mastered={'true' if mastered else 'false'}",
            ]
        )
        subject = f"{self.feedback_subject_prefix} grammar mastered"
        return self._mailto(subject=subject, body=body)

    def _mailto(self, *, subject: str, body: str) -> str:
        if not self.feedback_email:
            return "#"
        query = urlencode({"subject": subject, "body": body}, quote_via=quote)
        return f"mailto:{self.feedback_email}?{query}"
