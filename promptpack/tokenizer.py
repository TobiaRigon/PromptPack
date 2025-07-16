"""Utility functions for token counting with real tokenization models."""

from __future__ import annotations

from .settings import load_settings

try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    tiktoken = None  # fallback if tiktoken is missing

try:
    from anthropic import Anthropic  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Anthropic = None

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    genai = None


def gpt_tokens(text: str) -> int:
    """Count tokens using OpenAI tiktoken if available."""
    if tiktoken is None:
        # Fallback semplice se la libreria non è disponibile
        return len(text) // 4
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def claude_tokens(text: str) -> int:
    """Count tokens using Anthropic's official tokenizer if available."""
    if Anthropic is None:
        return len(text) // 4
    client = Anthropic()
    return client.count_tokens(text)


def gemini_tokens(text: str) -> int:
    """Count tokens using Google generative AI library if available."""
    if genai is None:
        return len(text) // 4
    info = genai.token_count(text)
    # google-generativeai returns a dict with 'token_count'
    return info.get("token_count", len(info.get("tokens", [])))



MODEL_DISPATCH = {
    "gpt": gpt_tokens,
    "claude": claude_tokens,
    "gemini": gemini_tokens,
}

_DEFAULT_MODEL = load_settings().get("token_model", "gpt")
_OVERRIDE_MODEL: str | None = None


def set_default_model(model: str | None) -> None:
    """Override default model used by :func:`estimate_token_count`."""
    global _OVERRIDE_MODEL
    _OVERRIDE_MODEL = model


def estimate_token_count(text: str, model: str | None = None) -> int:
    """Return number of tokens for the chosen model."""
    chosen_model = model or _OVERRIDE_MODEL or _DEFAULT_MODEL
    func = MODEL_DISPATCH.get(chosen_model)
    if func is None:
        raise ValueError(f"Modello sconosciuto: {chosen_model}")
    return func(text)

