"""
Provider-agnostic LLM adapter layer.
Supports: Anthropic, OpenAI, Google Gemini, Ollama (local), Mistral.
"""
from core.llm.factory import load_provider

__all__ = ["load_provider"]
