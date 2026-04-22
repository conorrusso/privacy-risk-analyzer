"""
Provider factory — load the configured AI provider.

Usage:
    from core.config import BanditConfig
    from core.llm.factory import load_provider

    cfg = BanditConfig().get_provider_config()
    provider = load_provider(cfg)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.llm.base import BaseLLMProvider


def load_provider(
    provider_cfg: dict | None = None,
) -> "BaseLLMProvider":
    """Load the configured AI provider.

    Reads from provider_cfg dict (from BanditConfig.get_provider_config()).
    Falls back to Anthropic + ANTHROPIC_API_KEY if no config provided.
    """
    if provider_cfg is None:
        provider_cfg = {}

    name = provider_cfg.get("name", "anthropic")
    model = provider_cfg.get("model", "")
    api_key = provider_cfg.get("api_key", "") or None
    ollama_url = provider_cfg.get(
        "ollama_base_url", "http://localhost:11434"
    )

    if name == "anthropic":
        from core.llm.anthropic import AnthropicProvider
        return AnthropicProvider(
            model=model or "claude-haiku-4-5-20251001",
            api_key=api_key,
        )

    elif name == "openai":
        from core.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(
            model=model or "gpt-4o",
            api_key=api_key,
        )

    elif name == "gemini":
        from core.llm.gemini_provider import GeminiProvider
        return GeminiProvider(
            model=model or "gemini-2.0-flash",
            api_key=api_key,
        )

    elif name == "ollama":
        from core.llm.ollama_provider import OllamaProvider
        return OllamaProvider(
            model=model or "llama3",
            base_url=ollama_url,
        )

    elif name == "mistral":
        from core.llm.mistral_provider import MistralProvider
        return MistralProvider(
            model=model or "mistral-large-latest",
            api_key=api_key,
        )

    else:
        raise ValueError(
            f"Unknown provider: '{name}'. "
            f"Valid options: anthropic, openai, "
            f"gemini, ollama, mistral"
        )
