import tkinter as tk
from tkinter import Toplevel, ttk, messagebox
from pathlib import Path
from ..settings import save_settings
from ..utils import apply_icon
from pathspec import PathSpec


def is_valid(app, f: Path) -> bool:
    return f.suffix in app.settings["allowed_exts"] and f.name not in app.settings["excluded_files"]


def update_default_selected_files(app, folder_path: Path):
    gitignore_file = folder_path / ".gitignore"
    if gitignore_file.exists():
        with gitignore_file.open("r", encoding="utf-8") as f:
            app.gitignore_spec = PathSpec.from_lines("gitwildmatch", f)
    else:
        app.gitignore_spec = None

    all_files = folder_path.rglob("*")
    spec = app.gitignore_spec
    app.selected_files = {
        f
        for f in all_files
        if f.is_file()
        and is_valid(app, f)
        and not any(excl in f.parts for excl in app.settings["excluded_dirs"])
        and not (spec and spec.match_file(str(f.relative_to(folder_path))))
    }


def select_files(app):
    folder = app.start_folder.get()
    if not folder:
        messagebox.showerror(app.t("error"), app.t("select_source_first"))
        return

    selector = Toplevel(app.root)
    selector.title(app.t("select_files_title"))
    apply_icon(selector)
    selector.resizable(True, True)
    palette = {
        "background": "#2d2d2d",
        "foreground": "#dcdcdc",
    } if app.theme.get() == "dark" else {
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

    controls = ttk.Frame(selector)
    controls.pack(fill=tk.X, padx=5, pady=5)

    search_var = tk.StringVar()
    ttk.Label(controls, text="Search:").pack(side="left")
    search_entry = ttk.Entry(controls, textvariable=search_var)
    search_entry.pack(side="left", fill="x", expand=True, padx=5)

    ext_var = tk.StringVar(value="All")
    ext_combo = ttk.Combobox(
        controls,
        textvariable=ext_var,
        values=["All", *app.settings["allowed_exts"]],
        state="readonly",
        width=7,
    )
    ext_combo.pack(side="left", padx=5)

    select_visible_var = tk.BooleanVar(value=False)
    select_visible_cb = ttk.Checkbutton(
        controls,
        text=app.t("select_deselect"),
        variable=select_visible_var,
        command=lambda: toggle_visible_all(select_visible_var.get()),
    )
    select_visible_cb.pack(side="left")

    frame = ttk.Frame(selector)
    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    tree = ttk.Treeview(frame, columns=("fullpath", "type"))
    tree.heading("#0", text="Name")
    tree.heading("type", text="Type")
    tree.column("fullpath", width=0, stretch=False)
    tree.column("type", width=80)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    token_label = ttk.Label(selector, text="")
    token_label.pack(pady=2)

    checkbox_vars: dict[str, tk.BooleanVar] = {}
    checkbox_items = {}
    all_state = tk.BooleanVar(value=False)

    def dir_has_visible(path: Path) -> bool:
        term = search_var.get().lower()
        ext = ext_var.get()
        if term and term in path.name.lower():
            return True
        for p in path.iterdir():
            if p.is_dir():
                if dir_has_visible(p):
                    return True
            else:
                if ext != "All" and p.suffix.lower() != ext.lower():
                    continue
                if term and term not in p.name.lower():
                    continue
                return True
        return False

    def refresh_tree(*_args):
        tree.delete(*tree.get_children())

        def insert_items(parent, path: Path):
            if path.is_dir():
                if not dir_has_visible(path):
                    return
                node = tree.insert(parent, 'end', text=path.name, values=(str(path), 'dir'), open=False)
                for child in sorted(path.iterdir()):
                    insert_items(node, child)
            else:
                if ext_var.get() != 'All' and path.suffix.lower() != ext_var.get().lower():
                    return
                term = search_var.get().lower()
                if term and term not in path.name.lower():
                    return
                var = checkbox_vars.get(str(path))
                if var is None:
                    default_checked = (
                        is_valid(app, path)
                        and not any(skip in path.parts for skip in app.settings["excluded_dirs"])
                        and not (
                            app.gitignore_spec
                            and app.gitignore_spec.match_file(str(path.relative_to(folder)))
                        )
                    )
                    var = tk.BooleanVar(value=(path in app.selected_files or default_checked))
                    checkbox_vars[str(path)] = var
                item = tree.insert(parent, 'end', text=f"[{'x' if var.get() else ' '}] {path.name}", values=(str(path), 'file'))
                checkbox_items[str(path)] = item

        insert_items('', Path(folder))
        update_token_label()


    def update_token_label():
        tokens = app.compute_token_count({Path(p) for p, var in checkbox_vars.items() if var.get()})
        max_tokens = app.settings.get("max_tokens", 200000)
        token_label.config(text=app.t("tokens", tokens=tokens, max=max_tokens))

    refresh_tree()
    search_var.trace_add("write", lambda *_: refresh_tree())
    ext_var.trace_add("write", lambda *_: refresh_tree())

    def update_preview_live():
        if app.enable_preview.get():
            files = {Path(p) for p, var in checkbox_vars.items() if var.get()}
            app.build_preview_async(files)
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

    def toggle_visible_all(new_val: bool):
        def apply_to_item(item):
            values = tree.item(item, "values")
            if len(values) >= 2:
                path_str, typ = values
                if typ == "file" and path_str in checkbox_vars:
                    var = checkbox_vars[path_str]
                    var.set(new_val)
                    tree.item(item, text=f"[{'x' if new_val else ' '}] {Path(path_str).name}")
            for child in tree.get_children(item):
                apply_to_item(child)

        for it in tree.get_children(""):
            apply_to_item(it)
        update_preview_live()
        update_token_label()

    def toggle_all():
        new_val = not all_state.get()
        all_state.set(new_val)
        for path_str, var in checkbox_vars.items():
            var.set(new_val)
            item = checkbox_items[path_str]
            tree.item(item, text=f"[{'x' if new_val else ' '}] {Path(path_str).name}")
        update_preview_live()
        update_token_label()


    def confirm_selection():
        app.selected_files = {Path(p) for p, var in checkbox_vars.items() if var.get()}
        app.settings["last_start_folder"] = app.start_folder.get()
        app.settings["last_selected_files"] = [
            str(Path(p).relative_to(app.start_folder.get()))
            for p, var in checkbox_vars.items() if var.get()
        ]
        save_settings(app.settings)
        selector.destroy()
        if app.preview_window and app.preview_window.winfo_exists():
            app.preview_window.destroy()

    ttk.Button(
        selector,
        text=app.t("confirm"),
        command=confirm_selection,
    ).pack(pady=5)

