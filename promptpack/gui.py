import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Toplevel, ttk
from pathlib import Path
from datetime import datetime
from tempfile import NamedTemporaryFile
import webbrowser
import markdown

from .settings import load_settings, save_settings
from pathspec import PathSpec
from .utils import apply_icon, estimate_token_count, LANG_MAP, generate_output, sanitize_sensitive_data
from .i18n import load_translations, available_languages

EN_TRANSLATIONS = load_translations("eng")



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
        if self.theme.get() == "dark":
            palette = {
                "background": "#2d2d2d",
                "foreground": "#dcdcdc",
                "activeBackground": "#505050",
                "activeForeground": "#ffffff",
            }
        else:
            palette = {
                "background": "#ffffff",
                "foreground": "#000000",
                "activeBackground": "#e0e0e0",
                "activeForeground": "#000000",
            }

        self.root.configure(bg=palette["background"])
        self.root.tk_setPalette(**palette)
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Heading.TLabel", font=("TkDefaultFont", 15, "bold"))
        style.configure(
            ".",
            background=palette["background"],
            foreground=palette["foreground"],
        )
        style.configure(
            "TButton",
            background=palette["background"],
            foreground=palette["foreground"],
        )
        style.map(
            "TButton",
            background=[("active", palette["activeBackground"])],
            foreground=[("active", palette["activeForeground"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=palette["background"],
            background=palette["background"],
            foreground=palette["foreground"],
            insertcolor=palette["foreground"],
        )
        style.configure(
            "TLabel",
            background=palette["background"],
            foreground=palette["foreground"],
        )
        style.configure(
        "TCheckbutton",
        background=palette["background"],
        foreground=palette["foreground"],
        )
        style.configure(
            "Gear.TButton",
            relief="flat",
            borderwidth=0,
            background=palette["background"],
            foreground=palette["foreground"],
            padding=2,
        )
        style.map("Gear.TButton", background=[], foreground=[])

        style.map("TCheckbutton", background=[], foreground=[])
        style.configure(
            "TRadiobutton",
            background=palette["background"],
            foreground=palette["foreground"],
        )
        style.map("TRadiobutton", background=[], foreground=[])
        style.configure(
            "TMenubutton",
            background=palette["background"],
            foreground=palette["foreground"],
        )
        style.map("TMenubutton", background=[], foreground=[])

        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.tk_setPalette(**palette)
            if self.preview_text:
                self.preview_text.configure(bg=palette["background"], fg=palette["foreground"])

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
        win = Toplevel(self.root)
        win.title(self.t("settings_title"))
        apply_icon(win)
        win.geometry("500x500")

        style = ttk.Style(win)
        style.configure("Heading.TLabel", font=("TkDefaultFont", 15, "bold"))


        def prompt_list(title, key):
            dlg = ListDialog(win, title, initial_value=",".join(self.settings[key]))
            result = dlg.result
            if result is not None:
                self.settings[key] = [x.strip() for x in result.split(",") if x.strip()]
        ttk.Label(win, text=self.t("default_selection"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
        ttk.Button(win, text=self.t("allowed_exts"), command=lambda: prompt_list(self.t("allowed_exts"), "allowed_exts")).pack(pady=5)
        ttk.Button(win, text=self.t("excluded_dirs"), command=lambda: prompt_list(self.t("excluded_dirs"), "excluded_dirs")).pack(pady=5)
        ttk.Button(win, text=self.t("excluded_files"), command=lambda: prompt_list(self.t("excluded_files"), "excluded_files")).pack(pady=5)

        ttk.Label(win, text=self.t("output_opts"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
        ttk.Label(win, text=self.t("export_format")).pack(pady=(5, 0))
        ttk.Radiobutton(win, text="TXT", variable=self.export_format, value="txt").pack(pady=2)
        ttk.Radiobutton(win, text="Markdown", variable=self.export_format, value="md").pack(pady=2)
        ttk.Radiobutton(win, text="JSON", variable=self.export_format, value="json").pack(pady=2)
        ttk.Checkbutton(win, text=self.t("include_headings"), variable=self.include_heading).pack(pady=5)
        ttk.Checkbutton(win, text=self.t("use_code"), variable=self.use_code_block).pack(pady=5)
        ttk.Checkbutton(win, text=self.t("tree_only"), variable=self.tree_only).pack(pady=5)

        ttk.Label(win, text=self.t("token_limit"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
        preset_limits = {
            "ChatGPT (16k)": 16000,
            "Gemini (32k)": 32000,
            "ChatGPT-4 Turbo (128k)": 128000,
            "Claude 3 (200k)": 200000,
        }
        preset_names = list(preset_limits.keys()) + ["Custom"]
        current_tokens = self.settings.get("max_tokens", 200000)
        preset_label = "Custom"
        for name, val in preset_limits.items():
            if val == current_tokens:
                preset_label = name
                break
        self.max_tokens_choice = tk.StringVar(value=preset_label)
        self.custom_max_tokens = tk.IntVar(value=current_tokens)
        token_frame = ttk.Frame(win)
        token_frame.pack(pady=5)
        token_menu = ttk.OptionMenu(token_frame, self.max_tokens_choice, preset_label, *preset_names, command=lambda *_: toggle_entry())
        token_menu.pack()
        # remove hover highlight from dropdown menu
        menu_widget = token_menu["menu"]
        bg = "#2d2d2d" if self.theme.get() == "dark" else "#ffffff"
        fg = "#dcdcdc" if self.theme.get() == "dark" else "#000000"
        menu_widget.configure(bg=bg, fg=fg, activebackground=bg, activeforeground=fg)

        token_entry = ttk.Entry(token_frame, textvariable=self.custom_max_tokens)
        if self.max_tokens_choice.get() == "Custom":
            token_entry.pack(pady=5)

        def toggle_entry(*_):
            if self.max_tokens_choice.get() == "Custom":
                token_entry.pack(pady=5)
            else:
                token_entry.pack_forget()


        ttk.Label(win, text=self.t("theme"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
        ttk.Radiobutton(win, text=self.t("light"), variable=self.theme, value="light", command=self.apply_theme).pack(pady=5)
        ttk.Radiobutton(win, text=self.t("dark"), variable=self.theme, value="dark", command=self.apply_theme).pack(pady=5)

        ttk.Label(win, text=self.t("language"), style="Heading.TLabel").pack(padx=10, pady=(20, 5))
        language_options = available_languages()
        ttk.OptionMenu(win, self.language, self.language.get(), *language_options, command=lambda *_: None).pack(pady=5)

        def save_and_close():
            new_settings = {
                **self.settings,
                "export_format": self.export_format.get(),
                "tree_only": self.tree_only.get(),
                "include_heading": self.include_heading.get(),
                "use_code_block": self.use_code_block.get(),
                "theme": self.theme.get(),
                "language": self.language.get(),
                "max_tokens": preset_limits.get(self.max_tokens_choice.get(), self.custom_max_tokens.get()),
            }
            save_settings(new_settings)
            self.settings = new_settings
            self.apply_theme()
            self.load_translations()
            self.update_texts()
            win.destroy()

        ttk.Button(win, text=self.t("save"), command=save_and_close).pack(pady=10)

    def is_valid(self, f: Path) -> bool:
        return f.suffix in self.settings["allowed_exts"] and f.name not in self.settings["excluded_files"]

    def update_default_selected_files(self, folder_path: Path):
        gitignore_file = folder_path / ".gitignore"
        if gitignore_file.exists():
            with gitignore_file.open("r", encoding="utf-8") as f:
                self.gitignore_spec = PathSpec.from_lines("gitwildmatch", f)
        else:
            self.gitignore_spec = None

        all_files = folder_path.rglob("*")
        spec = self.gitignore_spec
        self.selected_files = {
            f
            for f in all_files
            if f.is_file()
            and self.is_valid(f)
            and not any(excl in f.parts for excl in self.settings["excluded_dirs"])
            and not (spec and spec.match_file(str(f.relative_to(folder_path))))
        }

    def toggle_preview_window(self):
        if self.enable_preview.get():
            preview_text = self.get_preview_text(self.selected_files)
            if self.preview_window is None or not self.preview_window.winfo_exists():
                self.preview_window = Toplevel(self.root)
                self.preview_window.title(self.t("preview"))
                apply_icon(self.preview_window)
                self.preview_text = tk.Text(self.preview_window, wrap="word")
                self.preview_text.pack(fill="both", expand=True)
                ttk.Button(
                    self.preview_window,
                    text=self.t("copy"),
                    command=lambda: self.copy_text_widget(self.preview_text),
                ).pack(pady=5)
                self.apply_theme()
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", preview_text)
        else:
            if self.preview_window and self.preview_window.winfo_exists():
                self.preview_window.destroy()
                self.preview_window = None

    def preview_in_browser(self):
        if not self.selected_files:
            messagebox.showwarning(self.t("no_files"), self.t("no_preview"))
            return
        markdown_text = self.get_preview_text(self.selected_files)
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

        css = dark_css if self.theme.get() == "dark" else light_css

        html = f"<html><head>{css}</head><body>{html_body}</body></html>"
        with NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as tmp:
            tmp.write(html)
            webbrowser.open(f"file://{tmp.name}")

    def copy_text_widget(self, widget: tk.Text):
        text = widget.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo(self.t("copied"), self.t("content_copied"))

    def copy_preview(self):
        if not self.selected_files:
            messagebox.showwarning(self.t("no_files"), self.t("no_preview"))
            return
        text = self.get_preview_text(self.selected_files)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo(self.t("copied"), self.t("preview_copied"))

    def select_files(self):
        folder = self.start_folder.get()
        if not folder:
            messagebox.showerror(self.t("error"), self.t("select_source_first"))
            return

        selector = Toplevel(self.root)
        selector.title(self.t("select_files_title"))
        apply_icon(selector)
        selector.geometry("850x500")
        palette = {
            "background": "#2d2d2d",
            "foreground": "#dcdcdc",
        } if self.theme.get() == "dark" else {
            "background": "#ffffff",
            "foreground": "#000000",
        }
        selector.configure(bg=palette["background"])
        selector.tk_setPalette(**palette)
        style = ttk.Style(selector)
        style.theme_use("clam")
        style.configure(
            ".",
            background=palette["background"],
            foreground=palette["foreground"],
        )
        style.configure(
            "Treeview",
            background=palette["background"],
            fieldbackground=palette["background"],
            foreground=palette["foreground"],
        )

        tree = ttk.Treeview(selector, columns=("fullpath", "type"))
        tree.heading("#0", text="Name")
        tree.heading("type", text="Type")
        tree.column("fullpath", width=0, stretch=False)
        tree.column("type", width=80)
        tree.pack(fill=tk.BOTH, expand=True)

        token_label = ttk.Label(selector, text="")
        token_label.pack(pady=2)

        checkbox_vars = {}
        checkbox_items = {}
        all_state = tk.BooleanVar(value=False)

        def update_token_label():
            tokens = self.compute_token_count({Path(p) for p, var in checkbox_vars.items() if var.get()})
            max_tokens = self.settings.get("max_tokens", 200000)
            token_label.config(text=self.t("tokens", tokens=tokens, max=max_tokens))

        def insert_items(parent, path: Path):
            for p in sorted(path.iterdir()):
                if p.is_dir():
                    node = tree.insert(parent, 'end', text=p.name, values=(str(p), "dir"), open=False)
                    insert_items(node, p)
                else:
                    default_checked = (
                        self.is_valid(p)
                        and not any(skip in p.parts for skip in self.settings["excluded_dirs"])
                        and not (
                            self.gitignore_spec
                            and self.gitignore_spec.match_file(str(p.relative_to(folder)))
                        )
                    )
                    checked = p in self.selected_files or default_checked
                    var = tk.BooleanVar(value=checked)
                    item = tree.insert(parent, 'end', text=f"[{'x' if var.get() else ' '}] {p.name}", values=(str(p), "file"))
                    checkbox_vars[str(p)] = var
                    checkbox_items[str(p)] = item

        insert_items('', Path(folder))
        update_token_label()

        def update_preview_live():
            if self.enable_preview.get():
                preview_text = self.get_preview_text({Path(p) for p, var in checkbox_vars.items() if var.get()})
                if self.preview_window is None or not self.preview_window.winfo_exists():
                    self.preview_window = Toplevel(self.root)
                    self.preview_window.title(self.t("preview"))
                    apply_icon(self.preview_window)
                    self.preview_text = tk.Text(self.preview_window, wrap="word")
                    self.preview_text.pack(fill="both", expand=True)
                    self.apply_theme()
                self.preview_text.delete("1.0", "end")
                self.preview_text.insert("1.0", preview_text)
            update_token_label()

        def toggle_checkbox(event):
            item = tree.identify_row(event.y)
            if not item:
                return
            values = tree.item(item, 'values')
            if len(values) < 2:
                return
            path_str, typ = values
            if typ == "file" and path_str in checkbox_vars:
                var = checkbox_vars[path_str]
                var.set(not var.get())
                new_label = f"[{'x' if var.get() else ' '}] {Path(path_str).name}"
                tree.item(item, text=new_label)
                update_preview_live()
                update_token_label()

        tree.bind("<Button-1>", toggle_checkbox)

        def toggle_all():
            new_val = not all_state.get()
            all_state.set(new_val)
            for path_str, var in checkbox_vars.items():
                var.set(new_val)
                item = checkbox_items[path_str]
                tree.item(item, text=f"[{'x' if new_val else ' '}] {Path(path_str).name}")
            update_preview_live()
            update_token_label()

        ttk.Button(selector, text=self.t("select_deselect"), command=toggle_all).pack(pady=5)

        def confirm_selection():
            self.selected_files = {Path(p) for p, var in checkbox_vars.items() if var.get()}
            self.settings["last_start_folder"] = self.start_folder.get()
            self.settings["last_selected_files"] = [
                str(Path(p).relative_to(self.start_folder.get()))
                for p, var in checkbox_vars.items() if var.get()
            ]
            save_settings(self.settings)
            selector.destroy()
            if self.preview_window and self.preview_window.winfo_exists():
                self.preview_window.destroy()

        ttk.Button(
            selector,
            text=self.t("confirm"),
            command=confirm_selection,
        ).pack(pady=5)

    def compute_token_count(self, included_files):
        preview_lines = self.generate_preview_lines(self.start_folder.get(), included_files)
        full_text = "\n".join(preview_lines)
        return estimate_token_count(full_text)

    def get_preview_text(self, included_files):
        preview_lines = self.generate_preview_lines(self.start_folder.get(), included_files)
        full_text = "\n".join(preview_lines)
        token_count = estimate_token_count(full_text)
        max_tokens = self.settings.get("max_tokens", 200000)
        remaining = max_tokens - token_count
        header = self.t("token_header", count=token_count, remaining=remaining, sep="="*40)
        return header + full_text

    def generate_preview_lines(self, start_folder, included_files):
        lines = []
        project_name = Path(start_folder).name
        date_str = datetime.now().strftime('%Y%m%d')
        header = self.t("project_label", name=project_name, date=date_str) + "\n"
        lines.append(header)
        token_count = estimate_token_count(header)
        max_tokens = self.settings.get("max_tokens", 200000)

        for path in sorted(included_files):
            rel_path = path.relative_to(start_folder)
            if self.tree_only.get():
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
            if self.include_heading.get():
                chunk.append(f"## {rel_path.as_posix()}\n")
            if self.export_format.get() == "md" and self.use_code_block.get():
                lang = LANG_MAP.get(path.suffix, '')
                chunk.append(f"```{lang}\n{content}\n```\n")
            else:
                chunk.append(f"{content}\n")
            text = ''.join(chunk)
            tokens = estimate_token_count(text)
            if token_count + tokens > max_tokens:
                messagebox.showwarning(
                    self.t("limit_reached"),
                    self.t("limit_msg", max=max_tokens),
                )
                break
            lines.extend(chunk)
            token_count += tokens
        return lines

    def generate(self):
        if not self.start_folder.get() or not self.dest_folder.get():
            messagebox.showerror(self.t("error"), self.t("need_folders"))
            return
        if not self.selected_files:
            messagebox.showerror(self.t("error"), self.t("no_selected"))
            return
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
            )
            msg = "\n".join(str(p) for p in output_paths)
            messagebox.showinfo(self.t("done"), self.t("files_generated", msg=msg))
        except Exception as e:
            messagebox.showerror(self.t("error"), str(e))
