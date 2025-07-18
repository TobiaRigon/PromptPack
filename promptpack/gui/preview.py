import threading
import markdown
from pathlib import Path
from tempfile import NamedTemporaryFile
import webbrowser
import tkinter as tk
from tkinter import Toplevel, messagebox, ttk
from datetime import datetime

from ..utils import apply_icon, sanitize_sensitive_data, LANG_MAP, estimate_token_count


def build_preview_async(app, files):
    app.show_progress(app.t("preview"))

    def worker():
        text = app.get_preview_text(files)

        def update():
            if app.preview_window is None or not app.preview_window.winfo_exists():
                app.preview_window = Toplevel(app.root)
                app.preview_window.title(app.t("preview"))
                app.preview_window.resizable(True, True)
                apply_icon(app.preview_window)

                frame = ttk.Frame(app.preview_window)
                frame.pack(fill="both", expand=True)

                app.preview_text = tk.Text(frame, wrap="word")
                yscroll = ttk.Scrollbar(frame, command=app.preview_text.yview)
                app.preview_text.configure(yscrollcommand=yscroll.set)
                app.preview_text.pack(side="left", fill="both", expand=True)
                yscroll.pack(side="right", fill="y")

                ttk.Button(
                    app.preview_window,
                    text=app.t("copy"),
                    command=lambda: copy_text_widget(app, app.preview_text),
                ).pack(pady=5)
                app.apply_theme()
            app.preview_text.delete("1.0", "end")
            app.preview_text.insert("1.0", text)
            app.hide_progress()

        app.root.after(0, update)

    threading.Thread(target=worker, daemon=True).start()


def toggle_preview_window(app):
    if app.enable_preview.get():
        build_preview_async(app, app.selected_files)
    else:
        if app.preview_window and app.preview_window.winfo_exists():
            app.preview_window.destroy()
            app.preview_window = None


def preview_in_browser(app):
    if not app.selected_files:
        messagebox.showwarning(app.t("no_files"), app.t("no_preview"))
        return
    markdown_text = app.get_preview_text(app.selected_files)
    html_body = markdown.markdown(markdown_text, extensions=['fenced_code', 'codehilite'])

    dark_css = """
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

    light_css = """
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

    css = dark_css if app.theme.get() == "dark" else light_css

    html = f"<html><head>{css}</head><body>{html_body}</body></html>"
    with NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as tmp:
        tmp.write(html)
        webbrowser.open(f"file://{tmp.name}")


def copy_text_widget(app, widget: tk.Text):
    text = widget.get("1.0", "end-1c")
    app.root.clipboard_clear()
    app.root.clipboard_append(text)
    app.root.update()
    messagebox.showinfo(app.t("copied"), app.t("content_copied"))


def copy_preview(app):
    if not app.selected_files:
        messagebox.showwarning(app.t("no_files"), app.t("no_preview"))
        return
    text = app.get_preview_text(app.selected_files)
    app.root.clipboard_clear()
    app.root.clipboard_append(text)
    app.root.update()
    messagebox.showinfo(app.t("copied"), app.t("preview_copied"))


def compute_token_count(app, included_files):
    preview_lines = generate_preview_lines(app, app.start_folder.get(), included_files, warn_on_limit=False)
    full_text = "\n".join(preview_lines)
    return estimate_token_count(full_text)


def get_preview_text(app, included_files):
    app.limit_warning_displayed = False
    preview_lines = generate_preview_lines(app, app.start_folder.get(), included_files, warn_on_limit=True)
    full_text = "\n".join(preview_lines)
    token_count = estimate_token_count(full_text)
    max_tokens = app.settings.get("max_tokens", 200000)
    remaining = max_tokens - token_count
    header = app.t("token_header", count=token_count, remaining=remaining, sep="="*40)
    return header + full_text


def generate_preview_lines(app, start_folder, included_files, warn_on_limit=True):
    lines = []
    project_name = Path(start_folder).name
    date_str = datetime.now().strftime('%Y%m%d')
    header = app.t("project_label", name=project_name, date=date_str) + "\n"
    lines.append(header)
    token_count = estimate_token_count(header)
    max_tokens = app.settings.get("max_tokens", 200000)

    for path in sorted(included_files):
        rel_path = path.relative_to(start_folder)
        if app.tree_only.get():
            line = f"{rel_path.as_posix()}\n"
            tokens = estimate_token_count(line)
            if token_count + tokens > max_tokens:
                break
            lines.append(line)
            token_count += tokens
            continue
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        content = sanitize_sensitive_data(content)
        chunk = []
        if app.include_heading.get():
            chunk.append(f"## {rel_path.as_posix()}\n")
        if app.export_format.get() == "md" and app.use_code_block.get():
            lang = LANG_MAP.get(path.suffix, '')
            chunk.append(f"```{lang}\n{content}\n```\n")
        else:
            chunk.append(f"{content}\n")
        text = ''.join(chunk)
        tokens = estimate_token_count(text)
        if token_count + tokens > max_tokens:
            if warn_on_limit and not app.limit_warning_displayed:
                messagebox.showwarning(
                    app.t("limit_reached"),
                    app.t("limit_msg", max=max_tokens),
                )
                app.limit_warning_displayed = True
            break
        lines.extend(chunk)
        token_count += tokens
    return lines

