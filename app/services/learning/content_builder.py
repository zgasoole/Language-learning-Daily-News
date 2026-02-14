from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Set

from app.language_packs.base import LanguagePack
from app.models.schemas import DailyLesson, SourceArticle
from app.services.llm.gemini_client import GeminiClient


@dataclass
class LessonBuilder:
    gemini: GeminiClient
    language_pack: LanguagePack

    def build(self, article: SourceArticle, cefr_level: str, study_profile: Dict[str, Any] | None = None) -> DailyLesson:
        study_profile = study_profile or {}

        known_words: Set[str] = {
            self._norm(word)
            for word in study_profile.get("known_words", [])
            if str(word).strip()
        }
        forbid_extra: Set[str] = set()

        last_error = ""

        for attempt in range(1, 4):
            context = dict(study_profile)
            if forbid_extra:
                context["known_words"] = sorted(
                    set(context.get("known_words", [])) | set(forbid_extra)
                )

            payload = self.gemini.generate_json(
                system_prompt=self.language_pack.system_prompt(),
                user_prompt=self.language_pack.lesson_prompt(
                    article_title=article.title,
                    article_text=article.text,
                    cefr_level=cefr_level,
                    study_context=context,
                ),
            )

            effective_level = str(context.get("effective_level", cefr_level))
            lesson_id = f"{self.language_pack.code}-{datetime.utcnow().strftime('%Y%m%d')}"
            lesson = DailyLesson.from_llm_payload(
                payload,
                lesson_id=lesson_id,
                language=self.language_pack.code,
                cefr_level=effective_level,
                source_urls=[article.url],
            )

            if len(lesson.keywords) < 5:
                last_error = "Gemini did not return 5 keywords"
                continue
            if not lesson.news_text or not lesson.chinese_translation:
                last_error = "Gemini response missing news text or Chinese translation"
                continue

            known_hits = [word.word for word in lesson.keywords if self._norm(word.word) in known_words]
            if known_hits and attempt < 3:
                forbid_extra.update(self._norm(word) for word in known_hits)
                last_error = f"Returned known words in keyword set: {known_hits}. Retrying."
                continue

            return lesson

        raise RuntimeError(last_error or "Gemini failed to build a valid lesson")

    def _norm(self, value: str) -> str:
        text = value.strip().lower()
        return re.sub(r"[^a-zA-ZäöüßÄÖÜ0-9]+", "", text)
