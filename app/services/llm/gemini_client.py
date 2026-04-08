from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

import requests

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


@dataclass
class GeminiClient:
    api_key: str
    model: str
    fallback_models: List[str] = field(default_factory=list)
    timeout_seconds: int = 60
    max_retries_per_model: int = 3
    backoff_base_seconds: int = 2

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
        failure_summaries: List[str] = []

        for model in self._candidate_models():
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            tried_models.append(model)
            total_attempts = self.max_retries_per_model + 1
            last_error = ""
            print(f"[Gemini] Trying model '{model}'")

            for attempt in range(1, total_attempts + 1):
                print(f"[Gemini] Model '{model}' attempt {attempt}/{total_attempts}")
                try:
                    resp = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout_seconds)
                except requests.RequestException as exc:
                    last_error = f"{exc.__class__.__name__}: {exc}"
                    if attempt < total_attempts:
                        self._sleep_before_retry(model=model, attempt=attempt, total_attempts=total_attempts, error=last_error)
                        continue
                    print(
                        f"[Gemini] Model '{model}' exhausted retries after request error. "
                        f"Switching to fallback model. error={last_error}"
                    )
                    break

                if resp.status_code == 404:
                    last_error = f"model_not_found:{model}"
                    print(f"[Gemini] Model '{model}' returned 404. Trying next fallback model.")
                    break

                if resp.status_code in RETRYABLE_STATUS_CODES:
                    body = self._truncate_body(resp)
                    last_error = f"retryable_http_{resp.status_code}: {body or '<empty>'}"
                    if attempt < total_attempts:
                        self._sleep_before_retry(model=model, attempt=attempt, total_attempts=total_attempts, error=last_error)
                        continue
                    print(
                        f"[Gemini] Model '{model}' exhausted retries after HTTP {resp.status_code}. "
                        f"Switching to fallback model."
                    )
                    break

                try:
                    resp.raise_for_status()
                except requests.HTTPError as exc:
                    body = self._truncate_body(resp)
                    raise RuntimeError(f"Gemini request failed on model '{model}': {exc}. body={body}") from exc

                data = resp.json()
                text = self._extract_text(data)
                return self._parse_json(text)

            failure_summaries.append(f"{model}={last_error or 'unknown_error'}")
            print(f"[Gemini] Fallback triggered after model '{model}' failed: {last_error or 'unknown_error'}")

        print(f"[Gemini] All candidate models failed. tried={tried_models}, errors={failure_summaries}")
        raise RuntimeError(
            "Gemini failed: no available model succeeded. "
            f"configured={self.model}, tried={tried_models}, errors={failure_summaries}. "
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

    def _sleep_before_retry(self, *, model: str, attempt: int, total_attempts: int, error: str) -> None:
        delay = self._backoff_seconds(attempt)
        print(
            f"[Gemini] Retryable error on model '{model}' attempt {attempt}/{total_attempts}: {error}. "
            f"Sleeping {delay}s before retry."
        )
        time.sleep(delay)

    def _backoff_seconds(self, attempt: int) -> int:
        return self.backoff_base_seconds * (2 ** (attempt - 1))

    def _truncate_body(self, resp: requests.Response) -> str:
        try:
            return resp.text[:400]
        except Exception:
            return ""

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
