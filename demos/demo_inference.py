#!/usr/bin/env python3
"""
demo_inference.py – Minimal Victor LLM inference demo.

Loads (or trains) a tiny FractalTokenKernel from the example dataset and
generates a response for a hard-coded prompt.  No GPU required.

Run from the repo root:
    python demos/demo_inference.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure repo root is importable.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from victor_core.nlp.fractal_tokenizer import FractalTokenKernel_v1_1_0
from victor_cli.inference import _simple_generate


def main() -> None:
    print("=== Victor LLM – Minimal Inference Demo ===\n")

    # 1. Try loading a pre-trained tokenizer if available.
    tokenizer = FractalTokenKernel_v1_1_0()
    tok_path = REPO_ROOT / "victor_tokenizers" / "nlp_tokenizer.json"

    if tok_path.exists():
        loaded = tokenizer.load_from_file(str(tok_path))
        if loaded:
            print(f"Loaded tokenizer from {tok_path}  (vocab size: {len(tokenizer.vocabulary)})")
        else:
            print(f"Failed to load tokenizer from {tok_path} – will train inline.")
    else:
        # Train a tiny tokenizer on the example dataset texts.
        train_jsonl = REPO_ROOT / "datasets" / "example_dataset" / "train.jsonl"
        if not train_jsonl.exists():
            print("Example dataset not found – training on inline corpus.")
            corpus = [
                "Victor LLM is a modular AGI framework.",
                "Machine learning models learn from data.",
                "Neural networks transform input into output.",
                "The quick brown fox jumps over the lazy dog.",
            ]
        else:
            corpus = []
            for line in train_jsonl.read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                if "text" in rec:
                    corpus.append(rec["text"])
            print(f"Training tokenizer on {len(corpus)} example records …")

        tokenizer.train(corpus)
        print(f"Tokenizer trained. Vocab size: {len(tokenizer.vocabulary)}")

    # 2. Run inference.
    prompt = "Victor LLM is modular and powerful"
    print(f"\nPrompt  : {prompt}")

    vocab = tokenizer.vocabulary
    rev_vocab = tokenizer.reverse_vocabulary
    response = _simple_generate(prompt, vocab, rev_vocab, max_tokens=20, seed=7)
    print(f"Response: {response}")

    # 3. Tokenize the prompt.
    tokens = tokenizer.tokenize(prompt)
    print(f"\nTokens  : {tokens}")
    print("\nDemo complete ✅")


if __name__ == "__main__":
    main()
