from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from app.models.schemas import DailyLesson


VALID_GRAMMAR_STATUSES = {"unknown", "review", "mastered"}


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
        raw_status = topic_map.get(lesson.grammar_point.topic, "unknown")
        lesson.grammar_point.status = self._normalize_grammar_status(raw_status)

    def build_study_profile(self, base_level: str) -> Dict[str, Any]:
        vocab = self.load_json(self.vocab_path, {"words": {}})
        words_map = vocab.get("words", {})

        known_words = sorted([word for word, status in words_map.items() if str(status) == "known"])
        fuzzy_words = sorted([word for word, status in words_map.items() if str(status) == "fuzzy"])
        unknown_words = sorted([word for word, status in words_map.items() if str(status) == "unknown"])

        effective_level = self._compute_effective_level(base_level=base_level, known_count=len(known_words))

        return {
            "base_level": base_level,
            "effective_level": effective_level,
            "known_count": len(known_words),
            "fuzzy_count": len(fuzzy_words),
            "unknown_count": len(unknown_words),
            "known_words": known_words[-300:],
            "priority_review_words": (unknown_words + fuzzy_words)[:160],
        }

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

    def set_grammar_status(self, topic: str, status: str) -> None:
        grammar = self.load_json(self.grammar_path, {"topics": {}})
        grammar.setdefault("topics", {})[topic] = self._normalize_grammar_status(status)
        self.save_json(self.grammar_path, grammar)

    def set_grammar_mastered(self, topic: str, mastered: bool) -> None:
        self.set_grammar_status(topic=topic, status="mastered" if mastered else "review")

    def record_feedback_event(self, event: Dict[str, Any]) -> None:
        payload = self.load_json(self.feedback_log_path, {"events": [], "processed_message_keys": []})
        item = {"timestamp": datetime.utcnow().isoformat(), **event}
        payload.setdefault("events", []).append(item)
        self.save_json(self.feedback_log_path, payload)

    def get_processed_feedback_message_keys(self) -> Set[str]:
        payload = self.load_json(self.feedback_log_path, {"events": [], "processed_message_keys": []})
        raw_keys = payload.get("processed_message_keys", [])
        return {str(item).strip() for item in raw_keys if str(item).strip()}

    def mark_feedback_message_processed(self, message_key: str) -> None:
        if not message_key.strip():
            return
        payload = self.load_json(self.feedback_log_path, {"events": [], "processed_message_keys": []})
        keys: List[str] = [str(item).strip() for item in payload.get("processed_message_keys", []) if str(item).strip()]
        if message_key not in keys:
            keys.append(message_key)
        payload["processed_message_keys"] = keys[-5000:]
        self.save_json(self.feedback_log_path, payload)

    def _normalize_grammar_status(self, value: Any) -> str:
        if isinstance(value, bool):
            return "mastered" if value else "review"

        text = str(value).strip().lower()
        if text in VALID_GRAMMAR_STATUSES:
            return text
        if text in {"true", "1", "yes", "on"}:
            return "mastered"
        if text in {"false", "0", "no", "off", "needs_review", "need_review"}:
            return "review"
        return "unknown"

    def _compute_effective_level(self, base_level: str, known_count: int) -> str:
        base = base_level.upper().strip()

        # Progressive difficulty target: as known words accumulate,
        # move from A1 -> A2 -> A2+ (close to B1 entry).
        if known_count >= 450:
            return "A2+"
        if known_count >= 180:
            return "A2"
        if known_count >= 70 and base == "A1":
            return "A1+"
        return base
