import json
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import requests

from app.services.llm.gemini_client import GeminiClient


class _FakeResponse:
    def __init__(self, status_code: int, *, payload: Optional[Dict[str, Any]] = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            error = requests.HTTPError(f"{self.status_code} Error")
            error.response = self
            raise error

    def json(self) -> Dict[str, Any]:
        return self._payload


def _success_response(payload: Dict[str, Any]) -> _FakeResponse:
    return _FakeResponse(
        200,
        payload={
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(payload)}],
                    }
                }
            ]
        },
    )


def _endpoint(model: str) -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def test_generate_json_retries_retryable_status_then_succeeds() -> None:
    client = GeminiClient(api_key="key", model="primary", fallback_models=["fallback"])
    responses: List[_FakeResponse] = [
        _FakeResponse(503, text='{"error":"busy"}'),
        _success_response({"ok": True}),
    ]
    seen_urls: List[str] = []
    sleep_calls: List[int] = []

    def fake_post(url: str, **_: Any) -> _FakeResponse:
        seen_urls.append(url)
        return responses.pop(0)

    with patch("app.services.llm.gemini_client.requests.post", side_effect=fake_post), patch(
        "app.services.llm.gemini_client.time.sleep", side_effect=sleep_calls.append
    ):
        result = client.generate_json(system_prompt="sys", user_prompt="user")

    assert result == {"ok": True}
    assert seen_urls == [_endpoint("primary"), _endpoint("primary")]
    assert sleep_calls == [2]


def test_generate_json_retries_timeout_then_succeeds() -> None:
    client = GeminiClient(api_key="key", model="primary")
    seen_urls: List[str] = []
    sleep_calls: List[int] = []

    def fake_post(url: str, **_: Any) -> _FakeResponse:
        seen_urls.append(url)
        if len(seen_urls) == 1:
            raise requests.Timeout("timed out")
        return _success_response({"ok": True})

    with patch("app.services.llm.gemini_client.requests.post", side_effect=fake_post), patch(
        "app.services.llm.gemini_client.time.sleep", side_effect=sleep_calls.append
    ):
        result = client.generate_json(system_prompt="sys", user_prompt="user")

    assert result == {"ok": True}
    assert seen_urls == [_endpoint("primary"), _endpoint("primary")]
    assert sleep_calls == [2]


def test_generate_json_falls_back_after_retry_exhaustion() -> None:
    client = GeminiClient(api_key="key", model="primary", fallback_models=["fallback"])
    responses: List[_FakeResponse] = [
        _FakeResponse(503, text='{"error":"busy"}'),
        _FakeResponse(503, text='{"error":"busy"}'),
        _FakeResponse(503, text='{"error":"busy"}'),
        _FakeResponse(503, text='{"error":"busy"}'),
        _success_response({"model": "fallback"}),
    ]
    seen_urls: List[str] = []
    sleep_calls: List[int] = []

    def fake_post(url: str, **_: Any) -> _FakeResponse:
        seen_urls.append(url)
        return responses.pop(0)

    with patch("app.services.llm.gemini_client.requests.post", side_effect=fake_post), patch(
        "app.services.llm.gemini_client.time.sleep", side_effect=sleep_calls.append
    ):
        result = client.generate_json(system_prompt="sys", user_prompt="user")

    assert result == {"model": "fallback"}
    assert seen_urls == [
        _endpoint("primary"),
        _endpoint("primary"),
        _endpoint("primary"),
        _endpoint("primary"),
        _endpoint("fallback"),
    ]
    assert sleep_calls == [2, 4, 8]


def test_generate_json_skips_missing_model_without_retry() -> None:
    client = GeminiClient(api_key="key", model="primary", fallback_models=["fallback"])
    responses: List[_FakeResponse] = [
        _FakeResponse(404, text='{"error":"not found"}'),
        _success_response({"model": "fallback"}),
    ]
    seen_urls: List[str] = []
    sleep_calls: List[int] = []

    def fake_post(url: str, **_: Any) -> _FakeResponse:
        seen_urls.append(url)
        return responses.pop(0)

    with patch("app.services.llm.gemini_client.requests.post", side_effect=fake_post), patch(
        "app.services.llm.gemini_client.time.sleep", side_effect=sleep_calls.append
    ):
        result = client.generate_json(system_prompt="sys", user_prompt="user")

    assert result == {"model": "fallback"}
    assert seen_urls == [_endpoint("primary"), _endpoint("fallback")]
    assert sleep_calls == []
