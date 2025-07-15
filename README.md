# PromptPack

**PromptPack** is a desktop application written in Python with Tkinter that allows you to quickly generate summaries of selected source files in Markdown, plain text or JSON format. It's designed for developers and technical writers who need to prepare code documentation, share source samples, or create prompt material for LLMs.

## Features

- GUI for selecting a source folder and choosing which files to include
- Treeview interface with checkboxes for including/excluding individual files
- Live preview window to see the generated output before exporting
- Default filters for file extensions and folders (e.g., skip `.env`, `node_modules`, `.git`, etc.)
- Saves and loads user settings to/from a JSON file
- Choose export format (TXT, Markdown or JSON) and optionally include code blocks and headings
- Optionally export only the file tree without contents
- Switch between dark and light mode, with buttons and fields adopting dark colors when the theme is set to "dark"
- Files listed in a `.gitignore` file are automatically deselected
- Passwords and API keys in the output are masked for safety
- Exports larger than the chosen token limit are automatically split into multiple files
- Select a token limit preset (ChatGPT, Gemini, Claude) or set a custom value
- Copy the preview to the clipboard with one click
- Select or deselect all files at once when choosing what to include
- Remaining token counter shows usage versus limit
- Remembers last source folder and file selection

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

 
## Project Structure

The source code is organized in the `promptpack` package:
- `gui.py` contains the graphical interface.
- `settings.py` manages the application settings.
- `utils.py` includes supporting functions.

The file `promptpack.py` simply launches the application.

## How to Use

1. **Start Folder**: Click *Browse* to select the folder containing the files you want to include.
2. **Select Files**: Opens an expandable tree of all folders and files. You can include/exclude each item via checkboxes.
   - Default selections are based on the current settings.
3. **Settings**: Define default allowed extensions, excluded folders and files. Also choose:
   - Export format (txt, md, json)
   - Include file headings
   - Use code blocks for each file (Markdown only)
   - Export only the file tree
   - Token limit for preview and export
4. **Live Preview**: Enables a real-time preview of the final output file.
5. **Destination Folder**: Choose where the final file will be saved.
6. **Generate**: Creates an output file in the chosen format containing the selected source files, formatted according to your settings.

## Settings

User preferences are saved in a file named `promptpack_settings.json` in the same folder as the script. It stores:

```json
{
  "allowed_exts": [".php", ".js", ".ts", ".html", ".css", ".py"],
  "excluded_dirs": ["vendor", ".git", "node_modules"],
 "excluded_files": [".env", "README.md"],
 "export_format": "md",
 "tree_only": false,
 "include_heading": true,
  "use_code_block": true,
  "max_tokens": 200000,
  "last_start_folder": "",
  "last_selected_files": []
}
```

## Output Example

If Markdown and code blocks are enabled, the output will look like:

````markdown
Project: my-app - 20250710

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
- If a `.gitignore` file is present, its patterns are also deselected automatically.
- Detected passwords and API keys are replaced with `***` in the preview and export.
- All preview and configuration windows inherit the custom icon (`promptpack.ico`), if available.
- The "Select Files to Include" window uses a dark background when the dark theme is enabled.
- To avoid slowdowns, preview stops gathering content after the selected token limit. Export files are split when they exceed this limit.
- A clipboard button lets you quickly copy the preview text.
- A counter displays remaining tokens while selecting files.
- Last source folder and selections are remembered between runs.

## License

MIT License

## Author

Created by [Tobia Rigon](https://github.com/yourprofile), 2025.
