import os
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
    as_markdown: bool,
    include_heading: bool,
    use_code_block: bool,
    max_tokens: int = 200000,
):
    lines = []
    project_name = Path(start_folder).name
    date_str = datetime.now().strftime('%Y%m%d')
    header = f"Project: {project_name} - {date_str}\n\n"
    lines.append(header)
    token_count = estimate_token_count(header)

    for path in included_files:
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        new_lines = []
        rel_path = path.relative_to(start_folder)
        if include_heading:
            new_lines.append(f"## {rel_path.as_posix()}\n")
        if as_markdown and use_code_block:
            lang = LANG_MAP.get(path.suffix, '')
            new_lines.append(f"```{lang}\n{content}\n```\n\n")
        else:
            new_lines.append(f"{content}\n\n")
        block = ''.join(new_lines)
        block_tokens = estimate_token_count(block)
        if token_count + block_tokens > max_tokens:
            break
        lines.append(block)
        token_count += block_tokens

    output_file = Path(dest_folder) / f"{project_name}-{date_str}.{ 'md' if as_markdown else 'txt' }"
    output_file.write_text(''.join(lines), encoding='utf-8')
    return output_file

