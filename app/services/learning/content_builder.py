from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.language_packs.base import LanguagePack
from app.models.schemas import DailyLesson, SourceArticle
from app.services.llm.gemini_client import GeminiClient


@dataclass
class LessonBuilder:
    gemini: GeminiClient
    language_pack: LanguagePack

    def build(self, article: SourceArticle, cefr_level: str) -> DailyLesson:
        payload = self.gemini.generate_json(
            system_prompt=self.language_pack.system_prompt(),
            user_prompt=self.language_pack.lesson_prompt(
                article_title=article.title,
                article_text=article.text,
                cefr_level=cefr_level,
            ),
        )

        lesson_id = f"{self.language_pack.code}-{datetime.utcnow().strftime('%Y%m%d')}"
        lesson = DailyLesson.from_llm_payload(
            payload,
            lesson_id=lesson_id,
            language=self.language_pack.code,
            cefr_level=cefr_level,
            source_urls=[article.url],
        )

        if len(lesson.keywords) < 5:
            raise RuntimeError("Gemini did not return 5 keywords")
        if not lesson.news_text or not lesson.chinese_translation:
            raise RuntimeError("Gemini response missing news text or Chinese translation")

        return lesson
