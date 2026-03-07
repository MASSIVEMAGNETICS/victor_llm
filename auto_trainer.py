"""
auto_trainer.py - Automated Training Pipeline Orchestration
Part of the DataBlob Godmode Toolkit for Victor LLM

Features:
- Automatic model selection based on dataset characteristics
- Hyperparameter optimization integration
- Progressive training with checkpoint management
- Metrics tracking and visualization hooks
- Integration hooks for Victor LLM training backends
- Multi-GPU/distributed training support stubs
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

Record = Dict[str, Any]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TrainingConfig:
    """Hyperparameter and training configuration."""

    model_type: str = "auto"           # 'auto' | 'classification' | 'regression' | 'language_model' | 'embedding'
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    warmup_steps: int = 100
    max_steps: Optional[int] = None
    checkpoint_interval: int = 5       # Save checkpoint every N epochs
    early_stopping_patience: int = 5
    gradient_clip: float = 1.0
    device: str = "auto"               # 'auto' | 'cpu' | 'cuda' | 'mps'
    num_workers: int = 0
    seed: int = 42
    output_dir: str = "./checkpoints"
    run_id: str = ""
    # Fine-tuning / pretrained model options
    pretrained_model_path: Optional[str] = None   # Path to a pretrained .pt checkpoint
    freeze_embedding: bool = False                 # Freeze token & position embeddings
    freeze_layers: List[int] = field(default_factory=list)  # Transformer block indices to freeze
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.run_id:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            self.run_id = f"run-{ts}"


@dataclass
class TrainingMetrics:
    """Metrics snapshot for a single epoch."""

    epoch: int
    step: int
    train_loss: float
    val_loss: Optional[float] = None
    train_accuracy: Optional[float] = None
    val_accuracy: Optional[float] = None
    learning_rate: float = 0.0
    elapsed_seconds: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Checkpoint:
    """Metadata for a saved checkpoint."""

    path: str
    epoch: int
    step: int
    val_loss: Optional[float]
    config: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TrainingResult:
    """Final result of a training run."""

    run_id: str
    config: TrainingConfig
    metrics_history: List[TrainingMetrics]
    best_checkpoint: Optional[Checkpoint]
    total_epochs_run: int
    total_time_seconds: float
    stopped_early: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        last = self.metrics_history[-1] if self.metrics_history else None
        best_val = (
            min(
                (m.val_loss for m in self.metrics_history if m.val_loss is not None),
                default=None,
            )
        )
        return {
            "run_id": self.run_id,
            "epochs": self.total_epochs_run,
            "total_time_seconds": round(self.total_time_seconds, 2),
            "stopped_early": self.stopped_early,
            "final_train_loss": last.train_loss if last else None,
            "final_val_loss": last.val_loss if last else None,
            "best_val_loss": best_val,
            "best_checkpoint": self.best_checkpoint.path if self.best_checkpoint else None,
        }


# ---------------------------------------------------------------------------
# Model selector
# ---------------------------------------------------------------------------

class ModelSelector:
    """
    Select the most suitable model type based on dataset characteristics.
    """

    def select(
        self,
        dataset_info: Dict[str, Any],
    ) -> str:
        """
        Return a model type string based on dataset characteristics.

        *dataset_info* keys:
          - ``task_type``: 'classification' | 'regression' | 'language' | 'embedding'
          - ``num_classes``: int (for classification)
          - ``record_count``: int
          - ``field_count``: int
          - ``has_text``: bool
        """
        task = dataset_info.get("task_type", "").lower()

        if task == "classification":
            num_classes = dataset_info.get("num_classes", 2)
            record_count = dataset_info.get("record_count", 0)
            if dataset_info.get("has_text"):
                return "text_classification"
            if num_classes == 2:
                return "binary_classification"
            return "multiclass_classification"

        if task == "regression":
            return "regression"

        if task in ("language", "lm", "language_model"):
            return "language_model"

        if task == "embedding":
            return "embedding"

        # Fallback heuristics
        if dataset_info.get("has_text"):
            return "language_model"

        return "tabular_classification"


# ---------------------------------------------------------------------------
# Hyperparameter optimiser (simple grid/random search)
# ---------------------------------------------------------------------------

class HyperparamOptimizer:
    """Lightweight hyperparameter search (no external dependencies)."""

    def random_config(
        self,
        base_config: TrainingConfig,
        search_space: Optional[Dict[str, Any]] = None,
        seed: int = 0,
    ) -> TrainingConfig:
        """
        Return a TrainingConfig with hyperparams sampled from *search_space*.

        Default search_space samples learning_rate and batch_size.
        """
        import random as _random

        rng = _random.Random(seed)

        space = search_space or {
            "learning_rate": [1e-5, 5e-5, 1e-4, 5e-4, 1e-3],
            "batch_size": [16, 32, 64],
            "weight_decay": [0.0, 1e-5, 1e-4],
        }

        cfg_dict = asdict(base_config)
        for param, choices in space.items():
            if isinstance(choices, list):
                cfg_dict[param] = rng.choice(choices)
            elif isinstance(choices, tuple) and len(choices) == 2:
                lo, hi = choices
                cfg_dict[param] = lo + rng.random() * (hi - lo)

        # Ensure run_id is unique
        cfg_dict["run_id"] = f"hpo-{base_config.run_id}-seed{seed}"
        return TrainingConfig(**cfg_dict)

    def grid_configs(
        self,
        base_config: TrainingConfig,
        grid: Dict[str, List[Any]],
    ) -> List[TrainingConfig]:
        """Yield all grid combinations of hyperparameters."""
        import itertools

        keys = list(grid.keys())
        values = list(grid.values())
        configs = []
        for i, combo in enumerate(itertools.product(*values)):
            cfg_dict = asdict(base_config)
            for k, v in zip(keys, combo):
                cfg_dict[k] = v
            cfg_dict["run_id"] = f"grid-{base_config.run_id}-{i}"
            configs.append(TrainingConfig(**cfg_dict))
        return configs


# ---------------------------------------------------------------------------
# Checkpoint manager
# ---------------------------------------------------------------------------

class CheckpointManager:
    """Manage training checkpoints on disk."""

    def __init__(self, output_dir: Union[str, Path]) -> None:
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints: List[Checkpoint] = []

    def save(
        self,
        run_id: str,
        epoch: int,
        step: int,
        val_loss: Optional[float],
        config: TrainingConfig,
        model_state: Optional[Any] = None,
    ) -> Checkpoint:
        """
        Save a checkpoint.  If *model_state* is a dict, it is JSON-serialised.
        Otherwise a placeholder file is written.
        """
        ckpt_dir = self._dir / run_id
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        ckpt_path = ckpt_dir / f"epoch_{epoch:04d}.json"

        payload: Dict[str, Any] = {
            "run_id": run_id,
            "epoch": epoch,
            "step": step,
            "val_loss": val_loss,
            "config": asdict(config),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if isinstance(model_state, dict):
            payload["model_state"] = model_state

        ckpt_path.write_text(json.dumps(payload, indent=2, default=str))

        ckpt = Checkpoint(
            path=str(ckpt_path),
            epoch=epoch,
            step=step,
            val_loss=val_loss,
            config=asdict(config),
        )
        self._checkpoints.append(ckpt)
        logger.info("Checkpoint saved: %s (val_loss=%.4f)", ckpt_path, val_loss or 0)
        return ckpt

    def load(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load a checkpoint from disk."""
        return json.loads(Path(path).read_text())

    def best_checkpoint(self) -> Optional[Checkpoint]:
        """Return checkpoint with lowest validation loss."""
        with_loss = [c for c in self._checkpoints if c.val_loss is not None]
        if not with_loss:
            return self._checkpoints[-1] if self._checkpoints else None
        return min(with_loss, key=lambda c: c.val_loss)  # type: ignore[arg-type]

    def list_checkpoints(self) -> List[Checkpoint]:
        return list(self._checkpoints)


# ---------------------------------------------------------------------------
# Metrics tracker
# ---------------------------------------------------------------------------

class MetricsTracker:
    """Track and persist training metrics."""

    def __init__(self, output_dir: Union[str, Path], run_id: str) -> None:
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._run_id = run_id
        self._history: List[TrainingMetrics] = []
        self._callbacks: List[Callable[[TrainingMetrics], None]] = []

    def add_callback(self, fn: Callable[[TrainingMetrics], None]) -> None:
        self._callbacks.append(fn)

    def record(self, metrics: TrainingMetrics) -> None:
        self._history.append(metrics)
        for cb in self._callbacks:
            try:
                cb(metrics)
            except Exception as exc:
                logger.warning("Metrics callback error: %s", exc)
        self._flush()

    def _flush(self) -> None:
        path = self._dir / f"{self._run_id}_metrics.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(self._history[-1].to_dict(), default=str) + "\n")

    @property
    def history(self) -> List[TrainingMetrics]:
        return list(self._history)

    def best_epoch(self) -> Optional[int]:
        """Return epoch index with lowest val_loss."""
        with_loss = [(i, m.val_loss) for i, m in enumerate(self._history) if m.val_loss is not None]
        if not with_loss:
            return None
        return min(with_loss, key=lambda x: x[1])[0]


# ---------------------------------------------------------------------------
# Victor LLM training hook
# ---------------------------------------------------------------------------

class VictorTrainingHook:
    """
    Integration hook for the Victor LLM training infrastructure.
    Provides callbacks that bridge AutoTrainer events to the Victor backend.
    """

    def __init__(self, victor_core_path: Optional[str] = None) -> None:
        self._victor_path = victor_core_path
        self._backend_available = self._probe_backend()

    def _probe_backend(self) -> bool:
        """Check if Victor training backend is importable."""
        try:
            import importlib.util
            spec = importlib.util.find_spec("victor_core")
            return spec is not None
        except (ModuleNotFoundError, ValueError):
            return False

    def on_epoch_end(self, metrics: TrainingMetrics) -> None:
        if self._backend_available:
            try:
                from victor_core.brain import AsiCoreBrain  # type: ignore
                logger.debug("Victor hook: epoch %d, loss=%.4f", metrics.epoch, metrics.train_loss)
            except Exception as exc:
                logger.debug("Victor hook (on_epoch_end) skipped: %s", exc)

    def on_training_complete(self, result: TrainingResult) -> None:
        if self._backend_available:
            logger.info("Victor hook: training complete, run_id=%s", result.run_id)

    @property
    def available(self) -> bool:
        return self._backend_available


# ---------------------------------------------------------------------------
# Main AutoTrainer
# ---------------------------------------------------------------------------

class AutoTrainer:
    """
    Automated training pipeline orchestrator.

    Provides a model-agnostic training loop with:
    - Configurable hyperparameters
    - Checkpoint management
    - Metrics tracking
    - Early stopping
    - Victor LLM backend hooks
    - Custom training function injection

    Usage::

        trainer = AutoTrainer()

        def my_train_fn(batch, config):
            # return (train_loss, val_loss)
            return 0.5, 0.6

        result = trainer.train(
            train_records=train_data,
            val_records=val_data,
            train_fn=my_train_fn,
            config=TrainingConfig(epochs=10),
        )
    """

    def __init__(
        self,
        checkpoint_dir: Union[str, Path] = "./checkpoints",
        victor_hook: Optional[VictorTrainingHook] = None,
    ) -> None:
        self._ckpt_dir = Path(checkpoint_dir)
        self._victor_hook = victor_hook or VictorTrainingHook()
        self._model_selector = ModelSelector()
        self._hpo = HyperparamOptimizer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_model_type(self, dataset_info: Dict[str, Any]) -> str:
        """Auto-select model type from dataset characteristics."""
        return self._model_selector.select(dataset_info)

    def train(
        self,
        train_records: List[Record],
        val_records: List[Record],
        config: Optional[TrainingConfig] = None,
        train_fn: Optional[Callable[..., Tuple[float, float]]] = None,
        dataset_info: Optional[Dict[str, Any]] = None,
    ) -> TrainingResult:
        """
        Run the training loop.

        Parameters
        ----------
        train_records : training split
        val_records : validation split
        config : TrainingConfig
        train_fn : callable(batch, config) -> (train_loss, val_loss).
                   If None, a no-op stub is used (useful for pipeline testing).
        dataset_info : optional metadata for auto model selection
        """
        config = config or TrainingConfig()

        if dataset_info and config.model_type == "auto":
            config.model_type = self._model_selector.select(dataset_info)
            logger.info("Auto-selected model type: %s", config.model_type)

        ckpt_manager = CheckpointManager(self._ckpt_dir / config.run_id)
        metrics_tracker = MetricsTracker(self._ckpt_dir / config.run_id, config.run_id)
        metrics_tracker.add_callback(self._victor_hook.on_epoch_end)

        if train_fn is None:
            train_fn = self._stub_train_fn

        start_time = time.monotonic()
        step = 0
        best_val_loss: Optional[float] = None
        patience_counter = 0
        stopped_early = False

        max_epochs = config.epochs
        if config.max_steps is not None:
            steps_per_epoch = max(1, len(train_records) // config.batch_size)
            max_epochs = min(max_epochs, config.max_steps // steps_per_epoch + 1)

        for epoch in range(1, max_epochs + 1):
            epoch_start = time.monotonic()

            # Batch iteration stub
            batches = self._make_batches(train_records, config.batch_size)
            epoch_losses: List[float] = []
            epoch_val_loss: Optional[float] = None

            for batch in batches:
                try:
                    result = train_fn(batch, config)
                    if isinstance(result, (tuple, list)) and len(result) >= 2:
                        t_loss, v_loss = float(result[0]), float(result[1])
                    else:
                        t_loss = float(result)
                        v_loss = None
                except Exception as exc:
                    logger.error("train_fn error at epoch %d: %s", epoch, exc)
                    t_loss = float("inf")
                    v_loss = None
                epoch_losses.append(t_loss)
                if v_loss is not None:
                    epoch_val_loss = v_loss
                step += 1

                if config.max_steps and step >= config.max_steps:
                    break

            avg_train_loss = sum(epoch_losses) / len(epoch_losses) if epoch_losses else float("inf")

            # If no val_loss from train_fn, simulate one
            if epoch_val_loss is None and val_records:
                val_batches = self._make_batches(val_records, config.batch_size)
                val_losses: List[float] = []
                for vbatch in val_batches:
                    try:
                        vr = train_fn(vbatch, config)
                        vl = float(vr[0]) if isinstance(vr, (tuple, list)) else float(vr)
                        val_losses.append(vl)
                    except Exception:
                        pass
                epoch_val_loss = sum(val_losses) / len(val_losses) if val_losses else None

            elapsed = time.monotonic() - epoch_start
            metrics = TrainingMetrics(
                epoch=epoch,
                step=step,
                train_loss=avg_train_loss,
                val_loss=epoch_val_loss,
                learning_rate=config.learning_rate,
                elapsed_seconds=round(elapsed, 3),
            )
            metrics_tracker.record(metrics)

            logger.info(
                "[Epoch %d/%d] train_loss=%.4f val_loss=%s lr=%.2e",
                epoch,
                max_epochs,
                avg_train_loss,
                f"{epoch_val_loss:.4f}" if epoch_val_loss is not None else "N/A",
                config.learning_rate,
            )

            # Checkpointing
            if epoch % config.checkpoint_interval == 0 or epoch == max_epochs:
                ckpt_manager.save(
                    run_id=config.run_id,
                    epoch=epoch,
                    step=step,
                    val_loss=epoch_val_loss,
                    config=config,
                )

            # Early stopping
            if epoch_val_loss is not None:
                if best_val_loss is None or epoch_val_loss < best_val_loss:
                    best_val_loss = epoch_val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= config.early_stopping_patience:
                        logger.info("Early stopping triggered at epoch %d", epoch)
                        stopped_early = True
                        break

            if config.max_steps and step >= config.max_steps:
                break

        total_time = time.monotonic() - start_time
        best_ckpt = ckpt_manager.best_checkpoint()

        result = TrainingResult(
            run_id=config.run_id,
            config=config,
            metrics_history=metrics_tracker.history,
            best_checkpoint=best_ckpt,
            total_epochs_run=epoch,
            total_time_seconds=round(total_time, 2),
            stopped_early=stopped_early,
        )

        self._victor_hook.on_training_complete(result)

        logger.info(
            "Training complete: run_id=%s, epochs=%d, time=%.1fs",
            config.run_id,
            epoch,
            total_time,
        )
        return result

    def hpo_search(
        self,
        train_records: List[Record],
        val_records: List[Record],
        base_config: Optional[TrainingConfig] = None,
        search_space: Optional[Dict[str, Any]] = None,
        n_trials: int = 5,
        train_fn: Optional[Callable[..., Tuple[float, float]]] = None,
    ) -> Tuple[TrainingConfig, List[TrainingResult]]:
        """
        Random search hyperparameter optimisation.
        Returns (best_config, all_results).
        """
        base_config = base_config or TrainingConfig()
        results: List[TrainingResult] = []
        best_result: Optional[TrainingResult] = None
        best_val_loss = float("inf")

        for trial in range(n_trials):
            trial_cfg = self._hpo.random_config(base_config, search_space, seed=trial)
            logger.info("HPO trial %d/%d: lr=%.2e, batch=%d", trial + 1, n_trials, trial_cfg.learning_rate, trial_cfg.batch_size)
            r = self.train(train_records, val_records, trial_cfg, train_fn)
            results.append(r)

            trial_best = min(
                (m.val_loss for m in r.metrics_history if m.val_loss is not None),
                default=float("inf"),
            )
            if trial_best < best_val_loss:
                best_val_loss = trial_best
                best_result = r

        best_config = best_result.config if best_result else base_config
        logger.info("HPO complete. Best val_loss=%.4f", best_val_loss)
        return best_config, results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_batches(
        records: List[Record], batch_size: int
    ) -> List[List[Record]]:
        return [records[i: i + batch_size] for i in range(0, len(records), batch_size)]

    @staticmethod
    def _stub_train_fn(
        batch: List[Record], config: TrainingConfig
    ) -> Tuple[float, float]:
        """No-op training function – returns dummy decreasing loss."""
        import math as _math

        t = time.monotonic() % 1.0
        loss = 1.0 / (1.0 + t * len(batch) * 0.01 + _math.log1p(config.epochs))
        return loss, loss * 1.05
