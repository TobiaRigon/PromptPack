import os
import json
import re
from pathlib import Path
from datetime import datetime
from tempfile import NamedTemporaryFile
import webbrowser
import markdown

try:
    import weasyprint  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    weasyprint = None

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

PREVIEW_CSS_DARK = """
    <style>
    body {
        background-color: #1e1e1e;
        color: #d4d4d4;
        font-family: sans-serif;
        padding: 20px;
    }
    pre, code {
        background-color: #2d2d2d;
        color: #dcdcdc;
        font-family: monospace;
        padding: 5px;
        border-radius: 5px;
        overflow-x: auto;
        white-space: pre;
        word-break: normal;
        line-height: 1.4;
    }
    h2 {
        color: #569cd6;
    }
    </style>
"""

PREVIEW_CSS_LIGHT = """
    <style>
    body {
        background-color: #ffffff;
        color: #000000;
        font-family: sans-serif;
        padding: 20px;
    }
    pre, code {
        background-color: #f5f5f5;
        color: #000000;
        font-family: monospace;
        padding: 5px;
        border-radius: 5px;
        overflow-x: auto;
        white-space: pre;
        word-break: normal;
        line-height: 1.4;
    }
    h2 {
        color: #003366;
    }
    </style>
"""


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


def _init_export(start_folder: str, export_format: str):
    project_name = Path(start_folder).name
    date_str = datetime.now().strftime("%Y%m%d")
    if export_format == "json":
        header = ""
        container: list[str] | dict = {"project": project_name, "date": date_str, "files": []}
    else:
        header = f"Project: {project_name} - {date_str}\n\n"
        container = [header]
    tokens = estimate_token_count(header)
    return project_name, date_str, container, tokens


def _write_part(dest_folder: str, export_format: str, project_name: str, date_str: str, part: int, container, theme: str):
    if export_format == "json":
        output_file = Path(dest_folder) / f"{project_name}-{date_str}-part{part}.json"
        output_file.write_text(json.dumps(container, indent=2), encoding="utf-8")
    elif export_format in {"md", "txt", "html", "pdf"}:
        suffix = "md" if export_format == "md" else export_format
        output_file = Path(dest_folder) / f"{project_name}-{date_str}-part{part}.{suffix}"
        text = "".join(container)
        if export_format in {"html", "pdf"}:
            html = markdown.markdown(text, extensions=["fenced_code", "codehilite"])
            style = PREVIEW_CSS_DARK if theme == "dark" else PREVIEW_CSS_LIGHT
            html = f"<html><head>{style}</head><body>{html}</body></html>"
            if export_format == "pdf" and weasyprint is not None:
                weasyprint.HTML(string=html).write_pdf(str(output_file))
            else:
                output_file.write_text(html, encoding="utf-8")
        else:
            output_file.write_text(text, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported format: {export_format}")
    return output_file


def _add_block(container, export_format: str, block):
    if export_format == "json":
        container["files"].append(block)
    else:
        container.append(block)


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
    theme: str = "light",
):
    """Export selected files in the chosen format."""

    project_name, date_str, container, token_count = _init_export(start_folder, export_format if export_format not in {"html", "pdf"} else "md")

    part = 1
    output_files = []

    total_files = len(included_files)
    processed = 0

    for path in included_files:
        rel_path = path.relative_to(start_folder)
        if tree_only:
            line = rel_path.as_posix() + "\n"
            block_tokens = estimate_token_count(line)
            if token_count + block_tokens > max_tokens:
                output_files.append(_write_part(dest_folder, export_format, project_name, date_str, part, container, theme))
                part += 1
                container = _init_export(start_folder, export_format if export_format not in {"html", "pdf"} else "md")[2]
                token_count = estimate_token_count(container[0] if isinstance(container, list) else "")
            if export_format == "json":
                _add_block(container, export_format, {"path": rel_path.as_posix()})
            else:
                _add_block(container, export_format, line)
            token_count += block_tokens
            processed += 1
            if progress_callback:
                progress_callback(processed, total_files)
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        content = sanitize_sensitive_data(content)

        if export_format == "json":
            block_tokens = estimate_token_count(content)
            if token_count + block_tokens > max_tokens:
                output_files.append(_write_part(dest_folder, export_format, project_name, date_str, part, container, theme))
                part += 1
                container = _init_export(start_folder, export_format)[2]
                token_count = estimate_token_count("")
            _add_block(container, export_format, {"path": rel_path.as_posix(), "content": content})
            token_count += block_tokens
        else:
            block_lines = []
            if include_heading:
                block_lines.append(f"## {rel_path.as_posix()}\n")
            if use_code_block:
                lang = LANG_MAP.get(path.suffix, "")
                block_lines.append(f"```{lang}\n{content}\n```\n\n")
            else:
                block_lines.append(f"{content}\n\n")
            block = "".join(block_lines)
            block_tokens = estimate_token_count(block)
            if token_count + block_tokens > max_tokens:
                output_files.append(_write_part(dest_folder, export_format, project_name, date_str, part, container, theme))
                part += 1
                container = _init_export(start_folder, export_format if export_format not in {"html", "pdf"} else "md")[2]
                token_count = estimate_token_count(container[0] if isinstance(container, list) else "")
            _add_block(container, export_format, block)
            token_count += block_tokens

        processed += 1
        if progress_callback:
            progress_callback(processed, total_files)

    output_files.append(_write_part(dest_folder, export_format, project_name, date_str, part, container, theme))
    return output_files

