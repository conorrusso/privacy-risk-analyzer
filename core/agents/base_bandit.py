"""
Shared agentic tool-use loop.

BaseBandit drives the LLM ↔ tool execution cycle. Subclasses register
tools and call run_tool_loop() from their assess() method.

Tool-use message format (Anthropic convention, used throughout)
---------------------------------------------------------------
After an LLM response that includes tool calls, we append:
  {"role": "assistant", "content": <raw content blocks>}

Then for each tool result:
  {"role": "user", "content": [
      {"type": "tool_result", "tool_use_id": "...", "content": "<result>"}
  ]}

This is why LLMResponse.raw preserves the provider's native content blocks —
they get round-tripped back into messages without re-serialisation.
"""
from __future__ import annotations

from typing import Callable

from core.llm.base import BaseLLMProvider, LLMResponse


class BaseBandit:
    """Base class for all Bandit agents."""

    MAX_TURNS = 12

    def __init__(self, provider: BaseLLMProvider) -> None:
        self.provider = provider

    def run_tool_loop(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_registry: dict[str, Callable[..., str]],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Drive the LLM ↔ tool loop until stop_reason == 'end_turn'.

        Mutates *messages* in place so the full conversation is available
        to the caller after the loop ends.

        Parameters
        ----------
        messages:
            Initial conversation (usually a single user message).
            Extended in-place each turn.
        tools:
            Tool schemas passed to the provider on every call.
        tool_registry:
            Maps tool name → callable(**input) → str result.
            Unknown tool names return an error string rather than raising.
        system:
            System prompt.
        max_tokens:
            Token budget per LLM call.

        Returns
        -------
        LLMResponse
            The final response (stop_reason == 'end_turn').

        Raises
        ------
        RuntimeError
            If MAX_TURNS is exceeded without end_turn.
        """
        for turn in range(self.MAX_TURNS):
            response = self.provider.complete(
                messages=messages,
                tools=tools,
                system=system,
                max_tokens=max_tokens,
            )

            if not response.tool_calls or response.stop_reason == "end_turn":
                messages.append({
                    "role": "assistant",
                    "content": response.raw or response.text,
                })
                return response

            # Append raw assistant content (preserves tool_use blocks for
            # the API to validate in the next turn)
            messages.append({
                "role": "assistant",
                "content": response.raw,
            })

            # Execute each tool and collect results
            tool_results = []
            for tc in response.tool_calls:
                fn = tool_registry.get(tc.name)
                if fn is None:
                    result = f"Error: unknown tool '{tc.name}'"
                else:
                    try:
                        result = fn(**tc.input)
                    except Exception as exc:
                        result = f"Error executing {tc.name}: {exc}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": str(result)[:50_000],
                })

            messages.append({"role": "user", "content": tool_results})

        raise RuntimeError(
            f"Tool loop exceeded {self.MAX_TURNS} turns without end_turn. "
            "The agent may be stuck. Increase MAX_TURNS or check the system prompt."
        )
