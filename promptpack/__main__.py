import os
import sys
import tkinter as tk

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from promptpack.gui import PromptPackApp


def main():
    root = tk.Tk()
    app = PromptPackApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
