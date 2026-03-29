"""
Anthropic Claude adapter.

Usage
-----
provider = AnthropicProvider()                       # uses ANTHROPIC_API_KEY
provider = AnthropicProvider(model="claude-opus-4-6")
provider = AnthropicProvider(api_key="sk-ant-...")

The adapter passes tool schemas through to the Anthropic API unchanged —
they are already in Anthropic format (which is also what BaseBandit uses).
"""
from __future__ import annotations

from typing import Any

try:
    import anthropic as _anthropic
except ImportError as exc:
    raise ImportError(
        "anthropic package required — run: pip install anthropic"
    ) from exc

from core.llm.base import BaseLLMProvider, LLMResponse, ToolCall


class AnthropicProvider(BaseLLMProvider):
    """Adapter for Anthropic Claude models."""

    DEFAULT_MODEL = "claude-haiku-4-5-20251001"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or self.DEFAULT_MODEL
        # api_key=None → SDK reads ANTHROPIC_API_KEY from environment
        self._client = _anthropic.Anthropic(api_key=api_key)

    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        resp = self._client.messages.create(**kwargs)

        # Collect text across all TextBlocks
        text_parts = [
            block.text
            for block in resp.content
            if hasattr(block, "text")
        ]

        # Collect tool invocations across all ToolUseBlocks
        tool_calls = [
            ToolCall(id=block.id, name=block.name, input=dict(block.input))
            for block in resp.content
            if block.type == "tool_use"
        ]

        return LLMResponse(
            text="\n".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=resp.stop_reason,
            # Preserve raw content list so the tool loop can append it back
            # into the messages list verbatim — the Anthropic SDK accepts its
            # own block types as message content.
            raw=resp.content,
        )
