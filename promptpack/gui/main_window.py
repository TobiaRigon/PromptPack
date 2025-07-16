import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Toplevel, ttk
from pathlib import Path
from datetime import datetime
from tempfile import NamedTemporaryFile
import webbrowser
import markdown
import threading

from ..settings import load_settings, save_settings
from pathspec import PathSpec
from ..utils import apply_icon, estimate_token_count, LANG_MAP, generate_output, sanitize_sensitive_data
from ..i18n import load_translations, available_languages
from .theme import apply_theme
from .progress import show_progress, update_progress, hide_progress
from .preview import (
    build_preview_async,
    preview_in_browser,
    copy_preview,
    copy_text_widget,
    compute_token_count,
    get_preview_text,
    generate_preview_lines,
        toggle_preview_window,

)
from .file_selector import (
    select_files,
    is_valid,
    update_default_selected_files,
)
from .settings_dialog import configure_settings, ListDialog


class Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        label = ttk.Label(tw, text=self.text, relief="solid", borderwidth=1, background="#ffffe0")
        label.pack()

    def hide(self, _event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

EN_TRANSLATIONS = load_translations("eng")





class PromptPackApp:
    def load_translations(self):
        self.translations = load_translations(self.language.get())

    def t(self, key: str, **kwargs) -> str:
        template = self.translations.get(key, EN_TRANSLATIONS.get(key, key))
        return template.format(**kwargs)

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("PromptPack")
        apply_icon(root)


        self.settings = load_settings()

        self.export_format = tk.StringVar(value=self.settings.get("export_format", "md"))
        self.tree_only = tk.BooleanVar(value=self.settings.get("tree_only", False))
        self.include_heading = tk.BooleanVar(value=self.settings["include_heading"])
        self.use_code_block = tk.BooleanVar(value=self.settings["use_code_block"])
        self.theme = tk.StringVar(value=self.settings.get("theme", "dark"))
        self.language = tk.StringVar(value=self.settings.get("language", "eng"))
        self.load_translations()
        self.enable_preview = tk.BooleanVar(value=False)

        self.start_folder = tk.StringVar(value=self.settings.get("last_start_folder", ""))
        self.dest_folder = tk.StringVar()
        self.selected_files = set()
        self.gitignore_spec = None

        self.preview_window = None
        self.preview_text = None
        self.progress_frame = None
        self.progress_bar = None
        self.progress_var = tk.IntVar(value=0)
        self.limit_warning_displayed = False

        style = ttk.Style(self.root)
        style.configure("Heading.TLabel", font=("TkDefaultFont", 15, "bold"))

        self.build_gui()
        self.update_texts()

        folder = self.start_folder.get()
        if folder:
            self.update_default_selected_files(Path(folder))
            saved = {
                Path(folder) / Path(p)
                for p in self.settings.get("last_selected_files", [])
            }
            saved_existing = {p for p in saved if p.exists()}
            if saved_existing:
                self.selected_files = saved_existing

        self.apply_theme()

    def build_gui(self):
        # Rende le 3 colonne espandibili per migliore distribuzione
        for i in range(3):
            self.root.grid_columnconfigure(i, weight=1)

        heading_opts = {
            "style": "Heading.TLabel",
            "anchor": "center"
        }

        # Source section
        self.source_heading = ttk.Label(self.root, text=self.t("source"), **heading_opts)
        self.source_heading.grid(row=0, column=1, sticky="ew", padx=10, pady=(20, 5))

        self.source_label = ttk.Label(self.root, text=self.t("source_folder"))
        self.source_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        entry = ttk.Entry(self.root, textvariable=self.start_folder, width=50)
        entry.grid(row=1, column=1, padx=5, pady=5)

        self.browse_start_btn = ttk.Button(self.root, text=self.t("browse"), command=self.browse_start)
        self.browse_start_btn.grid(row=1, column=2, padx=5, pady=5)

        self.select_files_btn = ttk.Button(self.root, text=self.t("select_files"), command=self.select_files)
        self.select_files_btn.grid(row=2, column=1, pady=5)

        # Preview section
        self.preview_heading = ttk.Label(self.root, text=self.t("preview"), **heading_opts)
        self.preview_heading.grid(row=3, column=1, sticky="ew", padx=10, pady=(20, 5))

        self.browser_btn = ttk.Button(self.root, text=self.t("browser"), command=self.preview_in_browser)
        self.browser_btn.grid(row=4, column=1, pady=5)
        Tooltip(self.browser_btn, self.t("open_browser_tip"))

        self.live_preview_cb = ttk.Checkbutton(
            self.root,
            text=self.t("live_preview"),
            variable=self.enable_preview,
            command=self.toggle_preview_window,
        )
        self.live_preview_cb.grid(row=4, column=2, sticky="w", padx=5)

        # Output section
        self.output_heading = ttk.Label(self.root, text=self.t("output"), **heading_opts)
        self.output_heading.grid(row=5, column=1, sticky="ew", padx=10, pady=(20, 5))

        self.dest_label = ttk.Label(self.root, text=self.t("dest_folder"))
        self.dest_label.grid(row=6, column=0, sticky="w", padx=10, pady=5)

        ttk.Entry(self.root, textvariable=self.dest_folder, width=50)\
            .grid(row=6, column=1, padx=5, pady=5)

        self.browse_dest_btn = ttk.Button(self.root, text=self.t("browse"), command=self.browse_dest)
        self.browse_dest_btn.grid(row=6, column=2, padx=5, pady=5)

        self.generate_btn = ttk.Button(self.root, text=self.t("generate"), command=self.generate)
        self.generate_btn.grid(row=7, column=1, pady=10)

        # Settings gear button
        self.gear_button = ttk.Button(
            self.root,
            text=self.t("settings"),
            command=self.configure_settings,
            style="Gear.TButton"
        )
        self.gear_button.grid(row=8, column=2, sticky="e", pady=5, padx=5)
        self.gear_button.bind("<Enter>", lambda e: self.gear_button.config(cursor="hand2"))
        self.gear_button.bind("<Leave>", lambda e: self.gear_button.config(cursor=""))
        Tooltip(self.gear_button, self.t("settings_tip"))

    def update_texts(self):
        self.source_heading.config(text=self.t("source"))
        self.source_label.config(text=self.t("source_folder"))
        self.browse_start_btn.config(text=self.t("browse"))
        self.select_files_btn.config(text=self.t("select_files"))
        self.preview_heading.config(text=self.t("preview"))
        self.browser_btn.config(text=self.t("browser"))
        self.live_preview_cb.config(text=self.t("live_preview"))
        self.output_heading.config(text=self.t("output"))
        self.dest_label.config(text=self.t("dest_folder"))
        self.browse_dest_btn.config(text=self.t("browse"))
        self.generate_btn.config(text=self.t("generate"))
        self.gear_button.config(text=self.t("settings"))




    def apply_theme(self):
        apply_theme(self)

    def show_progress(self, message: str, maximum: int | None = None):
        show_progress(self, message, maximum)

    def update_progress(self, value: int, maximum: int):
        update_progress(self, value, maximum)

    def hide_progress(self):
        hide_progress(self)

    def build_preview_async(self, files):
        build_preview_async(self, files)

    def browse_start(self):
        folder = filedialog.askdirectory()
        if folder:
            self.start_folder.set(folder)
            self.update_default_selected_files(Path(folder))
            self.settings["last_start_folder"] = folder
            self.settings["last_selected_files"] = []
            save_settings(self.settings)


    def browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder.set(folder)

    def configure_settings(self):
        configure_settings(self)

    def is_valid(self, f: Path) -> bool:
        return is_valid(self, f)

    def update_default_selected_files(self, folder_path: Path):
        update_default_selected_files(self, folder_path)

    def toggle_preview_window(self):
        toggle_preview_window(self)

    def preview_in_browser(self):
        preview_in_browser(self)

    def copy_text_widget(self, widget: tk.Text):
        copy_text_widget(self, widget)

    def copy_preview(self):
        copy_preview(self)

    def select_files(self):
        select_files(self)

    def compute_token_count(self, included_files):
        return compute_token_count(self, included_files)

    def get_preview_text(self, included_files):
        return get_preview_text(self, included_files)

    def generate_preview_lines(self, start_folder, included_files, warn_on_limit=True):
        return generate_preview_lines(self, start_folder, included_files, warn_on_limit)

    def generate(self):
        if not self.start_folder.get() or not self.dest_folder.get():
            messagebox.showerror(self.t("error"), self.t("need_folders"))
            return
        if not self.selected_files:
            messagebox.showerror(self.t("error"), self.t("no_selected"))
            return
        total = len(self.selected_files)
        self.show_progress(self.t("generate"), maximum=total)

        def callback(current, maximum):
            self.root.after(0, lambda: self.update_progress(current, maximum))

        def worker():
            try:
                output_paths = generate_output(
                    self.start_folder.get(),
                    self.dest_folder.get(),
                    list(self.selected_files),
                    self.export_format.get(),
                    self.tree_only.get(),
                    self.include_heading.get(),
                    self.use_code_block.get(),
                    self.settings.get("max_tokens", 200000),
                    progress_callback=callback,
                    theme=self.theme.get(),
                )
                msg = "\n".join(str(p) for p in output_paths)
                self.root.after(0, lambda: [self.hide_progress(), messagebox.showinfo(self.t("done"), self.t("files_generated", msg=msg))])
            except Exception as e:
                self.root.after(0, lambda: [self.hide_progress(), messagebox.showerror(self.t("error"), str(e))])

        threading.Thread(target=worker, daemon=True).start()
