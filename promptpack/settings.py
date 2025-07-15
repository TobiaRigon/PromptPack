import json
import os
from pathlib import Path

SETTINGS_FILE = "promptpack_settings.json"

DEFAULT_SETTINGS = {
    "allowed_exts": [".php", ".js", ".ts", ".html", ".css", ".py"],
    "excluded_dirs": ["vendor", ".git", "node_modules"],
    "excluded_files": [".env", "README.md"],
    "export_format": "md",  # opzioni: txt, md, json
    "include_heading": True,
    "use_code_block": True,
    "theme": "dark",
    # Numero massimo di token da elaborare in anteprima o export
    "max_tokens": 200_000,
}


def load_settings():
    if Path(SETTINGS_FILE).exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "export_format" not in data:
                    # migrazione da versione precedente con as_markdown booleano
                    data["export_format"] = "md" if data.get("as_markdown", True) else "txt"
                return {**DEFAULT_SETTINGS, **data}
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

