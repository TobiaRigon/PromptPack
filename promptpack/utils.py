import os
import json
from pathlib import Path
from datetime import datetime
from tempfile import NamedTemporaryFile
import webbrowser
import markdown

LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".php": "php",
    ".html": "html",
    ".css": "css",
}


def apply_icon(window):
    try:
        icon_path = "promptpack.ico"
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
    except Exception as e:
        print(f"Icon not loaded: {e}")


def estimate_token_count(text: str) -> int:
    return int(len(text) / 4)


def generate_output(
    start_folder: str,
    dest_folder: str,
    included_files,
    export_format: str,
    tree_only: bool,
    include_heading: bool,
    use_code_block: bool,
    max_tokens: int = 200000,
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
            continue

        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

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

    output_files.append(_flush())
    return output_files

