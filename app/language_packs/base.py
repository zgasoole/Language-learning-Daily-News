from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LanguagePack(ABC):
    code: str
    display_name: str

    @abstractmethod
    def default_rss_urls(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def system_prompt(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def lesson_prompt(
        self,
        article_title: str,
        article_text: str,
        cefr_level: str,
        study_context: Dict[str, Any] | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def default_voice(self) -> str:
        raise NotImplementedError
