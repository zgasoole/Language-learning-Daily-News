from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict

import requests


@dataclass
class GeminiClient:
    api_key: str
    model: str
    timeout_seconds: int = 60

    def generate_json(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.5) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is empty")

        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

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

        resp = requests.post(endpoint, json=payload, timeout=self.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()

        text = self._extract_text(data)
        return self._parse_json(text)

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
