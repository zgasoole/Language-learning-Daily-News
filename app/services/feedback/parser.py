from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

WORD_STATUSES = {"unknown", "fuzzy", "known"}


@dataclass
class FeedbackCommand:
    command_type: str
    lesson_id: str
    language: str
    word: str = ""
    word_status: str = ""
    topic: str = ""
    mastered: bool = False


def parse_feedback_body(body: str, token: str) -> Optional[FeedbackCommand]:
    # Expected body format from mailto links:
    # LLDN_FEEDBACK
    # token=...
    # type=word|grammar
    # lesson_id=...
    # language=de
    # ...
    lines = [line.strip() for line in body.replace("\r", "\n").split("\n") if line.strip()]
    if "LLDN_FEEDBACK" not in lines:
        return None

    kv: Dict[str, str] = {}
    for line in lines:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        kv[key.strip().lower()] = value.strip()

    if token and kv.get("token", "") != token:
        return None

    command_type = kv.get("type", "")
    lesson_id = kv.get("lesson_id", "")
    language = kv.get("language", "")

    if not command_type or not lesson_id:
        return None

    if command_type == "word":
        word = kv.get("word", "")
        status = kv.get("status", "")
        if not word or status not in WORD_STATUSES:
            return None
        return FeedbackCommand(
            command_type="word",
            lesson_id=lesson_id,
            language=language,
            word=word,
            word_status=status,
        )

    if command_type == "grammar":
        topic = kv.get("topic", "")
        mastered_raw = kv.get("mastered", "").lower()
        if not topic:
            return None
        mastered = mastered_raw in {"1", "true", "yes", "on"}
        return FeedbackCommand(
            command_type="grammar",
            lesson_id=lesson_id,
            language=language,
            topic=topic,
            mastered=mastered,
        )

    return None
