import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Toplevel, ttk
from pathlib import Path
from datetime import datetime
from tempfile import NamedTemporaryFile
import webbrowser
import markdown

from .settings import load_settings, save_settings
from .utils import apply_icon, estimate_token_count, LANG_MAP, generate_output


class PromptPackApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("PromptPack")
        apply_icon(root)

        self.settings = load_settings()

        self.as_markdown = tk.BooleanVar(value=self.settings["as_markdown"])
        self.include_heading = tk.BooleanVar(value=self.settings["include_heading"])
        self.use_code_block = tk.BooleanVar(value=self.settings["use_code_block"])
        self.enable_preview = tk.BooleanVar(value=False)

        self.start_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.selected_files = set()

        self.preview_window = None
        self.preview_text = None

        self.build_gui()

    def build_gui(self):
        ttk.Label(self.root, text="Source Folder").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.start_folder, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.root, text="Browse", command=self.browse_start).grid(row=0, column=2)

        ttk.Button(self.root, text="Select Files", command=self.select_files).grid(row=1, column=1, pady=5)
        ttk.Button(self.root, text="Settings", command=self.configure_settings).grid(row=1, column=2)

        ttk.Checkbutton(
            self.root,
            text="Live Preview",
            variable=self.enable_preview,
            command=self.toggle_preview_window,
        ).grid(row=2, column=1, sticky='w')
        ttk.Button(self.root, text="Preview nel browser", command=self.preview_in_browser).grid(row=2, column=2, sticky='w')

        ttk.Label(self.root, text="Destination Folder").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.dest_folder, width=50).grid(row=3, column=1, padx=5)
        ttk.Button(self.root, text="Browse", command=self.browse_dest).grid(row=3, column=2)

        ttk.Button(self.root, text="Generate", command=self.generate).grid(row=4, column=1, pady=10)

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
        win.geometry("500x400")

        def prompt_list(title, key):
            result = simpledialog.askstring(
                title,
                f"{title} (comma separated):",
                initialvalue=",".join(self.settings[key]),
                parent=win,
            )
            if result is not None:
                self.settings[key] = [x.strip() for x in result.split(",") if x.strip()]

        ttk.Button(win, text="Allowed Extensions", command=lambda: prompt_list("Allowed Extensions", "allowed_exts")).pack(pady=5)
        ttk.Button(win, text="Excluded Directories", command=lambda: prompt_list("Excluded Directories", "excluded_dirs")).pack(pady=5)
        ttk.Button(win, text="Excluded Files", command=lambda: prompt_list("Excluded Files", "excluded_files")).pack(pady=5)

        ttk.Checkbutton(win, text="Markdown Format", variable=self.as_markdown).pack(anchor='w')
        ttk.Checkbutton(win, text="Include File Headings", variable=self.include_heading).pack(anchor='w')
        ttk.Checkbutton(win, text="Use Code Blocks", variable=self.use_code_block).pack(anchor='w')

        ttk.Button(
            win,
            text="Save",
            command=lambda: (
                save_settings(
                    {
                        **self.settings,
                        "as_markdown": self.as_markdown.get(),
                        "include_heading": self.include_heading.get(),
                        "use_code_block": self.use_code_block.get(),
                    }
                ),
                win.destroy(),
            ),
        ).pack(pady=10)

    def is_valid(self, f: Path) -> bool:
        return f.suffix in self.settings["allowed_exts"] and f.name not in self.settings["excluded_files"]

    def update_default_selected_files(self, folder_path: Path):
        all_files = folder_path.rglob("*")
        self.selected_files = {
            f
            for f in all_files
            if f.is_file()
            and self.is_valid(f)
            and not any(excl in f.parts for excl in self.settings["excluded_dirs"])
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

        css = """
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

        html = f"<html><head>{css}</head><body>{html_body}</body></html>"
        with NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as tmp:
            tmp.write(html)
            webbrowser.open(f"file://{tmp.name}")

    def select_files(self):
        folder = self.start_folder.get()
        if not folder:
            messagebox.showerror("Error", "Please select the source folder first")
            return

        selector = Toplevel(self.root)
        selector.title("Select Files to Include")
        apply_icon(selector)
        selector.geometry("850x500")

        tree = ttk.Treeview(selector, columns=("fullpath", "type"))
        tree.heading("#0", text="Name")
        tree.heading("type", text="Type")
        tree.column("fullpath", width=0, stretch=False)
        tree.column("type", width=80)
        tree.pack(fill=tk.BOTH, expand=True)

        checkbox_vars = {}

        def insert_items(parent, path: Path):
            for p in sorted(path.iterdir()):
                if p.is_dir():
                    node = tree.insert(parent, 'end', text=p.name, values=(str(p), "dir"), open=False)
                    insert_items(node, p)
                else:
                    default_checked = self.is_valid(p) and not any(
                        skip in p.parts for skip in self.settings["excluded_dirs"]
                    )
                    var = tk.BooleanVar(value=default_checked)
                    checkbox_vars[str(p)] = var
                    label = f"[{'x' if var.get() else ' '}] {p.name}"
                    tree.insert(parent, 'end', text=label, values=(str(p), "file"))

        insert_items('', Path(folder))

        def update_preview_live():
            if self.enable_preview.get():
                preview_text = self.get_preview_text({Path(p) for p, var in checkbox_vars.items() if var.get()})
                if self.preview_window is None or not self.preview_window.winfo_exists():
                    self.preview_window = Toplevel(self.root)
                    self.preview_window.title("Preview")
                    apply_icon(self.preview_window)
                    self.preview_text = tk.Text(self.preview_window, wrap="word")
                    self.preview_text.pack(fill="both", expand=True)
                self.preview_text.delete("1.0", "end")
                self.preview_text.insert("1.0", preview_text)

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

        tree.bind("<Button-1>", toggle_checkbox)

        ttk.Button(
            selector,
            text="Confirm Selection",
            command=lambda: (
                self.selected_files.update({Path(p) for p, var in checkbox_vars.items() if var.get()}),
                selector.destroy(),
                self.preview_window and self.preview_window.destroy(),
            ),
        ).pack(pady=5)

    def get_preview_text(self, included_files):
        preview_lines = self.generate_preview_lines(self.start_folder.get(), included_files)
        full_text = "\n".join(preview_lines)
        token_count = estimate_token_count(full_text)
        header = f"Token estimate: {token_count}\n{'='*40}\n"
        return header + full_text

    def generate_preview_lines(self, start_folder, included_files):
        lines = []
        project_name = Path(start_folder).name
        date_str = datetime.now().strftime('%Y%m%d')
        lines.append(f"Project: {project_name} - {date_str}\n")

        for path in sorted(included_files):
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            rel_path = path.relative_to(start_folder)
            if self.include_heading.get():
                lines.append(f"## {rel_path.as_posix()}\n")
            if self.as_markdown.get() and self.use_code_block.get():
                lang = LANG_MAP.get(path.suffix, '')
                lines.append(f"```{lang}\n{content}\n```\n")
            else:
                lines.append(f"{content}\n")
        return lines

    def generate(self):
        if not self.start_folder.get() or not self.dest_folder.get():
            messagebox.showerror("Error", "Please select both source and destination folders")
            return
        if not self.selected_files:
            messagebox.showerror("Error", "No files selected")
            return
        try:
            output_path = generate_output(
                self.start_folder.get(),
                self.dest_folder.get(),
                list(self.selected_files),
                self.as_markdown.get(),
                self.include_heading.get(),
                self.use_code_block.get(),
            )
            messagebox.showinfo("Done", f"File generated: {output_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
