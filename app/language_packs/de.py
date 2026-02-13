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
  "sentence_pairs": [
    {{ "de_sentence": "Ein Satz aus news_text", "zh_sentence": "对应中文翻译" }}
  ],
  "keywords": [
    {{
      "word": "...",
      "part_of_speech": "...",
      "explanation": "Bedeutung im Kontext auf Deutsch, einfach",
      "etymology": "Kurze Wortherkunft",
      "morphology": "必须中文详细拆解：词干/前缀/后缀分别是什么意思，组合后为什么是这个意思。示例格式：Kinderbetreuung = Kind(孩子) + Betreuung(照护，来自 betreuen 看护 + -ung 名词后缀)",
      "tense_or_inflection": "Bei Verb: typische Zeitformen; bei Nomen: Genus/Plural/Flexion",
      "translation_en": "...",
      "translation_zh": "...",
      "example_sentence_de": "Kurzer Beispielsatz"
    }}
  ],
  "grammar_point": {{
    "topic": "Wichtiges Grammatikthema aus dem Text",
    "source_sentence": "Originalsatz aus news_text",
    "explanation_zh": "中文核心解释（2-3句）",
    "explanation_zh_detailed": "中文详细讲解（教材风格，分点讲透：结构、位置、变形、易错点、对比）",
    "study_tips_zh": "中文复习建议（如何练习）",
    "reference_url": "https://... 一个可访问的语法学习页面",
    "example_de": "Zusatzbeispiel auf Deutsch"
  }},
  "audio_text": "gleich wie news_text"
}}

Harte Regeln:
1) keywords genau 5 Eintrage.
2) Keine erfundenen Fakten, bleibe nah am Quelltext.
3) news_text muss fur A1-A2 lernbar sein.
4) chinese_translation muss vollstandig sein.
5) sentence_pairs muss die Satze aus news_text in gleicher Reihenfolge enthalten.
""".strip()
