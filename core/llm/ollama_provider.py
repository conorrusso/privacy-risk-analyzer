"""
Ollama local provider adapter.

Runs models locally — no API key needed.
Must have Ollama running at base_url.

Install: https://ollama.ai
Run:     ollama serve
Models:  ollama pull llama3
"""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error

from core.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger("bandit")


class OllamaProvider(BaseLLMProvider):
    """Adapter for Ollama local chat API."""

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        **kwargs,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        ollama_messages = []
        if system:
            ollama_messages.append(
                {"role": "system", "content": system}
            )
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            ollama_messages.append(
                {"role": msg["role"], "content": content}
            )

        payload = json.dumps({
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            # Ollama can be slow for large prompts
            with urllib.request.urlopen(req, timeout=600) as resp:
                result = json.loads(resp.read())
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Ollama not reachable at {self.base_url}. "
                f"Is Ollama running? (ollama serve)\n{e}"
            ) from e

        text = result["message"]["content"]

        return LLMResponse(
            text=text,
            tool_calls=[],
            stop_reason="end_turn",
        )
