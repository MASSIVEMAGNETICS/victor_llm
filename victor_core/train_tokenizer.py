import argparse
from pathlib import Path

from victor_core.logger import VictorLoggerStub
from victor_core.nlp.fractal_tokenizer import FractalTokenKernel_v1_1_0


logger = VictorLoggerStub(component="VictorTokenizerTrainer")


def _load_corpus(path: Path) -> list[str]:
    if path.is_dir():
        files = sorted(p for p in path.rglob("*.txt") if p.is_file())
        corpus = []
        for file_path in files:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            corpus.extend(line for line in lines if line.strip())
        if not corpus:
            logger.warn(f"No non-empty lines found in directory: {path}")
        return corpus

    if path.is_file():
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return [line for line in lines if line.strip()]

    raise FileNotFoundError(f"Training input path does not exist: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Victor tokenizer vocabulary from text data.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to a text file or directory of .txt files to train on.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("models/tokenizer_vocab.json"),
        help="Path to save the trained vocabulary JSON.",
    )
    args = parser.parse_args()

    corpus = _load_corpus(args.input)
    if not corpus:
        logger.warn("Training aborted: no training data found.")
        return

    tokenizer = FractalTokenKernel_v1_1_0()
    tokenizer.train(corpus)
    tokenizer.save_vocabulary(args.output)


if __name__ == "__main__":
    main()
