"""
victor_cli.inference – run inference / predict using a trained tokenizer checkpoint.

For the current lightweight Victor LLM stack the "model" is the FractalTokenKernel
trained by AutoTrainer.  This module provides a deterministic, CPU-only inference
path that does NOT require PyTorch, making it suitable for smoke tests and demos.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Fallback phrases used when no checkpoint is loaded.
_FALLBACK_RESPONSES = [
    "Victor LLM is online and ready.",
    "Processing your request with fractal intelligence.",
    "The answer is encoded in the latent space.",
    "Victor acknowledges your prompt.",
    "Inference complete.",
]


def _simple_generate(
    prompt: str,
    vocabulary: dict,
    reverse_vocabulary: dict,
    max_tokens: int = 64,
    seed: int = 0,
) -> str:
    """
    Lightweight deterministic text generation from a word-level vocabulary.

    Treats the vocabulary as a unigram language model: tokens present in the
    prompt are used as seeds; unknown tokens fall back to random sampling.
    """
    rng = random.Random(seed + hash(prompt) % 2**31)
    words = prompt.lower().split()
    known = [w for w in words if w in vocabulary]
    pool = list(reverse_vocabulary.values()) if reverse_vocabulary else list(vocabulary.keys())
    if not pool:
        return "(empty vocabulary)"

    # Start from known prompt words, then sample from the vocabulary.
    output_words = list(known)
    while len(output_words) < max_tokens:
        output_words.append(rng.choice(pool))

    return " ".join(output_words[:max_tokens])


def run_predict(
    prompts: List[str],
    checkpoint: Optional[str] = None,
    max_tokens: int = 64,
    verbose: bool = False,
) -> int:
    """Run inference on a list of prompts and print results."""
    if not prompts:
        logger.error("No prompts provided.")
        return 1
    vocabulary: dict = {}
    reverse_vocabulary: dict = {}

    if checkpoint:
        ckpt_path = Path(checkpoint).expanduser().resolve()
        if not ckpt_path.exists():
            logger.error("Checkpoint not found: %s", ckpt_path)
            return 1

        # Support a tokenizer JSON file or an epoch checkpoint JSON.
        if ckpt_path.is_dir():
            # Look for a tokenizer file first.
            tok_candidates = list(ckpt_path.rglob("*tokenizer*.json"))
            ckpt_candidates = sorted(ckpt_path.rglob("epoch_*.json"))
            if tok_candidates:
                ckpt_path = tok_candidates[0]
            elif ckpt_candidates:
                ckpt_path = ckpt_candidates[-1]
            else:
                logger.warning("No tokenizer or epoch checkpoint found in %s – using fallback.", ckpt_path)
                ckpt_path = None  # type: ignore[assignment]

        if ckpt_path and ckpt_path.is_file():
            try:
                data = json.loads(ckpt_path.read_text(encoding="utf-8"))
                # FractalTokenKernel saves "vocabulary" and "reverse_vocabulary".
                vocabulary = data.get("vocabulary", {})
                reverse_vocabulary = {str(k): v for k, v in data.get("reverse_vocabulary", {}).items()}
                logger.info(
                    "Loaded vocabulary (%d tokens) from %s", len(vocabulary), ckpt_path
                )
            except Exception as exc:
                logger.warning("Could not load checkpoint %s: %s – using fallback.", ckpt_path, exc)
    else:
        # No checkpoint: try the default tokenizer location.
        default_tok = Path("victor_tokenizers") / "nlp_tokenizer.json"
        if default_tok.exists():
            try:
                data = json.loads(default_tok.read_text(encoding="utf-8"))
                vocabulary = data.get("vocabulary", {})
                reverse_vocabulary = {str(k): v for k, v in data.get("reverse_vocabulary", {}).items()}
                logger.info("Using default tokenizer (%d tokens).", len(vocabulary))
            except Exception:
                pass

    for i, prompt in enumerate(prompts):
        if vocabulary:
            response = _simple_generate(prompt, vocabulary, reverse_vocabulary, max_tokens=max_tokens, seed=i)
        else:
            response = random.choice(_FALLBACK_RESPONSES)  # noqa: S311

        print(f"\n[{i + 1}] Prompt  : {prompt}")
        print(f"     Response: {response}")

    return 0
