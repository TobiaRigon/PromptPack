# PromptPack

**PromptPack** is a desktop application written in Python with Tkinter that allows you to quickly generate a Markdown or plain text summary of selected source files from a project folder. It's designed for developers and technical writers who need to prepare code documentation, share source samples, or create prompt material for LLMs.

## Features

- GUI for selecting a source folder and choosing which files to include
- Treeview interface with checkboxes for including/excluding individual files
- Live preview window to see the generated output before exporting
- Default filters for file extensions and folders (e.g., skip `.env`, `node_modules`, `.git`, etc.)
- Saves and loads user settings to/from a JSON file
- Option to format output as Markdown with code blocks, headings, and file separators
- Switch between dark and light mode, con pulsanti e campi scuri quando il tema è impostato su "dark"

## Requirements

- Python 3.7+
- Tkinter (comes pre-installed with Python on most systems)

## Installation

1. Clone or download the repository.
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # on Linux/macOS
   venv\Scripts\activate     # on Windows
   ```
3. Run the script:
   ```bash
   python promptpack.py
   ```

 
## Struttura del progetto

Il codice sorgente è organizzato nel pacchetto `promptpack`:
- `gui.py` contiene l'interfaccia grafica.
- `settings.py` gestisce le impostazioni.
- `utils.py` racchiude le funzioni di supporto.

Il file `promptpack.py` avvia semplicemente l'applicazione.

## How to Use

1. **Start Folder**: Click *Browse* to select the folder containing the files you want to include.
2. **Select Files**: Opens an expandable tree of all folders and files. You can include/exclude each item via checkboxes.
   - Default selections are based on the current settings.
3. **Settings**: Define default allowed extensions, excluded folders and files. Also choose:
   - Markdown output
   - Include file headings
   - Use code blocks for each file
4. **Live Preview**: Enables a real-time preview of the final output file.
5. **Destination Folder**: Choose where the final file will be saved.
6. **Generate**: Creates a Markdown or plain text file containing the selected source files, formatted according to your settings.

## Settings

User preferences are saved in a file named `promptpack_settings.json` in the same folder as the script. It stores:

```json
{
  "allowed_exts": [".php", ".js", ".ts", ".html", ".css", ".py"],
  "excluded_dirs": ["vendor", ".git", "node_modules"],
  "excluded_files": [".env", "README.md"],
  "as_markdown": true,
  "include_heading": true,
  "use_code_block": true
}
```

## Output Example

If Markdown and code blocks are enabled, the output will look like:

````markdown
Progetto: my-app - 20250710

## src/index.js

```javascript
console.log("Hello world!");
```

## styles/main.css

```css
body {
  background: #fff;
}
```
````

## Notes

- Only files with allowed extensions are included by default.
- Hidden folders and ignored files are shown but deselected by default.
- All preview and configuration windows inherit the custom icon (`promptpack.ico`), if available.

## License

MIT License

## Author

Created by [Tobia Rigon](https://github.com/yourprofile), 2025.
