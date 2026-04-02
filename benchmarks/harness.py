#!/usr/bin/env python3
"""
benchmarks/harness.py – standalone benchmarking harness for Victor LLM.

Modes
-----
  inference   Measure latency, throughput and memory for text generation.
  training    Measure training speed on a tiny dataset.
  compare     Compare JSON result files stored in a directory.

Usage
-----
  python benchmarks/harness.py                            # inference, defaults
  python benchmarks/harness.py --prompts 50 --max-tokens 256
  python benchmarks/harness.py --checkpoint runs/my_run
  python benchmarks/harness.py --mode training --dataset datasets/example_dataset
  python benchmarks/harness.py --mode compare --compare benchmarks/results/
  victor benchmark --prompts 20 --max-tokens 128          # via victor CLI
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repo root is importable when run directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_memory_mb() -> float:
    """Return current RSS memory in MB (cross-platform, best-effort)."""
    try:
        import sys
        import resource  # Unix only

        usage = resource.getrusage(resource.RUSAGE_SELF)
        if sys.platform == "darwin":
            return usage.ru_maxrss / (1024 * 1024)
        return usage.ru_maxrss / 1024
    except ImportError:
        pass
    try:
        import os
        import psutil  # type: ignore

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    return 0.0


def _print_table(results: Dict[str, Any]) -> None:
    print("\n┌─────────────────────────────────────────────────────┐")
    print("│              Victor LLM Benchmark Results           │")
    print("├─────────────────────────────────────────┬───────────┤")
    rows = [
        ("Prompts", results.get("num_prompts", "?")),
        ("Max tokens", results.get("max_tokens", "?")),
        ("Vocab size", results.get("vocab_size", "?")),
        ("Latency mean", f"{results.get('latency_mean_s', 0):.4f}s"),
        ("Latency median", f"{results.get('latency_median_s', 0):.4f}s"),
        ("Latency min / max", f"{results.get('latency_min_s', 0):.4f}s / {results.get('latency_max_s', 0):.4f}s"),
        ("Latency stdev", f"{results.get('latency_stdev_s', 0):.4f}s"),
        ("Throughput", f"{results.get('throughput_tokens_per_s', 0):.1f} tok/s"),
        ("Memory delta", f"{results.get('memory_delta_mb', 0):.1f} MB"),
    ]
    for label, value in rows:
        print(f"│ {label:<39} │ {str(value):<9} │")
    print("└─────────────────────────────────────────┴───────────┘")


# ---------------------------------------------------------------------------
# Inference benchmark
# ---------------------------------------------------------------------------

def _bench_inference(
    checkpoint: Optional[str],
    num_prompts: int,
    max_tokens: int,
    output_dir: Path,
) -> Dict[str, Any]:
    from victor_cli.benchmark import run_benchmark, _SYNTHETIC_PROMPTS  # type: ignore[attr-defined]
    import random

    # Load vocabulary.
    vocabulary: dict = {}
    reverse_vocabulary: dict = {}

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
            except Exception:
                pass

    if not vocabulary:
        default_tok = REPO_ROOT / "victor_tokenizers" / "nlp_tokenizer.json"
        if default_tok.exists():
            data = json.loads(default_tok.read_text(encoding="utf-8"))
            vocabulary = data.get("vocabulary", {})
            reverse_vocabulary = {str(k): v for k, v in data.get("reverse_vocabulary", {}).items()}

    from victor_cli.inference import _simple_generate

    rng = random.Random(42)
    prompts = [rng.choice(_SYNTHETIC_PROMPTS) for _ in range(num_prompts)]

    # Warm-up.
    if vocabulary:
        _simple_generate(prompts[0], vocabulary, reverse_vocabulary, max_tokens, seed=99)

    latencies: List[float] = []
    mem_before = _get_memory_mb()

    for i, prompt in enumerate(prompts):
        t0 = time.perf_counter()
        _simple_generate(prompt, vocabulary, reverse_vocabulary, max_tokens, seed=i)
        latencies.append(time.perf_counter() - t0)

    mem_after = _get_memory_mb()
    n = len(latencies)
    total_tokens = n * max_tokens
    total_time = sum(latencies)

    results: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "inference",
        "checkpoint": str(checkpoint) if checkpoint else None,
        "num_prompts": n,
        "max_tokens": max_tokens,
        "vocab_size": len(vocabulary),
        "latency_mean_s": statistics.mean(latencies),
        "latency_median_s": statistics.median(latencies),
        "latency_min_s": min(latencies),
        "latency_max_s": max(latencies),
        "latency_stdev_s": statistics.stdev(latencies) if n > 1 else 0.0,
        "throughput_tokens_per_s": total_tokens / total_time if total_time > 0 else 0.0,
        "total_time_s": total_time,
        "memory_before_mb": mem_before,
        "memory_after_mb": mem_after,
        "memory_delta_mb": mem_after - mem_before,
    }
    return results


# ---------------------------------------------------------------------------
# Training benchmark
# ---------------------------------------------------------------------------

def _bench_training(dataset: str, epochs: int, output_dir: Path) -> Dict[str, Any]:
    from victor_cli.training import run_training

    dataset_dir = Path(dataset).expanduser().resolve()
    if not dataset_dir.exists():
        print(f"Dataset not found: {dataset_dir}")
        sys.exit(1)

    with tempfile.TemporaryDirectory(prefix="victor_bench_train_") as tmp:
        t0 = time.perf_counter()
        rc = run_training(
            dataset_dir=dataset_dir,
            output_dir=Path(tmp) / "runs",
            epochs=epochs,
            batch_size=4,
            seed=0,
        )
        elapsed = time.perf_counter() - t0

    if rc != 0:
        print("Training benchmark failed.")
        sys.exit(1)

    results: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "training",
        "dataset": str(dataset_dir),
        "epochs": epochs,
        "total_time_s": elapsed,
        "time_per_epoch_s": elapsed / epochs if epochs else 0.0,
    }
    return results


# ---------------------------------------------------------------------------
# Compare benchmark results
# ---------------------------------------------------------------------------

def _compare(results_dir: Path) -> None:
    files = sorted(results_dir.glob("benchmark_*.json"))
    if not files:
        print(f"No benchmark result files found in {results_dir}")
        return

    print(f"\nFound {len(files)} result file(s) in {results_dir}\n")
    header = f"{'Timestamp':<26} {'Mode':<12} {'Prompts':>8} {'Mean Latency':>14} {'Throughput':>14} {'ΔMem MB':>9}"
    print(header)
    print("-" * len(header))

    for f in files:
        try:
            d = json.loads(f.read_text())
            ts = d.get("timestamp", f.stem)[:25]
            mode = d.get("mode", "?")[:10]
            n = d.get("num_prompts", "-")
            lat = f"{d.get('latency_mean_s', 0):.4f}s"
            thr = f"{d.get('throughput_tokens_per_s', 0):.1f} t/s"
            mem = f"{d.get('memory_delta_mb', 0):.1f}"
            print(f"{ts:<26} {mode:<12} {str(n):>8} {lat:>14} {thr:>14} {mem:>9}")
        except Exception as exc:
            print(f"  Could not parse {f.name}: {exc}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Victor LLM Benchmarking Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--mode", choices=["inference", "training", "compare"], default="inference")
    p.add_argument("--checkpoint", metavar="PATH", help="Checkpoint to benchmark.")
    p.add_argument("--prompts", type=int, default=10, metavar="N", help="Number of synthetic prompts (inference mode).")
    p.add_argument("--max-tokens", type=int, default=64, help="Tokens per generation (inference mode).")
    p.add_argument("--dataset", default="datasets/example_dataset", metavar="DIR", help="Dataset directory (training mode).")
    p.add_argument("--epochs", type=int, default=1, help="Epochs (training mode, default: 1).")
    p.add_argument("--output-dir", metavar="DIR", default=str(REPO_ROOT / "benchmarks" / "results"), help="Where to save JSON results.")
    p.add_argument("--compare", metavar="DIR", help="Compare results in this directory (sets --mode compare).")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.compare:
        _compare(Path(args.compare))
        return 0

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "training":
        results = _bench_training(args.dataset, args.epochs, output_dir)
    else:
        results = _bench_inference(args.checkpoint, args.prompts, args.max_tokens, output_dir)

    _print_table(results)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_file = output_dir / f"benchmark_{ts}.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults saved to: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
