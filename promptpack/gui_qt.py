from __future__ import annotations

from pathlib import Path
from datetime import datetime

from PySide6 import QtWidgets

from .settings import load_settings, save_settings
from .utils import generate_output, sanitize_sensitive_data, LANG_MAP
from .tokenizer import estimate_token_count
from .i18n import load_translations


class PromptPackQtApp(QtWidgets.QWidget):
    """Interfaccia grafica basata su Qt."""

    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.translations = load_translations(self.settings.get("language", "eng"))
        self.selected_files: set[Path] = set()
        self.setup_ui()

    # Traduzione semplice
    def t(self, key: str) -> str:
        return self.translations.get(key, key)

    def setup_ui(self):
        self.setWindowTitle("PromptPack")
        layout = QtWidgets.QGridLayout(self)

        self.start_label = QtWidgets.QLabel(self.t("source_folder"))
        self.start_edit = QtWidgets.QLineEdit(self.settings.get("last_start_folder", ""))
        self.start_button = QtWidgets.QPushButton(self.t("browse"))
        self.start_button.clicked.connect(self.browse_start)

        self.select_button = QtWidgets.QPushButton(self.t("select_files"))
        self.select_button.clicked.connect(self.select_files)

        self.dest_label = QtWidgets.QLabel(self.t("dest_folder"))
        self.dest_edit = QtWidgets.QLineEdit()
        self.dest_button = QtWidgets.QPushButton(self.t("browse"))
        self.dest_button.clicked.connect(self.browse_dest)

        self.generate_button = QtWidgets.QPushButton(self.t("generate"))
        self.generate_button.clicked.connect(self.generate)

        layout.addWidget(self.start_label, 0, 0)
        layout.addWidget(self.start_edit, 0, 1)
        layout.addWidget(self.start_button, 0, 2)
        layout.addWidget(self.select_button, 1, 1)
        layout.addWidget(self.dest_label, 2, 0)
        layout.addWidget(self.dest_edit, 2, 1)
        layout.addWidget(self.dest_button, 2, 2)
        layout.addWidget(self.generate_button, 3, 1)

        self.setLayout(layout)

    def browse_start(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, self.t("source"))
        if folder:
            self.start_edit.setText(folder)
            self.settings["last_start_folder"] = folder
            save_settings(self.settings)

    def browse_dest(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, self.t("dest_folder"))
        if folder:
            self.dest_edit.setText(folder)

    def select_files(self):
        folder = self.start_edit.text()
        if not folder:
            QtWidgets.QMessageBox.warning(self, self.t("error"), self.t("need_folders"))
            return
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            self.t("select_files"),
            folder,
            ";;".join(f"*{ext}" for ext in self.settings.get("allowed_exts", [])),
        )
        if files:
            self.selected_files = {Path(f) for f in files}

    def generate_preview_lines(self, start_folder: str, included_files: set[Path]):
        lines: list[str] = []
        project_name = Path(start_folder).name
        date_str = datetime.now().strftime("%Y%m%d")
        header = self.t("project_label", name=project_name, date=date_str) + "\n"
        lines.append(header)
        token_count = estimate_token_count(header)
        max_tokens = self.settings.get("max_tokens", 200000)

        for path in sorted(included_files):
            rel_path = path.relative_to(start_folder)
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            content = sanitize_sensitive_data(content)
            chunk = []
            if self.settings.get("include_heading", True):
                chunk.append(f"## {rel_path.as_posix()}\n")
            if self.settings.get("export_format", "md") == "md" and self.settings.get("use_code_block", True):
                lang = LANG_MAP.get(path.suffix, "")
                chunk.append(f"```{lang}\n{content}\n```\n")
            else:
                chunk.append(f"{content}\n")
            text = "".join(chunk)
            tokens = estimate_token_count(text)
            if token_count + tokens > max_tokens:
                break
            lines.extend(chunk)
            token_count += tokens
        return lines

    def generate(self):
        start = self.start_edit.text()
        dest = self.dest_edit.text()
        if not start or not dest:
            QtWidgets.QMessageBox.critical(self, self.t("error"), self.t("need_folders"))
            return
        if not self.selected_files:
            QtWidgets.QMessageBox.critical(self, self.t("error"), self.t("no_selected"))
            return
        try:
            output_paths = generate_output(
                start,
                dest,
                list(self.selected_files),
                self.settings.get("export_format", "md"),
                self.settings.get("tree_only", False),
                self.settings.get("include_heading", True),
                self.settings.get("use_code_block", True),
                self.settings.get("max_tokens", 200000),
            )
            msg = "\n".join(str(p) for p in output_paths)
            QtWidgets.QMessageBox.information(self, self.t("done"), self.t("files_generated", msg=msg))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, self.t("error"), str(e))
