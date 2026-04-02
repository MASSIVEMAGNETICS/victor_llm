"""
victor_cli.evaluation – evaluate a checkpoint on a dataset split.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def run_eval(
    dataset_dir: Path,
    checkpoint: str,
    split: str = "test",
    verbose: bool = False,
) -> int:
    """
    Evaluate a saved AutoTrainer checkpoint against a dataset split.

    Loads the checkpoint JSON produced by AutoTrainer and reports metrics
    stored in the checkpoint metadata.  For richer evaluation, plug in a
    custom model evaluation function.
    """
    from victor_cli.dataset import load_split

    # Load evaluation records.
    try:
        records = load_split(dataset_dir, split)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1

    if not records:
        logger.error("Split '%s' is empty.", split)
        return 1

    logger.info("Loaded %d records from split '%s'.", len(records), split)

    # Resolve checkpoint.
    ckpt_path = Path(checkpoint).expanduser().resolve()
    if not ckpt_path.exists():
        logger.error("Checkpoint not found: %s", ckpt_path)
        return 1

    # If a directory was passed, look for the last epoch checkpoint.
    if ckpt_path.is_dir():
        candidates = sorted(ckpt_path.rglob("epoch_*.json"))
        if not candidates:
            logger.error("No epoch checkpoint files found in %s", ckpt_path)
            return 1
        ckpt_path = candidates[-1]
        logger.info("Using checkpoint: %s", ckpt_path)

    # Load checkpoint metadata (produced by AutoTrainer).
    try:
        ckpt_meta: Dict[str, Any] = json.loads(ckpt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Could not read checkpoint file: %s", exc)
        return 1

    # Extract metrics from checkpoint metadata.
    metrics: Dict[str, Any] = {
        "split": split,
        "num_records": len(records),
        "checkpoint_epoch": ckpt_meta.get("epoch"),
        "checkpoint_step": ckpt_meta.get("step"),
        "train_loss": ckpt_meta.get("train_loss"),
        "val_loss": ckpt_meta.get("val_loss"),
    }

    print(f"\n📊 Evaluation results  (split={split})")
    print(f"   checkpoint : {ckpt_path}")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"   {key:<20}: {value:.6f}")
        elif value is not None:
            print(f"   {key:<20}: {value}")

    return 0
