from PySide6 import QtWidgets

from promptpack import PromptPackQtApp


def main():
    app = QtWidgets.QApplication([])
    window = PromptPackQtApp()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
