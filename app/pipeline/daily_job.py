from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import Settings
from app.language_packs import get_language_pack
from app.services.email.renderer import EmailRenderer
from app.services.email.smtp_sender import SMTPSender
from app.services.learning.content_builder import LessonBuilder
from app.services.llm.gemini_client import GeminiClient
from app.services.news.rss_client import RSSNewsClient
from app.services.state.repository import StateRepository
from app.services.tts.factory import build_tts_provider


@dataclass
class DailyJob:
    settings: Settings

    def run(self, dry_run: bool = False) -> None:
        language_pack = get_language_pack(self.settings.target_language)
        rss_urls = self._resolve_rss_urls(language_pack.code)
        if not rss_urls:
            raise RuntimeError(f"No RSS URLs configured for language: {language_pack.code}")

        news_client = RSSNewsClient(max_articles=self.settings.max_articles_to_scan)
        articles = news_client.fetch_latest(rss_urls)
        if not articles:
            raise RuntimeError("No articles fetched from configured RSS feeds")

        article = articles[0]

        gemini = GeminiClient(
            api_key=self.settings.gemini_api_key,
            model=self.settings.gemini_model,
            fallback_models=self.settings.gemini_fallback_models,
        )
        builder = LessonBuilder(gemini=gemini, language_pack=language_pack)
        lesson = builder.build(article=article, cefr_level=self.settings.cefr_level)

        state_repo = StateRepository(data_dir=self.settings.data_dir)
        state_repo.apply_existing_progress(lesson)

        audio_file = self._generate_audio(lesson.audio_text, language_pack.default_voice())
        audio_attached = bool(audio_file and audio_file.exists())
        audio_url = self._build_audio_url(audio_file)

        renderer = EmailRenderer(
            template_dir=self.settings.template_dir,
            feedback_email=self.settings.feedback_email,
            feedback_subject_prefix=self.settings.feedback_subject_prefix,
            feedback_token=self.settings.feedback_token,
        )
        html = renderer.render_daily_lesson(
            lesson=lesson,
            audio_url=audio_url,
            has_audio_attachment=audio_attached,
        )

        if dry_run:
            output = self.settings.data_dir / "logs" / "latest_email_preview.html"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(html, encoding="utf-8")
            print(f"[DRY-RUN] Email HTML saved to: {output}")
            print(f"[DRY-RUN] Audio file: {audio_file if audio_attached else 'none'}")
        else:
            sender = SMTPSender(
                host=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_user,
                password=self.settings.smtp_password,
                sender=self.settings.email_from,
            )
            subject = f"[{language_pack.display_name} {self.settings.cefr_level}] {lesson.title}"
            sender.send_html(
                to_address=self.settings.email_to,
                subject=subject,
                html_body=html,
                audio_attachment=audio_file if audio_attached else None,
            )
            print(f"Email sent to {self.settings.email_to}")

        state_repo.record_sent_lesson(lesson)

    def _resolve_rss_urls(self, lang_code: str) -> list[str]:
        if lang_code == "de":
            return self.settings.de_rss_urls
        if lang_code == "fr":
            return self.settings.fr_rss_urls
        if lang_code == "ja":
            return self.settings.ja_rss_urls
        return []

    def _generate_audio(self, text: str, fallback_voice: str) -> Optional[Path]:
        provider = build_tts_provider(self.settings.tts_provider)
        voice = self.settings.edge_tts_voice or fallback_voice
        output = self.settings.data_dir / "audio" / f"{datetime.utcnow().strftime('%Y%m%d')}-{self.settings.target_language}.mp3"

        try:
            provider.synthesize(text=text, voice=voice, output_path=output)
        except Exception as exc:
            if self.settings.tts_strict:
                raise RuntimeError(f"TTS generation failed in strict mode: {exc}") from exc
            print(f"[WARN] TTS generation failed, sending email without audio: {exc}")
            return None

        if not output.exists() or output.stat().st_size == 0:
            if self.settings.tts_strict:
                raise RuntimeError("TTS produced no usable audio file")
            print("[WARN] TTS produced no usable audio file, sending email without audio")
            return None

        return output

    def _build_audio_url(self, audio_file: Optional[Path]) -> Optional[str]:
        if not audio_file or not self.settings.audio_public_base_url:
            return None
        return f"{self.settings.audio_public_base_url.rstrip('/')}/{audio_file.name}"
