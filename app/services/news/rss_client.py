from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

import feedparser
import trafilatura

from app.models.schemas import SourceArticle


@dataclass
class RSSNewsClient:
    max_articles: int = 8

    def fetch_latest(self, rss_urls: List[str]) -> List[SourceArticle]:
        articles: List[SourceArticle] = []

        for rss_url in rss_urls:
            parsed = feedparser.parse(rss_url)
            for entry in parsed.entries[: self.max_articles]:
                link = str(getattr(entry, "link", "")).strip()
                if not link:
                    continue

                title = str(getattr(entry, "title", "")).strip() or "Untitled"
                published = str(getattr(entry, "published", "")).strip() or datetime.utcnow().isoformat()
                text = self._extract_text(link)

                if not text:
                    summary = str(getattr(entry, "summary", "")).strip()
                    text = summary

                if not text:
                    continue

                articles.append(
                    SourceArticle(
                        title=title,
                        url=link,
                        published=published,
                        text=text,
                    )
                )

            if articles:
                break

        return articles

    def _extract_text(self, url: str) -> str:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""

        extracted = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_links=False,
            output_format="txt",
        )
        return (extracted or "").strip()
