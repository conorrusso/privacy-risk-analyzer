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
import logging
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

    @staticmethod
    def _load_key(env_var: str) -> str:
        """Load an API key from environment variable or config.env file."""
        import os
        from pathlib import Path

        key = os.environ.get(env_var, "")
        if key:
            return key
        env_file = Path.home() / ".bandit" / "config.env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith(f"{env_var}="):
                    return line.split("=", 1)[1].strip()
        return ""

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
        add even when instructed not to. Uses robust parsing with truncation
        recovery for large responses.
        """
        resp = self.complete(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=max_tokens,
        )
        text = resp.text.strip()
        return _parse_llm_json(text)


def _parse_llm_json(text: str, context: str = "") -> dict:
    """
    Robustly parse JSON from LLM response.
    Handles truncation, trailing commas, code fences.
    """
    logger = logging.getLogger("bandit")

    # Step 1: strip code fences
    text = text.replace("```json", "").replace("```", "").strip()

    # Step 2: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Step 3: fix trailing commas
    try:
        cleaned = re.sub(r',\s*([}\]])', r'\1', text)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Step 4: truncation recovery — if response was cut off mid-JSON,
    # try to close open structures
    try:
        opens = text.count('{') - text.count('}')
        opens_sq = text.count('[') - text.count(']')

        truncated = text.rstrip().rstrip(',')

        closing = (']' * max(0, opens_sq) +
                   '}' * max(0, opens))
        recovered = (
            truncated + '"' + closing
            if not truncated.endswith('"')
            else truncated + closing
        )

        cleaned_recovered = re.sub(
            r',\s*([}\]])', r'\1', recovered
        )
        result = json.loads(cleaned_recovered)
        logger.warning(
            f"LLM JSON was truncated"
            + (f" ({context})" if context else "")
            + " — recovered partial result. "
            "Increase max_tokens if this recurs."
        )
        return result
    except json.JSONDecodeError:
        pass

    # Step 5: extract outermost object
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            cleaned = re.sub(
                r',\s*([}\]])', r'\1', match.group(0)
            )
            return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # All attempts failed
    logger.error(
        f"Could not parse LLM JSON"
        + (f" ({context})" if context else "")
        + f". First 300 chars: {text[:300]}"
    )
    raise ValueError(
        "LLM returned malformed JSON: check logs for details."
    )
