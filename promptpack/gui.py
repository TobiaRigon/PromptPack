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
        self.enable_preview = tk.BooleanVar(value=False)

        self.start_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.selected_files = set()
        self.gitignore_spec = None

        self.preview_window = None
        self.preview_text = None

        style = ttk.Style(self.root)
        style.configure("Heading.TLabel", font=("TkDefaultFont", 15, "bold"))

        self.build_gui()
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
        ttk.Label(self.root, text="Source", **heading_opts)\
            .grid(row=0, column=1, sticky="ew", padx=10, pady=(20, 5))

        ttk.Label(self.root, text="Source Folder")\
            .grid(row=1, column=0, sticky="w", padx=10, pady=5)

        entry = ttk.Entry(self.root, textvariable=self.start_folder, width=50)
        entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.root, text="Browse", command=self.browse_start)\
            .grid(row=1, column=2, padx=5, pady=5)

        ttk.Button(self.root, text="Select Files", command=self.select_files)\
            .grid(row=2, column=1, pady=5)

        # Preview section
        ttk.Label(self.root, text="Preview", **heading_opts)\
            .grid(row=3, column=1, sticky="ew", padx=10, pady=(20, 5))

        ttk.Button(self.root, text="Copy to Clipboard", command=self.copy_preview)\
            .grid(row=4, column=0, pady=5)

        ttk.Button(self.root, text="Preview in browser", command=self.preview_in_browser)\
            .grid(row=4, column=1, pady=5)

        ttk.Checkbutton(
            self.root,
            text="Live Preview",
            variable=self.enable_preview,
            command=self.toggle_preview_window,
        ).grid(row=4, column=2, sticky="w", padx=5)

        # Output section
        ttk.Label(self.root, text="Output", **heading_opts)\
            .grid(row=5, column=1, sticky="ew", padx=10, pady=(20, 5))

        ttk.Label(self.root, text="Destination Folder")\
            .grid(row=6, column=0, sticky="w", padx=10, pady=5)

        ttk.Entry(self.root, textvariable=self.dest_folder, width=50)\
            .grid(row=6, column=1, padx=5, pady=5)

        ttk.Button(self.root, text="Browse", command=self.browse_dest)\
            .grid(row=6, column=2, padx=5, pady=5)

        ttk.Button(self.root, text="Generate", command=self.generate)\
            .grid(row=7, column=1, pady=10)

        # Settings gear button
        gear_button = ttk.Button(
            self.root,
            text="⚙️ Settings",
            command=self.configure_settings,
            style="Gear.TButton"
        )
        gear_button.grid(row=8, column=2, sticky="e", pady=5, padx=5)
        gear_button.bind("<Enter>", lambda e: gear_button.config(cursor="hand2"))
        gear_button.bind("<Leave>", lambda e: gear_button.config(cursor=""))




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


    def browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder.set(folder)

    def configure_settings(self):
        win = Toplevel(self.root)
        win.title("Settings")
        apply_icon(win)
        win.geometry("500x500")

        style = ttk.Style(win)
        style.configure("Heading.TLabel", font=("TkDefaultFont", 15, "bold"))


        def prompt_list(title, key):
            dlg = ListDialog(win, title, initial_value=",".join(self.settings[key]))
            result = dlg.result
            if result is not None:
                self.settings[key] = [x.strip() for x in result.split(",") if x.strip()]
        ttk.Label(win, text="Default Selection", style="Heading.TLabel").pack(padx=10, pady=(20, 5))
        ttk.Button(win, text="Default Allowed Extensions", command=lambda: prompt_list("Default Allowed Extensions", "allowed_exts")).pack(pady=5)
        ttk.Button(win, text="Default Excluded Directories", command=lambda: prompt_list("Default Excluded Directories", "excluded_dirs")).pack(pady=5)
        ttk.Button(win, text="Default Excluded Files", command=lambda: prompt_list("Default Excluded Files", "excluded_files")).pack(pady=5)

        ttk.Label(win, text="Output Options", style="Heading.TLabel").pack(padx=10, pady=(20, 5))
        ttk.Label(win, text="Export format:").pack(pady=(5, 0))
        ttk.Radiobutton(win, text="TXT", variable=self.export_format, value="txt").pack(pady=2)
        ttk.Radiobutton(win, text="Markdown", variable=self.export_format, value="md").pack(pady=2)
        ttk.Radiobutton(win, text="JSON", variable=self.export_format, value="json").pack(pady=2)
        ttk.Checkbutton(win, text="Include File Headings", variable=self.include_heading).pack(pady=5)
        ttk.Checkbutton(win, text="Use Code Blocks", variable=self.use_code_block).pack(pady=5)
        ttk.Checkbutton(win, text="Tree only", variable=self.tree_only).pack(pady=5)

        ttk.Label(win, text="Token limit", style="Heading.TLabel").pack(padx=10, pady=(20, 5))
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


        ttk.Label(win, text="Theme", style="Heading.TLabel").pack(padx=10, pady=(20, 5))
        ttk.Radiobutton(win, text="Light", variable=self.theme, value="light", command=self.apply_theme).pack(pady=5)
        ttk.Radiobutton(win, text="Dark", variable=self.theme, value="dark", command=self.apply_theme).pack(pady=5)

        def save_and_close():
            new_settings = {
                **self.settings,
                "export_format": self.export_format.get(),
                "tree_only": self.tree_only.get(),
                "include_heading": self.include_heading.get(),
                "use_code_block": self.use_code_block.get(),
                "theme": self.theme.get(),
                "max_tokens": preset_limits.get(self.max_tokens_choice.get(), self.custom_max_tokens.get()),
            }
            save_settings(new_settings)
            self.settings = new_settings
            self.apply_theme()
            win.destroy()

        ttk.Button(win, text="Save", command=save_and_close).pack(pady=10)

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
                self.preview_window.title("Preview")
                apply_icon(self.preview_window)
                self.preview_text = tk.Text(self.preview_window, wrap="word")
                self.preview_text.pack(fill="both", expand=True)
                ttk.Button(
                    self.preview_window,
                    text="Copy to Clipboard",
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
            messagebox.showwarning("No Files", "No files selected for preview.")
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
        messagebox.showinfo("Copied", "Content copied to clipboard")

    def copy_preview(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "No files selected for preview.")
            return
        text = self.get_preview_text(self.selected_files)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo("Copied", "Preview copied to clipboard")

    def select_files(self):
        folder = self.start_folder.get()
        if not folder:
            messagebox.showerror("Error", "Please select the source folder first")
            return

        selector = Toplevel(self.root)
        selector.title("Select Files to Include")
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
                    var = tk.BooleanVar(value=default_checked)
                    item = tree.insert(parent, 'end', text=f"[{'x' if var.get() else ' '}] {p.name}", values=(str(p), "file"))
                    checkbox_vars[str(p)] = var
                    checkbox_items[str(p)] = item

        insert_items('', Path(folder))
        update_token_label()

        def update_token_label():
            tokens = self.compute_token_count({Path(p) for p, var in checkbox_vars.items() if var.get()})
            max_tokens = self.settings.get("max_tokens", 200000)
            token_label.config(text=f"Tokens: {tokens} / {max_tokens}")

        def update_preview_live():
            if self.enable_preview.get():
                preview_text = self.get_preview_text({Path(p) for p, var in checkbox_vars.items() if var.get()})
                if self.preview_window is None or not self.preview_window.winfo_exists():
                    self.preview_window = Toplevel(self.root)
                    self.preview_window.title("Preview")
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

        ttk.Button(selector, text="Select/Deselect All", command=toggle_all).pack(pady=5)

        ttk.Button(
            selector,
            text="Confirm Selection",
            command=lambda: (
                self.selected_files.update({Path(p) for p, var in checkbox_vars.items() if var.get()}),
                selector.destroy(),
                self.preview_window and self.preview_window.destroy(),
            ),
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
        header = f"Token estimate: {token_count} (remaining {remaining})\n{'='*40}\n"
        return header + full_text

    def generate_preview_lines(self, start_folder, included_files):
        lines = []
        project_name = Path(start_folder).name
        date_str = datetime.now().strftime('%Y%m%d')
        header = f"Project: {project_name} - {date_str}\n"
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
                    "Limit reached",
                    f"Reached the limit of {max_tokens} tokens. Some files were skipped.",
                )
                break
            lines.extend(chunk)
            token_count += tokens
        return lines

    def generate(self):
        if not self.start_folder.get() or not self.dest_folder.get():
            messagebox.showerror("Error", "Please select both source and destination folders")
            return
        if not self.selected_files:
            messagebox.showerror("Error", "No files selected")
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
            messagebox.showinfo("Done", f"Files generated:\n{msg}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
