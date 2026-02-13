from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

import requests


@dataclass
class GeminiClient:
    api_key: str
    model: str
    fallback_models: List[str] = field(default_factory=list)
    timeout_seconds: int = 60

    def generate_json(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.5) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is empty")

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        tried_models: List[str] = []
        last_error: str = ""

        for model in self._candidate_models():
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            tried_models.append(model)

            resp = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout_seconds)
            if resp.status_code == 404:
                last_error = f"model_not_found:{model}"
                continue

            try:
                resp.raise_for_status()
            except requests.HTTPError as exc:
                body = ""
                try:
                    body = resp.text[:400]
                except Exception:
                    body = ""
                raise RuntimeError(f"Gemini request failed on model '{model}': {exc}. body={body}") from exc

            data = resp.json()
            text = self._extract_text(data)
            return self._parse_json(text)

        raise RuntimeError(
            "Gemini failed: no available model succeeded. "
            f"configured={self.model}, tried={tried_models}, last_error={last_error}. "
            "Set GEMINI_MODEL or GEMINI_FALLBACK_MODELS to currently available models."
        )

    def _candidate_models(self) -> List[str]:
        candidates = [self.model] + list(self.fallback_models) + [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-flash-latest",
        ]

        deduped: List[str] = []
        seen = set()
        for item in candidates:
            name = str(item).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            deduped.append(name)
        return deduped

    def _extract_text(self, payload: Dict[str, Any]) -> str:
        candidates = payload.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates: {payload}")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError(f"Gemini returned empty content parts: {payload}")

        text = str(parts[0].get("text", "")).strip()
        if not text:
            raise RuntimeError(f"Gemini returned blank text: {payload}")
        return text

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            cleaned = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()
            return json.loads(cleaned)
