from __future__ import annotations

from typing import Any, Dict, List

from app.language_packs.base import LanguagePack


class JapanesePack(LanguagePack):
    code = "ja"
    display_name = "Japanese"

    def default_rss_urls(self) -> List[str]:
        return []

    def default_voice(self) -> str:
        return "ja-JP-NanamiNeural"

    def system_prompt(self) -> str:
        return (
            "You are a language pedagogy assistant for CEFR A1-A2 Japanese learners. "
            "Output educational content in strict JSON."
        )

    def lesson_prompt(
        self,
        article_title: str,
        article_text: str,
        cefr_level: str,
        study_context: Dict[str, Any] | None = None,
    ) -> str:
        _ = (article_title, article_text, cefr_level, study_context)
        return (
            "Japanese pack placeholder. Keep same JSON schema as German pack. "
            "Implement details when Japanese rollout starts."
        )
