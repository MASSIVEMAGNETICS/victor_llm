#!/usr/bin/env python3
"""
demo_finetune.py – Fine-tuning demo using datasets/example_dataset.

Trains a classification model for 2 epochs on the example dataset and
prints the training summary.  No GPU or internet access required.

Run from the repo root:
    python demos/demo_finetune.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Ensure repo root is importable.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    print("=== Victor LLM – Fine-tuning Demo ===\n")

    from victor_cli.training import run_training

    dataset_dir = REPO_ROOT / "datasets" / "example_dataset"
    if not dataset_dir.exists():
        print(f"Example dataset not found at {dataset_dir}")
        sys.exit(1)

    with tempfile.TemporaryDirectory(prefix="victor_demo_finetune_") as tmp_dir:
        output_dir = Path(tmp_dir) / "runs"
        print(f"Dataset  : {dataset_dir}")
        print(f"Output   : {output_dir}\n")

        rc = run_training(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            epochs=2,
            batch_size=4,
            lr=1e-3,
            model_type="classification",
            seed=42,
        )

    if rc == 0:
        print("\nDemo complete ✅")
    else:
        print("\nDemo encountered errors ❌")
        sys.exit(rc)


if __name__ == "__main__":
    main()
