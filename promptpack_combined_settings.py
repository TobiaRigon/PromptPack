
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Toplevel
from pathlib import Path
from datetime import datetime

DEFAULT_EXTENSIONS = ['.php', '.js', '.ts', '.html', '.css', '.py']
DEFAULT_EXCLUDED_DIRS = ['vendor', '.git', 'node_modules']
DEFAULT_EXCLUDED_FILES = ['.env', 'README.md']

LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.php': 'php',
    '.html': 'html',
    '.css': 'css',
}

class PromptPackApp:
    def __init__(self, root):
        self.root = root
        root.title("PromptPack")
        self.start_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.as_markdown = tk.BooleanVar(value=True)
        self.include_heading = tk.BooleanVar(value=True)
        self.use_code_block = tk.BooleanVar(value=True)

        self.allowed_exts = DEFAULT_EXTENSIONS.copy()
        self.excluded_dirs = DEFAULT_EXCLUDED_DIRS.copy()
        self.excluded_files = DEFAULT_EXCLUDED_FILES.copy()
        self.selected_files = set()

        self.build_gui()

    def build_gui(self):
        tk.Label(self.root, text="Cartella di partenza").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.start_folder, width=50).grid(row=0, column=1, padx=5)
        tk.Button(self.root, text="Sfoglia", command=self.browse_start).grid(row=0, column=2)

        tk.Button(self.root, text="Seleziona file", command=self.select_files).grid(row=1, column=1, pady=5)
        tk.Button(self.root, text="Impostazioni", command=self.configure_defaults).grid(row=1, column=2)

        tk.Label(self.root, text="Cartella di destinazione").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.dest_folder, width=50).grid(row=2, column=1, padx=5)
        tk.Button(self.root, text="Sfoglia", command=self.browse_dest).grid(row=2, column=2)

        tk.Checkbutton(self.root, text="Formato Markdown", variable=self.as_markdown).grid(row=3, column=0, sticky='w', padx=5)
        tk.Checkbutton(self.root, text="Includi intestazioni file", variable=self.include_heading).grid(row=3, column=1, sticky='w')
        tk.Checkbutton(self.root, text="Blocchi di codice", variable=self.use_code_block).grid(row=3, column=2, sticky='w')

        tk.Button(self.root, text="Genera", command=self.generate).grid(row=4, column=1, pady=10)

    def browse_start(self):
        folder = filedialog.askdirectory()
        if folder:
            self.start_folder.set(folder)

    def browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder.set(folder)

    def configure_defaults(self):
        win = Toplevel(self.root)
        win.title("Impostazioni predefinite")
        win.geometry("500x300")

        tk.Label(win, text="Estensioni incluse (es. .php,.js,.py)").pack()
        ext_entry = tk.Text(win, height=2)
        ext_entry.insert("1.0", ",".join(self.allowed_exts))
        ext_entry.pack(fill=tk.X, padx=10)

        tk.Label(win, text="Cartelle escluse (es. node_modules,vendor)").pack()
        dir_entry = tk.Text(win, height=2)
        dir_entry.insert("1.0", ",".join(self.excluded_dirs))
        dir_entry.pack(fill=tk.X, padx=10)

        def save():
            self.allowed_exts = [x.strip() for x in ext_entry.get("1.0", "end").split(",") if x.strip()]
            self.excluded_dirs = [x.strip() for x in dir_entry.get("1.0", "end").split(",") if x.strip()]
            win.destroy()

        tk.Button(win, text="Salva", command=save).pack(pady=10)

    def select_files(self):
        folder = self.start_folder.get()
        if not folder:
            messagebox.showerror("Errore", "Seleziona prima la cartella di partenza")
            return

        self.selector = Toplevel(self.root)
        self.selector.title("Seleziona file da includere")
        self.selector.geometry("850x500")

        self.tree = ttk.Treeview(self.selector, columns=("fullpath", "type"))
        self.tree.heading("#0", text="Nome")
        self.tree.heading("type", text="Tipo")
        self.tree.column("fullpath", width=0, stretch=False)
        self.tree.column("type", width=80)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.checkbox_vars = {}

        def insert_items(parent, path):
            for p in sorted(path.iterdir()):
                if p.is_dir():
                    node = self.tree.insert(parent, 'end', text=p.name, values=(str(p), "dir"), open=False)
                    insert_items(node, p)
                else:
                    default_checked = self.is_valid(p) and not any(skip in p.parts for skip in self.excluded_dirs)
                    var = tk.BooleanVar(value=default_checked)
                    self.checkbox_vars[str(p)] = var
                    node = self.tree.insert(parent, 'end', text=f"[{'x' if var.get() else ' '}] {p.name}",
                                            values=(str(p), "file"))

        insert_items('', Path(folder))

        def toggle_checkbox(event):
            item = self.tree.identify_row(event.y)
            if not item:
                return
            values = self.tree.item(item, 'values')
            if len(values) < 2:
                return
            path_str, typ = values
            if typ == "file" and path_str in self.checkbox_vars:
                var = self.checkbox_vars[path_str]
                var.set(not var.get())
                new_label = f"[{'x' if var.get() else ' '}] {Path(path_str).name}"
                self.tree.item(item, text=new_label)

        self.tree.bind("<Button-1>", toggle_checkbox)

        def confirm():
            self.selected_files = {Path(p) for p, var in self.checkbox_vars.items() if var.get()}
            self.selector.destroy()

        tk.Button(self.selector, text="Conferma selezione", command=confirm).pack(pady=5)

    def is_valid(self, f):
        return f.suffix in self.allowed_exts and f.name not in self.excluded_files

    def generate(self):
        if not self.start_folder.get() or not self.dest_folder.get():
            messagebox.showerror("Errore", "Seleziona entrambe le cartelle")
            return
        if not self.selected_files:
            messagebox.showerror("Errore", "Nessun file selezionato")
            return
        try:
            output_path = generate_output(
                self.start_folder.get(), self.dest_folder.get(),
                list(self.selected_files),
                self.as_markdown.get(), self.include_heading.get(), self.use_code_block.get()
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
            lines.append(f"```{lang}\n{content}\n```\n\n")
        else:
            lines.append(f"{content}\n\n")

    output_file = Path(dest_folder) / f"{project_name}-{date_str}.{ 'md' if as_markdown else 'txt' }"
    output_file.write_text(''.join(lines), encoding='utf-8')
    return output_file

if __name__ == "__main__":
    root = tk.Tk()
    app = PromptPackApp(root)
    root.mainloop()
