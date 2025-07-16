import os
import json
import re
from pathlib import Path
from datetime import datetime
from tempfile import NamedTemporaryFile
import webbrowser

from .tokenizer import estimate_token_count

LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".php": "php",
    ".html": "html",
    ".css": "css",
    ".sh": "bash",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".kt": "kotlin",
    ".swift": "swift",
    ".rb": "ruby",
    ".md": "markdown",
    ".txt": "",
    ".it": "",
    ".en": "",
}


def apply_icon(window):
    try:
        icon_path = "promptpack.ico"
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
    except Exception as e:
        print(f"Icon not loaded: {e}")




SENSITIVE_PATTERNS = [
    # common formats like API_KEY="value" or api-key: value
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)(['\"]?)([^'\"\s]+)(['\"]?)"),
    re.compile(r"(?i)(password\s*[:=]\s*)(['\"]?)([^'\"\s]+)(['\"]?)"),
    re.compile(r"(?i)(secret[_-]?key\s*[:=]\s*)(['\"]?)([^'\"\s]+)(['\"]?)"),
    re.compile(r"(?i)(token\s*[:=]\s*)(['\"]?)([^'\"\s]+)(['\"]?)"),
    re.compile(r"(?i)(authorization\s*[:=]\s*['\"]?Bearer\s+)([^'\"\s]+)"),
    re.compile(r"(?i)(bearer\s+)([A-Za-z0-9\-_.]+)"),
    re.compile(r"(?i)(aws_secret_access_key\s*[:=]\s*)(['\"]?)([^'\"\s]+)(['\"]?)"),
]


def sanitize_sensitive_data(text: str) -> str:
    """Mask common secrets such as passwords or API keys."""
    for pat in SENSITIVE_PATTERNS:
        text = pat.sub(lambda m: m.group(1) + m.group(2) + "***" + m.group(4), text)
    return text


def generate_output(
    start_folder: str,
    dest_folder: str,
    included_files,
    export_format: str,
    tree_only: bool,
    include_heading: bool,
    use_code_block: bool,
    max_tokens: int = 200000,
    progress_callback=None,
):
    """Export selected files in the chosen format.

    The output is split into multiple parts if the number of tokens exceeds
    ``max_tokens``. Each part is saved sequentially in the destination folder.
    """
    project_name = Path(start_folder).name
    date_str = datetime.now().strftime('%Y%m%d')
    token_count = 0
    part = 1
    output_files = []

    if export_format == "json":
        data = {"project": project_name, "date": date_str, "files": []}
        lines = []
        header = ""
        token_count = 0
    else:
        lines = []
        header = f"Project: {project_name} - {date_str}\n\n"
        lines.append(header)
        token_count = estimate_token_count(header)

    def _flush():
        nonlocal part, data, lines
        if export_format == "json":
            output_file = Path(dest_folder) / f"{project_name}-{date_str}-part{part}.json"
            output_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else:
            suffix = "md" if export_format == "md" else "txt"
            output_file = Path(dest_folder) / f"{project_name}-{date_str}-part{part}.{suffix}"
            output_file.write_text("".join(lines), encoding="utf-8")
        part += 1
        return output_file

    total_files = len(included_files)
    processed = 0
    for path in included_files:
        rel_path = path.relative_to(start_folder)
        if tree_only:
            if export_format == "json":
                line_data = {"path": rel_path.as_posix()}
                block_tokens = estimate_token_count(rel_path.as_posix())
                if token_count + block_tokens > max_tokens:
                    output_files.append(_flush())
                    token_count = estimate_token_count(header)
                    data = {"project": project_name, "date": date_str, "files": []}
                data["files"].append(line_data)
                token_count += block_tokens
            else:
                line = f"{rel_path.as_posix()}\n"
                block_tokens = estimate_token_count(line)
                if token_count + block_tokens > max_tokens:
                    output_files.append(_flush())
                    token_count = estimate_token_count(header)
                    lines = [header]
                lines.append(line)
                token_count += block_tokens
            processed += 1
            if progress_callback:
                progress_callback(processed, total_files)
            continue

        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        content = sanitize_sensitive_data(content)

        if export_format == "json":
            block_tokens = estimate_token_count(content)
            if token_count + block_tokens > max_tokens:
                output_files.append(_flush())
                token_count = estimate_token_count(header)
                data = {"project": project_name, "date": date_str, "files": []}
            data["files"].append({"path": rel_path.as_posix(), "content": content})
            token_count += block_tokens
        else:
            new_lines = []
            if include_heading:
                new_lines.append(f"## {rel_path.as_posix()}\n")
            if export_format == "md" and use_code_block:
                lang = LANG_MAP.get(path.suffix, '')
                new_lines.append(f"```{lang}\n{content}\n```\n\n")
            else:
                new_lines.append(f"{content}\n\n")
            block = ''.join(new_lines)
            block_tokens = estimate_token_count(block)
            if token_count + block_tokens > max_tokens:
                output_files.append(_flush())
                token_count = estimate_token_count(header)
                lines = [header]
            lines.append(block)
            token_count += block_tokens

        processed += 1
        if progress_callback:
            progress_callback(processed, total_files)

    output_files.append(_flush())
    return output_files

