import argparse
from pathlib import Path
from .settings import load_settings
from .utils import generate_output
from .tokenizer import set_default_model
from pathspec import PathSpec


def collect_files(start_folder: str, settings) -> list[Path]:
    folder = Path(start_folder)
    gitignore = folder / ".gitignore"
    spec = None
    if gitignore.exists():
        with gitignore.open("r", encoding="utf-8") as f:
            spec = PathSpec.from_lines("gitwildmatch", f)
    files = [
        p
        for p in folder.rglob("*")
        if p.is_file()
        and p.suffix in settings["allowed_exts"]
        and p.name not in settings["excluded_files"]
        and not any(excl in p.parts for excl in settings["excluded_dirs"])
        and not (spec and spec.match_file(str(p.relative_to(folder))))
    ]
    return files


def main():
    parser = argparse.ArgumentParser(description="PromptPack CLI")
    parser.add_argument("source", help="cartella sorgente")
    parser.add_argument("dest", help="cartella di destinazione")
    parser.add_argument("--format", choices=["txt", "md", "json"], dest="format")
    parser.add_argument("--tree-only", action="store_true")
    parser.add_argument("--no-heading", action="store_true")
    parser.add_argument("--no-code-block", action="store_true")
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--model", choices=["gpt", "claude", "gemini"], help="tokenizer model")
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    if args.model:
        set_default_model(args.model)

    settings = load_settings()
    export_format = args.format or settings.get("export_format", "md")
    tree_only = args.tree_only or settings.get("tree_only", False)
    include_heading = settings.get("include_heading", True)
    if args.no_heading:
        include_heading = False
    use_code_block = settings.get("use_code_block", True)
    if args.no_code_block:
        use_code_block = False
    max_tokens = args.max_tokens or settings.get("max_tokens", 200000)

    files = collect_files(args.source, settings)
    total = len(files)

    def cb(current, maximum):
        if args.progress:
            percent = int(current / maximum * 100)
            print(f"\r{percent}% ({current}/{maximum})", end="", flush=True)

    output_paths = generate_output(
        args.source,
        args.dest,
        files,
        export_format,
        tree_only,
        include_heading,
        use_code_block,
        max_tokens,
        progress_callback=cb if args.progress else None,
    )
    if args.progress:
        print()
    for p in output_paths:
        print(p)


if __name__ == "__main__":
    main()
