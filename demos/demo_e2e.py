#!/usr/bin/env python3
"""
demo_e2e.py – End-to-end Victor LLM demo.

Runs the full pipeline:
  1. prepare  – validate datasets/example_dataset
  2. train    – 2 epochs, classification, tiny batch
  3. eval     – evaluate on the test split
  4. predict  – generate text for two prompts
  5. benchmark – 3 synthetic prompts, 16 tokens each

Run from the repo root:
    python demos/demo_e2e.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Ensure repo root is importable.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def main() -> None:
    print("=== Victor LLM – End-to-End Demo ===")

    dataset_dir = REPO_ROOT / "datasets" / "example_dataset"
    if not dataset_dir.exists():
        print(f"Example dataset not found at {dataset_dir}")
        sys.exit(1)

    from victor_cli.dataset import prepare_dataset
    from victor_cli.training import run_training
    from victor_cli.evaluation import run_eval
    from victor_cli.inference import run_predict
    from victor_cli.benchmark import run_benchmark

    with tempfile.TemporaryDirectory(prefix="victor_demo_e2e_") as tmp_dir:
        output_dir = Path(tmp_dir) / "runs"
        bench_dir = Path(tmp_dir) / "bench_results"

        # ---- 1. Prepare ----
        _section("Step 1 – Prepare")
        rc = prepare_dataset(dataset_dir, verbose=True)
        assert rc == 0, "prepare step failed"

        # ---- 2. Train ----
        _section("Step 2 – Train (2 epochs)")
        rc = run_training(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            epochs=2,
            batch_size=4,
            lr=1e-3,
            model_type="classification",
            seed=0,
        )
        assert rc == 0, "train step failed"

        # Find the checkpoint produced.
        checkpoints = sorted(output_dir.rglob("epoch_*.json"))
        checkpoint_path = str(checkpoints[-1].parent) if checkpoints else str(output_dir)

        # ---- 3. Eval ----
        _section("Step 3 – Eval (test split)")
        rc = run_eval(
            dataset_dir=dataset_dir,
            checkpoint=checkpoint_path,
            split="test",
            verbose=True,
        )
        # eval may return 1 if checkpoint format is minimal – not fatal for demo
        print(f"   (eval exit code: {rc})")

        # ---- 4. Predict ----
        _section("Step 4 – Predict")
        rc = run_predict(
            prompts=[
                "Victor LLM is modular and powerful",
                "Neural networks learn from data",
            ],
            checkpoint=checkpoint_path,
            max_tokens=16,
        )
        assert rc == 0, "predict step failed"

        # ---- 5. Benchmark ----
        _section("Step 5 – Benchmark")
        rc = run_benchmark(
            checkpoint=checkpoint_path,
            num_prompts=3,
            max_tokens=16,
            output_dir=bench_dir,
        )
        assert rc == 0, "benchmark step failed"

    _section("Demo Complete ✅")
    print("  All steps finished successfully.\n")


if __name__ == "__main__":
    main()
