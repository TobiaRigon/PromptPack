import tkinter as tk
try:
    from tkinterdnd2 import TkinterDnD
except Exception:  # library not available
    TkinterDnD = tk.Tk

from promptpack import PromptPackApp


def main():
    root = TkinterDnD() if TkinterDnD is not tk.Tk else tk.Tk()
    app = PromptPackApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
