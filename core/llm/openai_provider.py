"""
OpenAI provider adapter (GPT-4o, GPT-4o-mini).

Uses urllib — no SDK dependency required.
"""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error

from core.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger("bandit")


class OpenAIProvider(BaseLLMProvider):
    """Adapter for OpenAI chat completions API."""

    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or self._load_key("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "OpenAI API key not set. "
                "Set OPENAI_API_KEY or configure in bandit.config.yml."
            )

    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        oai_messages = []
        if system:
            oai_messages.append(
                {"role": "system", "content": system}
            )
        for msg in messages:
            content = msg.get("content", "")
            # Flatten content blocks to plain text
            if isinstance(content, list):
                content = "\n".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            oai_messages.append(
                {"role": msg["role"], "content": content}
            )

        payload: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": oai_messages,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.BASE_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"OpenAI API error {e.code}: {body[:500]}"
            ) from e

        choice = result["choices"][0]
        text = choice["message"].get("content", "")
        stop = (
            "end_turn" if choice.get("finish_reason") == "stop"
            else choice.get("finish_reason", "end_turn")
        )

        return LLMResponse(
            text=text,
            tool_calls=[],
            stop_reason=stop,
        )
