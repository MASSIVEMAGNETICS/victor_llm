"""
victor_cli.benchmark – latency, throughput and memory benchmarking for Victor LLM.

Measures:
  - Per-prompt latency (seconds)
  - Throughput (tokens / second)
  - Peak RSS memory (MB)

Results are saved as JSON under benchmarks/results/.
"""

from __future__ import annotations

import json
import logging
import os
import random
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

_SYNTHETIC_PROMPTS = [
    "Tell me about neural networks.",
    "What is the capital of France?",
    "Explain gradient descent in simple terms.",
    "How does attention work in transformers?",
    "Describe the difference between supervised and unsupervised learning.",
    "What is the role of the tokenizer?",
    "Summarise the history of artificial intelligence.",
    "How do you fine-tune a language model?",
    "What is overfitting and how do you prevent it?",
    "Define the concept of backpropagation.",
    "What is a convolutional neural network?",
    "How does RLHF improve language models?",
    "Explain self-supervised learning.",
    "What makes a model production-grade?",
    "How do you evaluate a language model?",
]


def _get_memory_mb() -> float:
    """Return current RSS memory in MB (cross-platform, best-effort)."""
    try:
        import sys
        import resource  # Unix only

        usage = resource.getrusage(resource.RUSAGE_SELF)
        # Linux reports ru_maxrss in kB; macOS reports in bytes.
        if sys.platform == "darwin":
            return usage.ru_maxrss / (1024 * 1024)
        return usage.ru_maxrss / 1024
    except ImportError:
        pass
    try:
        import psutil  # type: ignore

        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    return 0.0


def _run_single(
    prompt: str,
    vocabulary: dict,
    reverse_vocabulary: dict,
    max_tokens: int,
    seed: int,
) -> tuple[str, float]:
    """Run inference on one prompt; return (response, elapsed_seconds)."""
    from victor_cli.inference import _simple_generate

    t0 = time.perf_counter()
    response = _simple_generate(prompt, vocabulary, reverse_vocabulary, max_tokens=max_tokens, seed=seed)
    elapsed = time.perf_counter() - t0
    return response, elapsed


def run_benchmark(
    checkpoint: Optional[str],
    num_prompts: int = 10,
    max_tokens: int = 64,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
) -> int:
    """Run inference benchmark and save results."""
    vocabulary: dict = {}
    reverse_vocabulary: dict = {}

    # Load vocabulary from checkpoint or default tokenizer.
    if checkpoint:
        ckpt_path = Path(checkpoint).expanduser().resolve()
        if ckpt_path.is_dir():
            candidates = list(ckpt_path.rglob("*tokenizer*.json")) + sorted(ckpt_path.rglob("epoch_*.json"))
            if candidates:
                ckpt_path = candidates[0]
        if ckpt_path.is_file():
            try:
                data = json.loads(ckpt_path.read_text(encoding="utf-8"))
                vocabulary = data.get("vocabulary", {})
                reverse_vocabulary = {str(k): v for k, v in data.get("reverse_vocabulary", {}).items()}
                logger.info("Loaded vocabulary (%d tokens) from %s", len(vocabulary), ckpt_path)
            except Exception as exc:
                logger.warning("Could not load checkpoint: %s", exc)
    else:
        default_tok = Path("victor_tokenizers") / "nlp_tokenizer.json"
        if default_tok.exists():
            data = json.loads(default_tok.read_text(encoding="utf-8"))
            vocabulary = data.get("vocabulary", {})
            reverse_vocabulary = {str(k): v for k, v in data.get("reverse_vocabulary", {}).items()}

    # Generate synthetic prompts.
    rng = random.Random(42)
    prompts = [rng.choice(_SYNTHETIC_PROMPTS) for _ in range(num_prompts)]

    # Warm-up pass (not timed).
    if vocabulary:
        _run_single(prompts[0], vocabulary, reverse_vocabulary, max_tokens, seed=99)

    # Timed runs.
    latencies: List[float] = []
    mem_before = _get_memory_mb()

    for i, prompt in enumerate(prompts):
        _, elapsed = _run_single(prompt, vocabulary, reverse_vocabulary, max_tokens, seed=i)
        latencies.append(elapsed)
        if verbose:
            logger.debug("prompt %d: %.4fs", i, elapsed)

    mem_after = _get_memory_mb()

    # Compute stats.
    n = len(latencies)
    total_tokens = n * max_tokens
    total_time = sum(latencies)
    throughput = total_tokens / total_time if total_time > 0 else 0.0
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checkpoint": str(checkpoint) if checkpoint else None,
        "num_prompts": n,
        "max_tokens": max_tokens,
        "vocab_size": len(vocabulary),
        "latency_mean_s": statistics.mean(latencies),
        "latency_median_s": statistics.median(latencies),
        "latency_min_s": min(latencies),
        "latency_max_s": max(latencies),
        "latency_stdev_s": statistics.stdev(latencies) if n > 1 else 0.0,
        "throughput_tokens_per_s": throughput,
        "total_time_s": total_time,
        "memory_before_mb": mem_before,
        "memory_after_mb": mem_after,
        "memory_delta_mb": mem_after - mem_before,
    }

    # Print summary.
    print("\n🔬 Benchmark Results")
    print(f"   prompts          : {n}")
    print(f"   max_tokens       : {max_tokens}")
    print(f"   vocab_size       : {len(vocabulary)}")
    print(f"   latency mean     : {results['latency_mean_s']:.4f}s")
    print(f"   latency median   : {results['latency_median_s']:.4f}s")
    print(f"   latency min/max  : {results['latency_min_s']:.4f}s / {results['latency_max_s']:.4f}s")
    print(f"   throughput       : {throughput:.1f} tokens/s")
    print(f"   memory delta     : {results['memory_delta_mb']:.1f} MB")

    # Save results.
    if output_dir is None:
        output_dir = Path("benchmarks") / "results"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    result_file = output_dir / f"benchmark_{ts}.json"
    result_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n   Results saved to : {result_file}")

    return 0
