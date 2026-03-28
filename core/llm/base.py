"""
Provider-agnostic LLM interface.

Architecture
------------
Each provider adapter subclasses BaseLLMProvider and implements complete().
The agent loop in BaseBandit only calls complete() and complete_json(),
so swapping providers requires no changes to agent code.

Message format
--------------
messages: list of {"role": "user"|"assistant", "content": str | list}
  - str content: simple text
  - list content: content blocks (tool_use, tool_result, text)
    Format follows Anthropic conventions; adapters translate as needed.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """A tool invocation requested by the LLM."""

    id: str
    name: str
    input: dict


@dataclass
class LLMResponse:
    """Normalised response from any LLM provider."""

    text: str                   # concatenated text content from the response
    tool_calls: list[ToolCall]  # empty list when stop_reason is "end_turn"
    stop_reason: str            # "end_turn" | "tool_use" | "max_tokens"
    raw: Any = None             # raw provider content blocks for round-tripping
                                # into subsequent messages in a tool-use loop


class BaseLLMProvider(ABC):
    """Abstract base for all LLM provider adapters."""

    model: str

    @abstractmethod
    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send messages and return a normalised response.

        Parameters
        ----------
        messages:
            Conversation history as dicts with "role" and "content" keys.
        tools:
            Tool schemas in Anthropic format. Adapters translate to their
            provider's native format.
        system:
            System prompt string.
        max_tokens:
            Token budget for the response.
        """

    def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> dict:
        """Complete with a single user prompt and return parsed JSON.

        Strips markdown code fences (```json ... ```) that models sometimes
        add even when instructed not to.
        """
        resp = self.complete(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=max_tokens,
        )
        text = resp.text.strip()
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        return json.loads(text)
