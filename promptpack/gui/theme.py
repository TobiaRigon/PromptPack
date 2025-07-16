import tkinter as tk
from tkinter import ttk


def apply_theme(app):
    """Apply the selected theme to the application widgets."""
    if app.theme.get() == "dark":
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

    app.root.configure(bg=palette["background"])
    app.root.tk_setPalette(**palette)
    style = ttk.Style(app.root)
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

    if app.preview_window and app.preview_window.winfo_exists():
        app.preview_window.tk_setPalette(**palette)
        if app.preview_text:
            app.preview_text.configure(bg=palette["background"], fg=palette["foreground"])

