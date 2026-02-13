from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, *, text: str, voice: str, output_path: Path) -> None:
        raise NotImplementedError
