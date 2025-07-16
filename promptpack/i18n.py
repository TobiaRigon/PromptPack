"""Utility per la gestione delle traduzioni."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "locales"

_cache: dict[str, dict[str, str]] = {}


def load_translations(lang: str) -> dict[str, str]:
    """Carica le stringhe localizzate dal file corrispondente."""
    if lang not in _cache:
        path = LOCALES_DIR / f"{lang}.json"
        if not path.exists():
            path = LOCALES_DIR / "eng.json"
        try:
            with path.open("r", encoding="utf-8") as f:
                _cache[lang] = json.load(f)
        except Exception:
            _cache[lang] = {}
    return _cache[lang]
