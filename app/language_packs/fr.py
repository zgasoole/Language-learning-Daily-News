from __future__ import annotations

from typing import List

from app.language_packs.base import LanguagePack


class FrenchPack(LanguagePack):
    code = "fr"
    display_name = "Francais"

    def default_rss_urls(self) -> List[str]:
        return []

    def default_voice(self) -> str:
        return "fr-FR-DeniseNeural"

    def system_prompt(self) -> str:
        return (
            "You are a language pedagogy assistant for CEFR A1-A2 French. "
            "Output educational content in strict JSON."
        )

    def lesson_prompt(self, article_title: str, article_text: str, cefr_level: str) -> str:
        return (
            "French pack placeholder. Keep same JSON schema as German pack. "
            "Implement details when French rollout starts."
        )
