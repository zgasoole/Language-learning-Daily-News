from __future__ import annotations

from typing import List

from app.language_packs.base import LanguagePack


class GermanPack(LanguagePack):
    code = "de"
    display_name = "Deutsch"

    def default_rss_urls(self) -> List[str]:
        return [
            "https://www.tagesschau.de/xml/rss2",
            "https://rss.dw.com/rdf/rss-de-all",
        ]

    def default_voice(self) -> str:
        return "de-DE-KatjaNeural"

    def system_prompt(self) -> str:
        return (
            "Du bist Sprachdidaktik-Experte fur Deutsch A1-A2. "
            "Erzeuge korrektes, klares und lernorientiertes Material."
        )

    def lesson_prompt(self, article_title: str, article_text: str, cefr_level: str) -> str:
        return f"""
Nutze den folgenden Nachrichteninhalt und erstelle Lernmaterial fur Deutsch {cefr_level}.

Titel der Quelle:
{article_title}

Text der Quelle:
{article_text}

Ausgabe NUR als gueltiges JSON ohne Markdown.
Schema:
{{
  "title": "Kurzer deutscher Titel",
  "news_text": "Ca. 200 Worter, Niveau {cefr_level}, klare Satze",
  "chinese_translation": "Vollstandige chinesische Ubersetzung des news_text",
  "keywords": [
    {{
      "word": "...",
      "part_of_speech": "...",
      "explanation": "Bedeutung im Kontext auf Deutsch, einfach",
      "etymology": "Kurze Wortherkunft",
      "morphology": "Wortstamm/Präfix/Suffix/Komposition",
      "tense_or_inflection": "Bei Verb: typische Zeitformen; bei Nomen: Genus/Plural/Flexion",
      "translation_en": "...",
      "translation_zh": "...",
      "example_sentence_de": "Kurzer Beispielsatz"
    }}
  ],
  "grammar_point": {{
    "topic": "Wichtiges Grammatikthema aus dem Text",
    "source_sentence": "Originalsatz aus news_text",
    "explanation_zh": "中文解释",
    "example_de": "Zusatzbeispiel auf Deutsch"
  }},
  "audio_text": "gleich wie news_text"
}}

Harte Regeln:
1) keywords genau 5 Eintrage.
2) Keine erfundenen Fakten, bleibe nah am Quelltext.
3) news_text muss fur A1-A2 lernbar sein.
4) chinese_translation muss vollstandig sein.
""".strip()
