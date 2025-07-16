import tkinter as tk

from .gui import PromptPackApp


def main():
    root = tk.Tk()
    app = PromptPackApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
