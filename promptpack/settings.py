import json
import os
from pathlib import Path

SETTINGS_FILE = "promptpack_settings.json"

DEFAULT_SETTINGS = {
    "allowed_exts": [".php", ".js", ".ts", ".html", ".css", ".py"],
    "excluded_dirs": ["vendor", ".git", "node_modules"],
    "excluded_files": [".env", "README.md"],
    "export_format": "md",  # options: txt, md, json
    # If True, export only the file tree without contents
    "tree_only": False,
    "include_heading": True,
    "use_code_block": True,
    "theme": "dark",
    "language": "eng",
    "token_model": "gpt",
    # Maximum tokens per preview or export file
    "max_tokens": 200_000,
    # Disable live preview for files bigger than this size (bytes)
    "preview_size_limit": 1_000_000,
    # Remember last source folder and selected files
    "last_start_folder": "",
    "last_selected_files": [],
}


def load_settings():
    if Path(SETTINGS_FILE).exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "export_format" not in data:
                    # migrate from previous version using boolean as_markdown
                    data["export_format"] = "md" if data.get("as_markdown", True) else "txt"
                if "tree_only" not in data:
                    data["tree_only"] = DEFAULT_SETTINGS["tree_only"]
                if "last_start_folder" not in data:
                    data["last_start_folder"] = DEFAULT_SETTINGS["last_start_folder"]
                if "last_selected_files" not in data:
                    data["last_selected_files"] = DEFAULT_SETTINGS["last_selected_files"]
                if "language" not in data:
                    data["language"] = DEFAULT_SETTINGS["language"]
                if "token_model" not in data:
                    data["token_model"] = DEFAULT_SETTINGS["token_model"]
                if "preview_size_limit" not in data:
                    data["preview_size_limit"] = DEFAULT_SETTINGS["preview_size_limit"]
                return {**DEFAULT_SETTINGS, **data}
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

