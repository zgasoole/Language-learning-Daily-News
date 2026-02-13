from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import quote_plus


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
    explanation_zh_detailed: str
    study_tips_zh: str
    reference_url: str
    example_de: str
    status: str = "unknown"


@dataclass
class SentencePair:
    de_sentence: str
    zh_sentence: str


@dataclass
class DailyLesson:
    lesson_id: str
    language: str
    cefr_level: str
    title: str
    news_text: str
    chinese_translation: str
    sentence_pairs: List[SentencePair]
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
        news_text = str(payload.get("news_text", "")).strip()
        chinese_translation = str(payload.get("chinese_translation", "")).strip()

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
        grammar_topic = str(grammar.get("topic", "")).strip()
        grammar_point = GrammarPoint(
            topic=grammar_topic,
            source_sentence=str(grammar.get("source_sentence", "")).strip(),
            explanation_zh=str(grammar.get("explanation_zh", "")).strip(),
            explanation_zh_detailed=str(grammar.get("explanation_zh_detailed", "")).strip(),
            study_tips_zh=str(grammar.get("study_tips_zh", "")).strip(),
            reference_url=DailyLesson._resolve_grammar_reference_url(
                raw_url=str(grammar.get("reference_url", "")).strip(),
                topic=grammar_topic,
            ),
            example_de=str(grammar.get("example_de", "")).strip(),
            status="unknown",
        )

        sentence_pairs = DailyLesson._build_sentence_pairs(
            payload_pairs=payload.get("sentence_pairs", []),
            news_text=news_text,
            chinese_translation=chinese_translation,
        )

        return DailyLesson(
            lesson_id=lesson_id,
            language=language,
            cefr_level=cefr_level,
            title=str(payload.get("title", "")).strip(),
            news_text=news_text,
            chinese_translation=chinese_translation,
            sentence_pairs=sentence_pairs,
            keywords=keywords[:5],
            grammar_point=grammar_point,
            source_urls=source_urls,
            audio_text=str(payload.get("audio_text", "")).strip() or news_text,
        )

    @staticmethod
    def _build_sentence_pairs(payload_pairs: List[Dict[str, Any]], news_text: str, chinese_translation: str) -> List[SentencePair]:
        pairs: List[SentencePair] = []

        for item in payload_pairs:
            de_sentence = str(item.get("de_sentence", "")).strip()
            zh_sentence = str(item.get("zh_sentence", "")).strip()
            if de_sentence or zh_sentence:
                pairs.append(SentencePair(de_sentence=de_sentence, zh_sentence=zh_sentence))

        if pairs:
            return pairs

        de_sentences = DailyLesson._split_de_sentences(news_text)
        zh_sentences = DailyLesson._split_zh_sentences(chinese_translation)

        max_len = max(len(de_sentences), len(zh_sentences), 1)
        aligned: List[SentencePair] = []
        for i in range(max_len):
            aligned.append(
                SentencePair(
                    de_sentence=de_sentences[i] if i < len(de_sentences) else "",
                    zh_sentence=zh_sentences[i] if i < len(zh_sentences) else "",
                )
            )
        return aligned

    @staticmethod
    def _split_de_sentences(text: str) -> List[str]:
        chunks = re.split(r"(?<=[.!?])\s+", text.strip())
        return [item.strip() for item in chunks if item.strip()]

    @staticmethod
    def _split_zh_sentences(text: str) -> List[str]:
        chunks = re.split(r"(?<=[。！？])\s*", text.strip())
        return [item.strip() for item in chunks if item.strip()]

    @staticmethod
    def _resolve_grammar_reference_url(raw_url: str, topic: str) -> str:
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            return raw_url
        query = quote_plus(f"Deutsch Grammatik {topic or 'A1 A2'}")
        return f"https://www.google.com/search?q={query}"
