"""
victor_cli.training – training pipeline backed by DataBlobGodmodeKit / AutoTrainer.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _load_config_file(path: str) -> Dict[str, Any]:
    """Load a YAML or JSON config file and return a flat dict."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        logger.error("Config file not found: %s", p)
        sys.exit(1)

    suffix = p.suffix.lower()
    raw = p.read_text(encoding="utf-8")

    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore

            return yaml.safe_load(raw) or {}
        except ImportError:
            logger.error("PyYAML is required to load .yaml config files.  pip install pyyaml")
            sys.exit(1)
    elif suffix == ".json":
        return json.loads(raw)
    elif suffix == ".toml":
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore  # backport
            except ImportError:
                logger.error("tomli/tomllib is required to load .toml config files.  pip install tomli")
                sys.exit(1)
        return tomllib.loads(raw)
    else:
        logger.error("Unsupported config format: %s", suffix)
        sys.exit(1)


def run_training(
    dataset_dir: Path,
    output_dir: Path,
    epochs: int = 5,
    batch_size: int = 32,
    lr: float = 1e-3,
    model_type: str = "auto",
    checkpoint: Optional[str] = None,
    config_file: Optional[str] = None,
    seed: int = 42,
    verbose: bool = False,
) -> int:
    """
    Run a full training cycle on the given dataset directory.

    Loads train.jsonl (+ valid.jsonl if present), builds a CompiledDataset via
    DataBlobGodmodeKit, and delegates to AutoTrainer.  Saves artifacts to
    output_dir/<run_id>/.
    """
    from victor_cli.dataset import load_split, prepare_dataset

    # Validate dataset first.
    rc = prepare_dataset(dataset_dir, verbose=verbose)
    if rc != 0:
        return rc

    # Merge optional config file on top of CLI defaults.
    cfg_overrides: Dict[str, Any] = {}
    if config_file:
        cfg_overrides = _load_config_file(config_file)
        logger.info("Loaded config overrides from %s: %s", config_file, list(cfg_overrides.keys()))

    epochs = int(cfg_overrides.get("epochs", epochs))
    batch_size = int(cfg_overrides.get("batch_size", batch_size))
    lr = float(cfg_overrides.get("lr", lr))
    model_type = str(cfg_overrides.get("model_type", model_type))
    seed = int(cfg_overrides.get("seed", seed))
    if "output_dir" in cfg_overrides:
        output_dir = Path(cfg_overrides["output_dir"]).expanduser().resolve()
    if "checkpoint" in cfg_overrides and checkpoint is None:
        checkpoint = cfg_overrides["checkpoint"]

    # Load training records.
    train_records = load_split(dataset_dir, "train")
    logger.info("Loaded %d training records.", len(train_records))

    has_valid = (dataset_dir / "valid.jsonl").exists()
    valid_records = load_split(dataset_dir, "valid") if has_valid else []
    if valid_records:
        logger.info("Loaded %d validation records.", len(valid_records))

    # Build dataset via DataBlobGodmodeKit (leverages SmartParser + StructEngine + DatasetCompiler).
    try:
        from data_blob_godmode_kit import DataBlobGodmodeKit, GodmodeConfig
    except ImportError as exc:
        logger.error("Could not import DataBlobGodmodeKit: %s", exc)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    godmode_cfg = GodmodeConfig(
        output_dir=str(output_dir),
        checkpoint_dir=str(checkpoint_dir),
    )
    kit = DataBlobGodmodeKit(config=godmode_cfg)

    # Ingest records.
    kit.ingest_records(train_records, source_name=str(dataset_dir))
    if valid_records:
        kit.ingest_records(valid_records, source_name=f"{dataset_dir}#valid")

    kit.structure()

    # Auto-detect label_field from dataset.yaml if present.
    label_field: Optional[str] = None
    meta_path = dataset_dir / "dataset.yaml"
    if meta_path.exists():
        try:
            import yaml  # type: ignore

            meta = yaml.safe_load(meta_path.read_text()) or {}
            label_field = meta.get("label_field")
            if label_field:
                logger.info("Using label_field '%s' from dataset.yaml.", label_field)
        except Exception:
            pass

    compiled = kit.compile_dataset(
        name=dataset_dir.name,
        label_field=label_field,
    )

    # Build AutoTrainer config.
    from auto_trainer import TrainingConfig

    train_cfg = TrainingConfig(
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=lr,
        model_type=model_type,
        output_dir=str(checkpoint_dir),
        seed=seed,
        pretrained_model_path=checkpoint,
    )

    logger.info(
        "Starting training: epochs=%d  batch=%d  lr=%g  model_type=%s  run_id=%s",
        epochs,
        batch_size,
        lr,
        model_type,
        train_cfg.run_id,
    )

    result = kit.train(compiled, config=train_cfg)

    # Build summary using the dataclass helper method (avoids field-name brittleness).
    summary = result.summary()

    # Save training result summary to output_dir.
    run_dir = output_dir / result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    summary_path = run_dir / "training_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    logger.info("Training complete.  run_id=%s", result.run_id)
    logger.info("Summary saved to %s", summary_path)

    print(f"\n✅ Training complete")
    print(f"   run_id      : {result.run_id}")
    print(f"   epochs      : {result.total_epochs_run}")
    final_loss = summary.get("final_train_loss")
    if final_loss is not None:
        print(f"   final loss  : {final_loss:.6f}")
    best_val = summary.get("best_val_loss")
    if best_val is not None:
        print(f"   best val    : {best_val:.6f}")
    print(f"   artifacts   : {run_dir}")
    return 0
