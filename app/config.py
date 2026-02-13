from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value.strip())


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, fallback: List[str]) -> List[str]:
    value = os.getenv(name, "").strip()
    if not value:
        return fallback
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    template_dir: Path

    target_language: str
    cefr_level: str
    max_articles_to_scan: int

    gemini_api_key: str
    gemini_model: str
    gemini_fallback_models: List[str]

    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_from: str
    email_to: str

    imap_host: str
    imap_port: int
    imap_user: str
    imap_password: str

    feedback_email: str
    feedback_subject_prefix: str
    feedback_token: str
    feedback_allowed_senders: List[str]

    tts_provider: str
    edge_tts_voice: str
    tts_strict: bool
    audio_public_base_url: str

    de_rss_urls: List[str]
    fr_rss_urls: List[str]
    ja_rss_urls: List[str]

    dry_run: bool


def load_settings() -> Settings:
    project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
    data_dir = project_root / "data"
    template_dir = project_root / "app" / "templates"

    gmail_address = _env_str("GMAIL_ADDRESS", "")
    gmail_password = _env_str("GMAIL_APP_PASSWORD", "")

    email_from = _env_str("EMAIL_FROM", gmail_address)
    email_to = _env_str("EMAIL_TO", gmail_address)

    smtp_user = _env_str("SMTP_USER", gmail_address)
    smtp_password = _env_str("SMTP_PASSWORD", gmail_password)
    imap_user = _env_str("IMAP_USER", gmail_address)
    imap_password = _env_str("IMAP_PASSWORD", gmail_password)

    allowed_fallback = [item for item in [email_to, gmail_address] if item]
    allowed_senders = [
        sender.lower()
        for sender in _env_list("FEEDBACK_ALLOWED_SENDERS", allowed_fallback)
        if sender.strip()
    ]

    return Settings(
        project_root=project_root,
        data_dir=data_dir,
        template_dir=template_dir,
        target_language=_env_str("TARGET_LANGUAGE", "de").lower(),
        cefr_level=_env_str("CEFR_LEVEL", "A1").upper(),
        max_articles_to_scan=_env_int("MAX_ARTICLES_TO_SCAN", 8),
        gemini_api_key=_env_str("GEMINI_API_KEY", ""),
        gemini_model=_env_str("GEMINI_MODEL", "gemini-2.5-flash"),
        gemini_fallback_models=_env_list(
            "GEMINI_FALLBACK_MODELS",
            ["gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-flash-latest"],
        ),
        smtp_host=_env_str("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=_env_int("SMTP_PORT", 587),
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        email_from=email_from,
        email_to=email_to,
        imap_host=_env_str("IMAP_HOST", "imap.gmail.com"),
        imap_port=_env_int("IMAP_PORT", 993),
        imap_user=imap_user,
        imap_password=imap_password,
        feedback_email=_env_str("FEEDBACK_EMAIL", gmail_address or imap_user or email_from),
        feedback_subject_prefix=_env_str("FEEDBACK_SUBJECT_PREFIX", "[LLDN]"),
        feedback_token=_env_str("FEEDBACK_TOKEN", ""),
        feedback_allowed_senders=allowed_senders,
        tts_provider=_env_str("TTS_PROVIDER", "edge").lower(),
        edge_tts_voice=_env_str("EDGE_TTS_VOICE", "de-DE-KatjaNeural"),
        tts_strict=_env_bool("TTS_STRICT", False),
        audio_public_base_url=_env_str("AUDIO_PUBLIC_BASE_URL", ""),
        de_rss_urls=_env_list(
            "DE_RSS_URLS",
            [
                "https://www.tagesschau.de/xml/rss2",
                "https://rss.dw.com/rdf/rss-de-all",
            ],
        ),
        fr_rss_urls=_env_list("FR_RSS_URLS", []),
        ja_rss_urls=_env_list("JA_RSS_URLS", []),
        dry_run=_env_bool("DRY_RUN", False),
    )
