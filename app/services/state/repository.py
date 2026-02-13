from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.models.schemas import DailyLesson


@dataclass
class StateRepository:
    data_dir: Path

    @property
    def vocab_path(self) -> Path:
        return self.data_dir / "progress" / "vocabulary_status.json"

    @property
    def grammar_path(self) -> Path:
        return self.data_dir / "progress" / "grammar_status.json"

    @property
    def sent_log_path(self) -> Path:
        return self.data_dir / "progress" / "sent_log.json"

    @property
    def feedback_log_path(self) -> Path:
        return self.data_dir / "progress" / "feedback_log.json"

    def load_json(self, path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def save_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def apply_existing_progress(self, lesson: DailyLesson) -> None:
        vocab = self.load_json(self.vocab_path, {"words": {}})
        grammar = self.load_json(self.grammar_path, {"topics": {}})

        word_map = vocab.get("words", {})
        for item in lesson.keywords:
            status = str(word_map.get(item.word, "unknown"))
            item.mastery_level = status

        topic_map = grammar.get("topics", {})
        lesson.grammar_point.mastered = bool(topic_map.get(lesson.grammar_point.topic, False))

    def record_sent_lesson(self, lesson: DailyLesson) -> None:
        sent_log = self.load_json(self.sent_log_path, {"lessons": []})
        sent_log.setdefault("lessons", []).append(
            {
                "lesson_id": lesson.lesson_id,
                "title": lesson.title,
                "language": lesson.language,
                "created_at": lesson.created_at,
                "source_urls": lesson.source_urls,
            }
        )
        self.save_json(self.sent_log_path, sent_log)

    def upsert_word_status(self, word: str, status: str) -> None:
        vocab = self.load_json(self.vocab_path, {"words": {}})
        vocab.setdefault("words", {})[word] = status
        self.save_json(self.vocab_path, vocab)

    def set_grammar_mastered(self, topic: str, mastered: bool) -> None:
        grammar = self.load_json(self.grammar_path, {"topics": {}})
        grammar.setdefault("topics", {})[topic] = mastered
        self.save_json(self.grammar_path, grammar)

    def record_feedback_event(self, event: Dict[str, Any]) -> None:
        payload = self.load_json(self.feedback_log_path, {"events": []})
        item = {"timestamp": datetime.utcnow().isoformat(), **event}
        payload.setdefault("events", []).append(item)
        self.save_json(self.feedback_log_path, payload)
