from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
from urllib.parse import parse_qs, unquote_plus

WORD_STATUSES = {"unknown", "fuzzy", "known"}
GRAMMAR_STATUSES = {"mastered", "review"}


@dataclass
class FeedbackCommand:
    command_type: str
    lesson_id: str
    language: str
    word: str = ""
    word_status: str = ""
    topic: str = ""
    grammar_status: str = ""


def parse_feedback_commands(body: str, token: str) -> List[FeedbackCommand]:
    kv = _extract_kv(body)
    if not kv:
        return []

    if token and kv.get("token", "") != token:
        return []

    commands: List[FeedbackCommand] = []

    # Legacy single-command mode
    legacy = _parse_legacy_single(kv)
    if legacy:
        commands.append(legacy)

    # Batch mode from form/template
    commands.extend(_parse_batch(kv))

    return commands


def parse_feedback_body(body: str, token: str) -> FeedbackCommand | None:
    # Backward-compatible helper used by older tests/calls.
    commands = parse_feedback_commands(body, token)
    return commands[0] if commands else None


def _extract_kv(body: str) -> Dict[str, str]:
    normalized = body.replace("\r", "\n")

    kv: Dict[str, str] = {}

    lines = [line.strip() for line in normalized.split("\n") if line.strip()]
    for line in lines:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        k = key.strip().lower()
        v = unquote_plus(value.strip())
        if k and k not in kv:
            kv[k] = v

    # Some clients may send one-line query-style payload.
    query_like = "&".join(lines)
    if "=" in query_like and "&" in query_like:
        parsed = parse_qs(query_like, keep_blank_values=True)
        for key, values in parsed.items():
            k = key.strip().lower()
            if not k or k in kv or not values:
                continue
            kv[k] = unquote_plus(values[0].strip())

    return kv


def _parse_legacy_single(kv: Dict[str, str]) -> FeedbackCommand | None:
    if kv.get("lldn_feedback") is None and kv.get("type", "") not in {"word", "grammar"}:
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
        if not topic:
            return None

        mastered_raw = kv.get("mastered", "").lower().strip()
        status = "mastered" if mastered_raw in {"1", "true", "yes", "on"} else "review"
        return FeedbackCommand(
            command_type="grammar",
            lesson_id=lesson_id,
            language=language,
            topic=topic,
            grammar_status=status,
        )

    return None


def _parse_batch(kv: Dict[str, str]) -> List[FeedbackCommand]:
    if kv.get("lln_feedback", "") not in {"1", "true", "yes", "on"} and kv.get("type", "") != "batch":
        # No explicit batch flag; still allow if indexed fields exist.
        has_indexed_word = any(key.startswith("word_") and key.endswith("_status") for key in kv)
        if not has_indexed_word and "grammar_status" not in kv:
            return []

    lesson_id = kv.get("lesson_id", "")
    language = kv.get("language", "")
    if not lesson_id:
        return []

    out: List[FeedbackCommand] = []

    for idx in range(1, 31):
        word = kv.get(f"word_{idx}_text", "").strip()
        status = kv.get(f"word_{idx}_status", "").strip().lower()
        if not word or status not in WORD_STATUSES:
            continue
        out.append(
            FeedbackCommand(
                command_type="word",
                lesson_id=lesson_id,
                language=language,
                word=word,
                word_status=status,
            )
        )

    topic = kv.get("grammar_topic", "").strip() or kv.get("topic", "").strip()
    grammar_status = kv.get("grammar_status", "").strip().lower()
    if topic and grammar_status in GRAMMAR_STATUSES:
        out.append(
            FeedbackCommand(
                command_type="grammar",
                lesson_id=lesson_id,
                language=language,
                topic=topic,
                grammar_status=grammar_status,
            )
        )

    return out
