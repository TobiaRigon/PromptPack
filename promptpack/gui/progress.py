from tkinter import ttk


def show_progress(app, message: str, maximum: int | None = None):
    if app.progress_frame:
        app.progress_frame.destroy()
    app.progress_var.set(0)
    app.progress_frame = ttk.Frame(app.root)
    app.progress_frame.grid(row=9, column=0, columnspan=3, pady=(10, 5))
    ttk.Label(app.progress_frame, text=message).pack(padx=10, pady=5)
    mode = "indeterminate" if maximum is None else "determinate"
    app.progress_bar = ttk.Progressbar(
        app.progress_frame,
        variable=app.progress_var,
        maximum=maximum if maximum is not None else 100,
        mode=mode,
    )
    app.progress_bar.pack(padx=10, pady=5, fill="x", expand=True)
    if mode == "indeterminate":
        app.progress_bar.start()


def update_progress(app, value: int, maximum: int):
    if app.progress_bar and app.progress_bar["mode"] == "determinate":
        app.progress_bar.config(maximum=maximum)
        app.progress_var.set(value)
        app.progress_bar.update_idletasks()


def hide_progress(app):
    if app.progress_bar:
        if app.progress_bar["mode"] == "indeterminate":
            app.progress_bar.stop()
    if app.progress_frame:
        app.progress_frame.destroy()
        app.progress_frame = None
        app.progress_bar = None

