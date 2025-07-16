"""Utility per la gestione delle traduzioni."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "locales"

_cache: dict[str, dict[str, str]] = {}


def load_translations(lang: str) -> dict[str, str]:
    """Carica le stringhe localizzate dal file corrispondente."""
    if lang not in _cache:
        # Always start from English strings as fallback
        data: dict[str, str] = {}
        try:
            with (LOCALES_DIR / "eng.json").open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        if lang != "eng":
            path = LOCALES_DIR / f"{lang}.json"
            if path.exists():
                try:
                    with path.open("r", encoding="utf-8") as f:
                        data.update(json.load(f))
                except Exception:
                    pass
        _cache[lang] = data
    return _cache[lang]


def available_languages() -> list[str]:
    """Ritorna l'elenco dei codici lingua disponibili."""
    return sorted(p.stem for p in LOCALES_DIR.glob("*.json"))
