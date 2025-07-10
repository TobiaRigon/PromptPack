import os
import PySimpleGUI as sg
from pathlib import Path
from datetime import datetime

LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.php': 'php',
    '.html': 'html',
    '.css': 'css',
}

def generate_output(start_folder: Path, dest_folder: Path, extensions, skip_dirs, skip_files, as_markdown: bool,
                     include_heading: bool, use_code_block: bool):
    lines = []
    project_name = start_folder.name
    date_str = datetime.now().strftime('%Y%m%d')
    header = f"Progetto: {project_name} - {date_str}\n\n"
    lines.append(header)

    for root, dirs, files in os.walk(start_folder):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            path = Path(root) / file
            if path.suffix not in extensions:
                continue
            if path.name in skip_files:
                continue
            relative = path.relative_to(start_folder)
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            if include_heading:
                lines.append(f"## {relative.as_posix()}\n")
            if as_markdown and use_code_block:
                lang = LANG_MAP.get(path.suffix, '')
                lines.append(f"```{lang}\n{content}\n```\n\n")
            else:
                lines.append(f"{content}\n\n")

    output_name = f"{project_name}-{date_str}.{'md' if as_markdown else 'txt'}"
    output_path = dest_folder / output_name
    output_path.write_text(''.join(lines), encoding='utf-8')
    return output_path

def main():
    sg.theme('SystemDefault')
    layout = [
        [sg.Text('Cartella di partenza'), sg.Input(key='START_FOLDER'), sg.FolderBrowse('Sfoglia')],
        [sg.Text('Estensioni da includere (seleziona con Ctrl)')],
        [sg.Listbox(values=['.php', '.js', '.ts', '.html', '.css'], select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                    size=(20,5), key='EXTS', default_values=['.php', '.js', '.ts', '.html', '.css'])],
        [sg.Text('Cartelle da escludere (seleziona con Ctrl)')],
        [sg.Listbox(values=['vendor', 'node_modules', '.git'], select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                    size=(20,3), key='SKIP_DIRS', default_values=['vendor', 'node_modules', '.git'])],
        [sg.Text('File da escludere (seleziona con Ctrl)')],
        [sg.Listbox(values=['.env', 'README.md'], select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                    size=(20,2), key='SKIP_FILES', default_values=['.env', 'README.md'])],
        [sg.Text('Formato output'),
         sg.Radio('Markdown (.md)', 'FORMAT', key='MD', default=True),
         sg.Radio('Testo (.txt)', 'FORMAT', key='TXT')],
        [sg.Checkbox('Includi nomi file come intestazioni', key='HEADINGS', default=True)],
        [sg.Checkbox('Usa blocchi di codice (solo Markdown)', key='CODEBLOCK', default=True)],
        [sg.Text('Cartella di destinazione'), sg.Input(key='DEST_FOLDER'), sg.FolderBrowse('Sfoglia')],
        [sg.Button('Genera')]
    ]

    window = sg.Window('PromptPack', layout)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        if event == 'Genera':
            start_folder = Path(values['START_FOLDER']) if values['START_FOLDER'] else None
            dest_folder = Path(values['DEST_FOLDER']) if values['DEST_FOLDER'] else None
            if not start_folder or not start_folder.exists():
                sg.popup('Seleziona una cartella di partenza valida')
                continue
            if not dest_folder or not dest_folder.exists():
                sg.popup('Seleziona una cartella di destinazione valida')
                continue
            extensions = set(values['EXTS'])
            skip_dirs = set(values['SKIP_DIRS'])
            skip_files = set(values['SKIP_FILES'])
            as_markdown = values['MD']
            include_heading = values['HEADINGS']
            use_code_block = values['CODEBLOCK']
            output_path = generate_output(start_folder, dest_folder, extensions, skip_dirs, skip_files,
                                          as_markdown, include_heading, use_code_block)
            sg.popup(f"File generato in: {output_path}")

    window.close()

if __name__ == '__main__':
    main()
