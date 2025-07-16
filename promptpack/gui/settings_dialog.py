import os
import sys
import tkinter as tk
from tkinter import Toplevel, ttk, simpledialog
from ..settings import save_settings
from ..utils import apply_icon
from ..i18n import available_languages


class ListDialog(simpledialog.Dialog):
    """Simple entry dialog that supports a custom window icon."""

    def __init__(self, parent, title, initial_value=""):
        self.initial_value = initial_value
        self.dialog_title = title
        super().__init__(parent, title)

    def body(self, master):
        apply_icon(self)
        ttk.Label(master, text=f"{self.dialog_title} (comma separated):").pack(padx=5, pady=5)
        self.entry = ttk.Entry(master, width=50)
        self.entry.pack(padx=5, pady=5)
        self.entry.insert(0, self.initial_value)
        return self.entry

    def apply(self):
        self.result = self.entry.get()


def configure_settings(app):
    win = Toplevel(app.root)
    win.title(app.t("settings_title"))
    apply_icon(win)
    win.resizable(True, True)

    container = ttk.Frame(win)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable, anchor="nw")

    scrollable.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # Scroll fix (cross-platform, sicuro)
    def _on_mousewheel(event):
        if event.widget.winfo_exists():
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_linux_scroll(event):
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

    def _bind_scroll_events(widget):
        if os.name == "nt" or sys.platform == "darwin":
            widget.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
            widget.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        else:
            widget.bind("<Enter>", lambda e: (
                canvas.bind_all("<Button-4>", _on_linux_scroll),
                canvas.bind_all("<Button-5>", _on_linux_scroll)
            ))
            widget.bind("<Leave>", lambda e: (
                canvas.unbind_all("<Button-4>"),
                canvas.unbind_all("<Button-5>")
            ))

    _bind_scroll_events(scrollable)

    style = ttk.Style(win)
    style.configure("Heading.TLabel", font=("TkDefaultFont", 15, "bold"))

    def prompt_list(title, key):
        dlg = ListDialog(win, title, initial_value=",".join(app.settings[key]))
        result = dlg.result
        if result is not None:
            app.settings[key] = [x.strip() for x in result.split(",") if x.strip()]

    ttk.Label(scrollable, text=app.t("default_selection"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
    ttk.Button(scrollable, text=app.t("allowed_exts"), command=lambda: prompt_list(app.t("allowed_exts"), "allowed_exts")).pack(pady=5)
    ttk.Button(scrollable, text=app.t("excluded_dirs"), command=lambda: prompt_list(app.t("excluded_dirs"), "excluded_dirs")).pack(pady=5)
    ttk.Button(scrollable, text=app.t("excluded_files"), command=lambda: prompt_list(app.t("excluded_files"), "excluded_files")).pack(pady=5)

    ttk.Label(scrollable, text=app.t("output_opts"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
    ttk.Label(scrollable, text=app.t("export_format")).pack(pady=(5, 0))
    format_combo = ttk.Combobox(
        scrollable,
        textvariable=app.export_format,
        values=["txt", "md", "html", "pdf", "json"],
        state="readonly",
    )
    format_combo.set(app.export_format.get())
    format_combo.pack(pady=5)
    ttk.Checkbutton(scrollable, text=app.t("include_headings"), variable=app.include_heading).pack(pady=5)
    ttk.Checkbutton(scrollable, text=app.t("use_code"), variable=app.use_code_block).pack(pady=5)
    ttk.Checkbutton(scrollable, text=app.t("tree_only"), variable=app.tree_only).pack(pady=5)

    ttk.Label(scrollable, text=app.t("token_limit"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
    preset_limits = {
        "ChatGPT (16k)": 16000,
        "Gemini (32k)": 32000,
        "ChatGPT-4 Turbo (128k)": 128000,
        "Claude 3 (200k)": 200000,
    }
    preset_names = list(preset_limits.keys()) + ["Custom"]
    current_tokens = app.settings.get("max_tokens", 200000)
    preset_label = "Custom"
    for name, val in preset_limits.items():
        if val == current_tokens:
            preset_label = name
            break
    app.max_tokens_choice = tk.StringVar(value=preset_label)
    app.custom_max_tokens = tk.IntVar(value=current_tokens)
    token_frame = ttk.Frame(scrollable)
    token_frame.pack(pady=5)
    token_menu = ttk.OptionMenu(token_frame, app.max_tokens_choice, preset_label, *preset_names, command=lambda *_: toggle_entry())
    token_menu.pack()

    menu_widget = token_menu["menu"]
    bg = "#2d2d2d" if app.theme.get() == "dark" else "#ffffff"
    fg = "#dcdcdc" if app.theme.get() == "dark" else "#000000"
    menu_widget.configure(bg=bg, fg=fg, activebackground=bg, activeforeground=fg)

    token_entry = ttk.Entry(token_frame, textvariable=app.custom_max_tokens)
    if app.max_tokens_choice.get() == "Custom":
        token_entry.pack(pady=5)

    def toggle_entry(*_):
        if app.max_tokens_choice.get() == "Custom":
            token_entry.pack(pady=5)
        else:
            token_entry.pack_forget()

    ttk.Label(scrollable, text=app.t("theme"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
    ttk.Radiobutton(scrollable, text=app.t("light"), variable=app.theme, value="light", command=app.apply_theme).pack(pady=5)
    ttk.Radiobutton(scrollable, text=app.t("dark"), variable=app.theme, value="dark", command=app.apply_theme).pack(pady=5)

    ttk.Label(scrollable, text=app.t("language"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
    language_options = available_languages()

    def on_language_change(*_):
        app.load_translations()
        app.update_texts()

    ttk.OptionMenu(scrollable, app.language, app.language.get(), *language_options, command=on_language_change).pack(pady=5)

    def save_and_close():
        new_settings = {
            **app.settings,
            "export_format": app.export_format.get(),
            "tree_only": app.tree_only.get(),
            "include_heading": app.include_heading.get(),
            "use_code_block": app.use_code_block.get(),
            "theme": app.theme.get(),
            "language": app.language.get(),
            "max_tokens": preset_limits.get(app.max_tokens_choice.get(), app.custom_max_tokens.get()),
        }
        save_settings(new_settings)
        app.settings = new_settings
        app.apply_theme()
        app.load_translations()
        app.update_texts()
        win.destroy()

    ttk.Button(scrollable, text=app.t("save"), command=save_and_close).pack(pady=10)
