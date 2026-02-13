from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SourceArticle:
    title: str
    url: str
    published: str
    text: str


@dataclass
class WordExplanation:
    word: str
    part_of_speech: str
    explanation: str
    etymology: str
    morphology: str
    tense_or_inflection: str
    translation_en: str
    translation_zh: str
    example_sentence_de: str
    mastery_level: str = "unknown"


@dataclass
class GrammarPoint:
    topic: str
    source_sentence: str
    explanation_zh: str
    example_de: str
    mastered: bool = False


@dataclass
class DailyLesson:
    lesson_id: str
    language: str
    cefr_level: str
    title: str
    news_text: str
    chinese_translation: str
    keywords: List[WordExplanation]
    grammar_point: GrammarPoint
    source_urls: List[str]
    audio_text: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data

    @staticmethod
    def from_llm_payload(payload: Dict[str, Any], *, lesson_id: str, language: str, cefr_level: str, source_urls: List[str]) -> "DailyLesson":
        keywords: List[WordExplanation] = []
        for item in payload.get("keywords", []):
            keywords.append(
                WordExplanation(
                    word=str(item.get("word", "")).strip(),
                    part_of_speech=str(item.get("part_of_speech", "")).strip(),
                    explanation=str(item.get("explanation", "")).strip(),
                    etymology=str(item.get("etymology", "")).strip(),
                    morphology=str(item.get("morphology", "")).strip(),
                    tense_or_inflection=str(item.get("tense_or_inflection", "")).strip(),
                    translation_en=str(item.get("translation_en", "")).strip(),
                    translation_zh=str(item.get("translation_zh", "")).strip(),
                    example_sentence_de=str(item.get("example_sentence_de", "")).strip(),
                    mastery_level="unknown",
                )
            )

        grammar = payload.get("grammar_point", {})
        grammar_point = GrammarPoint(
            topic=str(grammar.get("topic", "")).strip(),
            source_sentence=str(grammar.get("source_sentence", "")).strip(),
            explanation_zh=str(grammar.get("explanation_zh", "")).strip(),
            example_de=str(grammar.get("example_de", "")).strip(),
            mastered=False,
        )

        return DailyLesson(
            lesson_id=lesson_id,
            language=language,
            cefr_level=cefr_level,
            title=str(payload.get("title", "")).strip(),
            news_text=str(payload.get("news_text", "")).strip(),
            chinese_translation=str(payload.get("chinese_translation", "")).strip(),
            keywords=keywords[:5],
            grammar_point=grammar_point,
            source_urls=source_urls,
            audio_text=str(payload.get("audio_text", "")).strip() or str(payload.get("news_text", "")).strip(),
        )
