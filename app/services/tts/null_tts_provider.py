from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.tts.base import TTSProvider


@dataclass
class NullTTSProvider(TTSProvider):
    def synthesize(self, *, text: str, voice: str, output_path: Path) -> None:
        # Placeholder provider: intentionally does nothing.
        _ = (text, voice, output_path)
