import json
import os
from pathlib import Path

SETTINGS_FILE = "promptpack_settings.json"

DEFAULT_SETTINGS = {
    "allowed_exts": [".php", ".js", ".ts", ".html", ".css", ".py"],
    "excluded_dirs": ["vendor", ".git", "node_modules"],
    "excluded_files": [".env", "README.md"],
    "as_markdown": True,
    "include_heading": True,
    "use_code_block": True,
    "dark_mode": False,
}


def load_settings():
    if Path(SETTINGS_FILE).exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

