import argparse
from pathlib import Path

from victor_core.config import ASIConfigCore
from victor_core.nlp.fractal_tokenizer import FractalTokenKernel_v1_1_0


def _collect_files(paths: list[Path], extensions: set[str]) -> list[Path]:
    collected: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.suffix.lower() in extensions:
                    collected.append(candidate)
        elif path.is_file() and path.suffix.lower() in extensions:
            collected.append(path)
    return collected


def _load_corpus(paths: list[str], extensions: set[str]) -> list[str]:
    resolved_paths = [Path(path).expanduser().resolve() for path in paths]
    files = _collect_files(resolved_paths, extensions)
    corpus: list[str] = []
    for file_path in files:
        corpus.append(file_path.read_text(encoding="utf-8", errors="ignore"))
    return corpus


def _train_tokenizer(corpus: list[str], output_path: Path, label: str) -> None:
    tokenizer = FractalTokenKernel_v1_1_0()
    tokenizer.train(corpus)
    tokenizer.save(str(output_path))
    print(f"{label} tokenizer saved to {output_path} with vocab size {len(tokenizer.vocabulary)}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Victor tokenizers from text or code corpora.")
    parser.add_argument(
        "--corpus",
        nargs="+",
        help="Paths to text files or directories to train the NLP tokenizer.",
    )
    parser.add_argument(
        "--code-corpus",
        nargs="+",
        help="Paths to code files or directories to train the code tokenizer.",
    )
    parser.add_argument(
        "--output-dir",
        default=ASIConfigCore.TOKENIZER_DIR,
        help="Directory to save trained tokenizers.",
    )

    args = parser.parse_args()
    if not args.corpus and not args.code_corpus:
        parser.error("Provide --corpus and/or --code-corpus to train tokenizers.")

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.corpus:
        corpus = _load_corpus(args.corpus, {".txt", ".md", ".rst"})
        if not corpus:
            raise SystemExit("No NLP corpus files found with extensions: .txt, .md, .rst")
        _train_tokenizer(corpus, output_dir / "nlp_tokenizer.json", "NLP")

    if args.code_corpus:
        code_corpus = _load_corpus(args.code_corpus, {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml"})
        if not code_corpus:
            raise SystemExit("No code corpus files found with supported extensions.")
        _train_tokenizer(code_corpus, output_dir / "code_tokenizer.json", "Code")


if __name__ == "__main__":
    main()
