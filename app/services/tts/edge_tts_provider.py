from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from app.services.tts.base import TTSProvider


@dataclass
class EdgeTTSProvider(TTSProvider):
    max_attempts: int = 3

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

        last_error = ""
        for attempt in range(1, self.max_attempts + 1):
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                return

            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            last_error = stderr or stdout or f"exit_code={result.returncode}"

            if attempt < self.max_attempts:
                time.sleep(attempt)

        raise RuntimeError(
            f"edge-tts failed after {self.max_attempts} attempts: {last_error}"
        )
