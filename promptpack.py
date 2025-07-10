import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, Toplevel
from pathlib import Path
from datetime import datetime
import json
import os

SETTINGS_FILE = "promptpack_settings.json"

DEFAULT_SETTINGS = {
    "allowed_exts": [".php", ".js", ".ts", ".html", ".css", ".py"],
    "excluded_dirs": ["vendor", ".git", "node_modules"],
    "excluded_files": [".env", "README.md"],
    "as_markdown": True,
    "include_heading": True,
    "use_code_block": True
}

LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".php": "php",
    ".html": "html",
    ".css": "css",
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

class PromptPackApp:
    def __init__(self, root):
        self.root = root
        root.title("PromptPack")

        self.settings = load_settings()

        self.as_markdown = tk.BooleanVar(value=self.settings["as_markdown"])
        self.include_heading = tk.BooleanVar(value=self.settings["include_heading"])
        self.use_code_block = tk.BooleanVar(value=self.settings["use_code_block"])

        self.start_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.selected_files = set()

        self.build_gui()

    def build_gui(self):
        tk.Label(self.root, text="Cartella di partenza").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.start_folder, width=50).grid(row=0, column=1, padx=5)
        tk.Button(self.root, text="Sfoglia", command=self.browse_start).grid(row=0, column=2)

        tk.Button(self.root, text="Seleziona file", command=self.select_files).grid(row=1, column=1, pady=5)
        tk.Button(self.root, text="Impostazioni", command=self.configure_settings).grid(row=1, column=2)

        tk.Label(self.root, text="Cartella di destinazione").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.dest_folder, width=50).grid(row=2, column=1, padx=5)
        tk.Button(self.root, text="Sfoglia", command=self.browse_dest).grid(row=2, column=2)

        tk.Button(self.root, text="Genera", command=self.generate).grid(row=3, column=1, pady=10)

    def browse_start(self):
        folder = filedialog.askdirectory()
        if folder:
            self.start_folder.set(folder)

    def browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder.set(folder)

    def configure_settings(self):
        win = Toplevel(self.root)
        win.title("Impostazioni")
        win.geometry("500x400")

        def prompt_list(title, key):
            result = simpledialog.askstring(title, f"{title} (separati da virgola):",
                                            initialvalue=",".join(self.settings[key]), parent=win)
            if result is not None:
                self.settings[key] = [x.strip() for x in result.split(",") if x.strip()]

        tk.Button(win, text="Estensioni incluse", command=lambda: prompt_list("Estensioni incluse", "allowed_exts")).pack(pady=5)
        tk.Button(win, text="Cartelle escluse", command=lambda: prompt_list("Cartelle escluse", "excluded_dirs")).pack(pady=5)
        tk.Button(win, text="File esclusi", command=lambda: prompt_list("File esclusi", "excluded_files")).pack(pady=5)

        tk.Checkbutton(win, text="Formato Markdown", variable=self.as_markdown).pack(anchor='w')
        tk.Checkbutton(win, text="Includi intestazioni file", variable=self.include_heading).pack(anchor='w')
        tk.Checkbutton(win, text="Blocchi di codice", variable=self.use_code_block).pack(anchor='w')

        def save_and_close():
            self.settings["as_markdown"] = self.as_markdown.get()
            self.settings["include_heading"] = self.include_heading.get()
            self.settings["use_code_block"] = self.use_code_block.get()
            save_settings(self.settings)
            win.destroy()

        tk.Button(win, text="Salva", command=save_and_close).pack(pady=10)

    def is_valid(self, f):
        return f.suffix in self.settings["allowed_exts"] and f.name not in self.settings["excluded_files"]

    def select_files(self):
        folder = self.start_folder.get()
        if not folder:
            messagebox.showerror("Errore", "Seleziona prima la cartella di partenza")
            return

        selector = Toplevel(self.root)
        selector.title("Seleziona file da includere")
        selector.geometry("850x500")

        tree = ttk.Treeview(selector, columns=("fullpath", "type"))
        tree.heading("#0", text="Nome")
        tree.heading("type", text="Tipo")
        tree.column("fullpath", width=0, stretch=False)
        tree.column("type", width=80)
        tree.pack(fill=tk.BOTH, expand=True)

        checkbox_vars = {}

        def insert_items(parent, path):
            for p in sorted(path.iterdir()):
                if p.is_dir():
                    node = tree.insert(parent, 'end', text=p.name, values=(str(p), "dir"), open=False)
                    insert_items(node, p)
                else:
                    default_checked = self.is_valid(p) and not any(skip in p.parts for skip in self.settings["excluded_dirs"])
                    var = tk.BooleanVar(value=default_checked)
                    checkbox_vars[str(p)] = var
                    label = f"[{'x' if var.get() else ' '}] {p.name}"
                    node = tree.insert(parent, 'end', text=label, values=(str(p), "file"))

        insert_items('', Path(folder))

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

        tree.bind("<Button-1>", toggle_checkbox)

        def confirm():
            self.selected_files = {Path(p) for p, var in checkbox_vars.items() if var.get()}
            selector.destroy()

        tk.Button(selector, text="Conferma selezione", command=confirm).pack(pady=5)

    def generate(self):
        if not self.start_folder.get() or not self.dest_folder.get():
            messagebox.showerror("Errore", "Seleziona entrambe le cartelle")
            return
        if not self.selected_files:
            messagebox.showerror("Errore", "Nessun file selezionato")
            return
        try:
            output_path = generate_output(
                self.start_folder.get(),
                self.dest_folder.get(),
                list(self.selected_files),
                self.as_markdown.get(),
                self.include_heading.get(),
                self.use_code_block.get()
            )
            messagebox.showinfo("Fatto", f"File generato: {output_path}")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

def generate_output(start_folder, dest_folder, included_files, as_markdown, include_heading, use_code_block):
    lines = []
    project_name = Path(start_folder).name
    date_str = datetime.now().strftime('%Y%m%d')
    header = f"Progetto: {project_name} - {date_str}\n\n"
    lines.append(header)

    for path in included_files:
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        rel_path = path.relative_to(start_folder)
        if include_heading:
            lines.append(f"## {rel_path.as_posix()}\n")
        if as_markdown and use_code_block:
            lang = LANG_MAP.get(path.suffix, '')
            lines.append(f"

{lang}\n{content}\n

\n\n")
        else:
            lines.append(f"{content}\n\n")

    output_file = Path(dest_folder) / f"{project_name}-{date_str}.{ 'md' if as_markdown else 'txt' }"
    output_file.write_text(''.join(lines), encoding='utf-8')
    return output_file

if __name__ == "__main__":
    root = tk.Tk()
    app = PromptPackApp(root)
    root.mainloop()