"""
victor_cli.dataset – dataset validation and preparation helpers.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

REQUIRED_SPLITS = {"train"}
OPTIONAL_SPLITS = {"valid", "test"}
ALL_SPLITS = REQUIRED_SPLITS | OPTIONAL_SPLITS


def _load_jsonl(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Load a JSONL file; return (records, errors)."""
    records: List[Dict[str, Any]] = []
    errors: List[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                errors.append(f"Line {lineno}: expected JSON object, got {type(obj).__name__}.")
            else:
                records.append(obj)
        except json.JSONDecodeError as exc:
            errors.append(f"Line {lineno}: {exc}")
    return records, errors


def _load_dataset_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Load dataset.yaml if present; return None if missing or unparseable."""
    try:
        import yaml  # type: ignore

        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        logger.debug("PyYAML not installed; skipping dataset.yaml validation.")
        return None
    except Exception as exc:
        logger.warning("Could not load dataset.yaml: %s", exc)
        return None


def prepare_dataset(dataset_dir: Path, verbose: bool = False) -> int:
    """
    Validate the layout of a dataset directory.

    Returns 0 on success, 1 if critical errors are found.
    """
    if not dataset_dir.exists():
        logger.error("Dataset directory does not exist: %s", dataset_dir)
        return 1

    logger.info("Preparing dataset: %s", dataset_dir)

    # Check required splits.
    missing = [s for s in REQUIRED_SPLITS if not (dataset_dir / f"{s}.jsonl").exists()]
    if missing:
        logger.error("Missing required split file(s): %s", ", ".join(f"{s}.jsonl" for s in missing))
        return 1

    # Optional metadata.
    meta_path = dataset_dir / "dataset.yaml"
    meta: Optional[Dict[str, Any]] = None
    if meta_path.exists():
        meta = _load_dataset_yaml(meta_path)
        if meta:
            logger.info("Loaded dataset.yaml: name=%s, task=%s", meta.get("name", "?"), meta.get("task", "?"))

    total_ok = 0
    total_errors = 0
    for split in ("train", "valid", "test"):
        split_path = dataset_dir / f"{split}.jsonl"
        if not split_path.exists():
            continue
        records, errors = _load_jsonl(split_path)
        total_ok += len(records)
        total_errors += len(errors)
        status = "✅" if not errors else "⚠️ "
        logger.info(
            "%s %s: %d records, %d error(s)",
            status,
            split,
            len(records),
            len(errors),
        )
        if errors and verbose:
            for err in errors[:10]:
                logger.warning("  %s", err)

    logger.info("Total records: %d  |  Parse errors: %d", total_ok, total_errors)
    if total_errors > 0:
        logger.warning("Dataset has %d parse error(s). Consider fixing before training.", total_errors)
    else:
        logger.info("Dataset validation passed ✅")
    return 0


def load_split(dataset_dir: Path, split: str) -> List[Dict[str, Any]]:
    """Load a split from a dataset directory; raises FileNotFoundError if absent."""
    split_path = dataset_dir / f"{split}.jsonl"
    if not split_path.exists():
        raise FileNotFoundError(f"Split '{split}' not found at {split_path}")
    records, errors = _load_jsonl(split_path)
    if errors:
        logger.warning("Split '%s' has %d parse error(s) (first: %s)", split, len(errors), errors[0])
    return records
