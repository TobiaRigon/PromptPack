"""Utility functions for token counting with real tokenization models."""

from __future__ import annotations

try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    tiktoken = None

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


def estimate_token_count(text: str, model: str = "gpt") -> int:
    """Return number of tokens for the chosen model."""
    func = MODEL_DISPATCH.get(model)
    if func is None:
        raise ValueError(f"Modello sconosciuto: {model}")
    return func(text)

