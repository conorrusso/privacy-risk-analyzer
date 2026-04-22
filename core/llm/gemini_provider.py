"""
Google Gemini provider adapter (Gemini 2.0 Flash, 1.5 Pro).

Uses urllib — no SDK dependency required.
"""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error

from core.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger("bandit")


class GeminiProvider(BaseLLMProvider):
    """Adapter for Google Gemini generateContent API."""

    BASE_URL = (
        "https://generativelanguage.googleapis.com"
        "/v1beta/models/{model}:generateContent"
        "?key={api_key}"
    )

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or self._load_key("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Gemini API key not set. "
                "Set GEMINI_API_KEY or configure in bandit.config.yml."
            )

    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        # Build content parts from messages
        parts = []
        if system:
            parts.append({"text": system + "\n\n"})
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            parts.append({"text": content})

        payload = json.dumps({
            "contents": [{"parts": parts}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
            },
        }).encode("utf-8")

        url = self.BASE_URL.format(
            model=self.model,
            api_key=self.api_key,
        )

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Gemini API error {e.code}: {body[:500]}"
            ) from e

        text = (
            result["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        return LLMResponse(
            text=text,
            tool_calls=[],
            stop_reason="end_turn",
        )
