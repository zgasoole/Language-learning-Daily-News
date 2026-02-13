from __future__ import annotations

from app.services.tts.base import TTSProvider
from app.services.tts.edge_tts_provider import EdgeTTSProvider
from app.services.tts.null_tts_provider import NullTTSProvider


def build_tts_provider(provider_name: str) -> TTSProvider:
    provider_name = provider_name.strip().lower()
    if provider_name == "edge":
        return EdgeTTSProvider()
    if provider_name == "none":
        return NullTTSProvider()
    raise ValueError(f"Unsupported TTS provider: {provider_name}")
