from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.services.tts.base import TTSProvider


@dataclass
class EdgeTTSProvider(TTSProvider):
    def synthesize(self, *, text: str, voice: str, output_path: Path) -> None:
        if not shutil.which("edge-tts"):
            raise RuntimeError("edge-tts command not found; install dependencies first")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "edge-tts",
            "--voice",
            voice,
            "--text",
            text,
            "--write-media",
            str(output_path),
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"edge-tts failed: {result.stderr.strip()}")
