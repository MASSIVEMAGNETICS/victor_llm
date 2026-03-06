"""
data_blob_godmode_kit.py - Main DataBlob Godmode Toolkit
Part of the Victor LLM ecosystem

High-level orchestrator integrating:
  - SmartParser        (multi-format data ingestion)
  - StructEngine       (intelligent data structuring)
  - DatasetCompiler    (dataset compilation & export)
  - AutoTrainer        (automated training pipeline)
  - AnalyticsDashboard (visual monitoring)

Usage::

    from data_blob_godmode_kit import DataBlobGodmodeKit

    kit = DataBlobGodmodeKit(output_dir="./godmode_output")

    # Ingest
    kit.ingest_file("data.json")
    kit.ingest_bytes(raw_bytes, hint="data.csv")

    # Compile dataset
    dataset = kit.compile_dataset(name="my_dataset", label_field="label")

    # Train
    result = kit.train(dataset, config=None, train_fn=my_fn)

    # Analytics
    kit.dashboard.print_summary()
    kit.dashboard.save_html("report.html")
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from smart_parser import DataFormat, ParseResult, SmartParser
from struct_engine import StructEngine, StructuredDataset
from dataset_compiler import (
    CompiledDataset,
    DatasetCompiler,
    MergeStrategy,
    SplitConfig,
)
from auto_trainer import AutoTrainer, TrainingConfig, TrainingResult, VictorTrainingHook
from analytics_dashboard import AnalyticsDashboard

logger = logging.getLogger(__name__)

# Configure basic logging if no handlers are set
if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

Record = Dict[str, Any]


# ---------------------------------------------------------------------------
# Kit configuration
# ---------------------------------------------------------------------------

class GodmodeConfig:
    """Global configuration for the DataBlob Godmode Toolkit."""

    def __init__(
        self,
        output_dir: Union[str, Path] = "./godmode_output",
        default_export_format: str = "jsonl",
        log_level: int = logging.INFO,
        dashboard_port: int = 8787,
        checkpoint_dir: Optional[Union[str, Path]] = None,
        seed: int = 42,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.default_export_format = default_export_format
        self.log_level = log_level
        self.dashboard_port = dashboard_port
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else self.output_dir / "checkpoints"
        self.seed = seed


# ---------------------------------------------------------------------------
# Main kit
# ---------------------------------------------------------------------------

class DataBlobGodmodeKit:
    """
    All-in-one DataBlob Godmode Toolkit.

    Orchestrates data ingestion → structuring → dataset compilation →
    automated training → visual analytics.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        output_dir: Union[str, Path] = "./godmode_output",
        config: Optional[GodmodeConfig] = None,
    ) -> None:
        self._config = config or GodmodeConfig(output_dir=output_dir)
        self._config.output_dir.mkdir(parents=True, exist_ok=True)
        self._config.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        logging.getLogger().setLevel(self._config.log_level)

        # Components
        self._parser = SmartParser()
        self._struct_engine = StructEngine()
        self._compiler = DatasetCompiler()
        self._trainer = AutoTrainer(
            checkpoint_dir=self._config.checkpoint_dir,
            victor_hook=VictorTrainingHook(),
        )
        self._dashboard = AnalyticsDashboard()

        # State
        self._raw_sources: List[ParseResult] = []
        self._all_records: List[Record] = []
        self._structured: Optional[StructuredDataset] = None
        self._compiled: Optional[CompiledDataset] = None
        self._last_train_result: Optional[TrainingResult] = None

        logger.info("DataBlobGodmodeKit v%s initialised. Output: %s", self.VERSION, self._config.output_dir)

    # ------------------------------------------------------------------
    # Properties (read-only access to components)
    # ------------------------------------------------------------------

    @property
    def parser(self) -> SmartParser:
        return self._parser

    @property
    def struct_engine(self) -> StructEngine:
        return self._struct_engine

    @property
    def compiler(self) -> DatasetCompiler:
        return self._compiler

    @property
    def trainer(self) -> AutoTrainer:
        return self._trainer

    @property
    def dashboard(self) -> AnalyticsDashboard:
        return self._dashboard

    @property
    def records(self) -> List[Record]:
        return list(self._all_records)

    @property
    def structured_dataset(self) -> Optional[StructuredDataset]:
        return self._structured

    @property
    def compiled_dataset(self) -> Optional[CompiledDataset]:
        return self._compiled

    @property
    def last_training_result(self) -> Optional[TrainingResult]:
        return self._last_train_result

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest_file(
        self,
        path: Union[str, Path],
        fmt: Optional[DataFormat] = None,
    ) -> ParseResult:
        """Parse a file and add its records to the internal pool."""
        result = self._parser.parse_file(path, format_hint=fmt)
        self._raw_sources.append(result)
        self._all_records.extend(result.records)
        logger.info(
            "Ingested %d records from '%s' (format=%s, errors=%d)",
            len(result.records), path, result.format.name, len(result.errors),
        )
        if result.errors:
            for err in result.errors[:5]:
                logger.warning("Parse warning (%s): %s", Path(path).name, err)
        return result

    def ingest_bytes(
        self,
        data: bytes,
        hint: str = "",
        fmt: Optional[DataFormat] = None,
    ) -> ParseResult:
        """Parse raw bytes and add records to the internal pool."""
        result = self._parser.parse_bytes(data, hint=hint, format_hint=fmt)
        self._raw_sources.append(result)
        self._all_records.extend(result.records)
        logger.info(
            "Ingested %d records from bytes (hint=%r, format=%s)",
            len(result.records), hint, result.format.name,
        )
        return result

    def ingest_records(self, records: List[Record], source_name: str = "manual") -> None:
        """Add pre-parsed records directly."""
        self._all_records.extend(records)
        logger.info("Ingested %d records from %r", len(records), source_name)

    def stream_file(self, path: Union[str, Path], fmt: Optional[DataFormat] = None):
        """Stream records from a large file (generator)."""
        return self._parser.stream_file(path, format_hint=fmt)

    def clear_records(self) -> None:
        """Reset the internal record pool."""
        self._raw_sources.clear()
        self._all_records.clear()
        self._structured = None
        self._compiled = None
        logger.info("Record pool cleared.")

    # ------------------------------------------------------------------
    # Structuring
    # ------------------------------------------------------------------

    def structure(
        self,
        records: Optional[List[Record]] = None,
        source_name: str = "dataset",
    ) -> StructuredDataset:
        """
        Run the StructEngine over all ingested records (or *records* if given).
        Caches and returns the :class:`StructuredDataset`.
        """
        recs = records if records is not None else self._all_records
        self._structured = self._struct_engine.structure(recs, source_name)

        # Update dashboard
        null_pcts = self._structured.metadata.get("null_percentages", {})
        self._dashboard.update_dataset(
            field_stats=self._structured.field_stats,
            null_pcts=null_pcts,
            quality_score=self._structured.quality_score,
            record_count=len(recs),
            anomaly_count=len(self._structured.anomalies),
        )
        return self._structured

    def normalize(
        self,
        records: Optional[List[Record]] = None,
        strategies: Optional[Dict[str, str]] = None,
    ) -> List[Record]:
        """Normalise numeric fields in *records* (or all ingested records)."""
        recs = records if records is not None else self._all_records
        return self._struct_engine.normalize(recs, strategies)

    # ------------------------------------------------------------------
    # Dataset compilation
    # ------------------------------------------------------------------

    def compile_dataset(
        self,
        name: str = "dataset",
        records: Optional[List[Record]] = None,
        split_config: Optional[SplitConfig] = None,
        label_field: Optional[str] = None,
        balance_strategy: Optional[str] = None,
        merge_strategy: str = MergeStrategy.CONCAT,
        sources: Optional[List[List[Record]]] = None,
    ) -> CompiledDataset:
        """
        Compile a dataset from ingested records (or provided *records*/*sources*).

        Parameters
        ----------
        name : dataset name
        records : explicit records list (overrides ingested pool)
        split_config : SplitConfig (defaults to 70/15/15)
        label_field : stratify / balance field
        balance_strategy : 'oversample' | 'undersample' | None
        merge_strategy : how to merge multiple sources
        sources : explicit list-of-record-lists to fuse (overrides pool)
        """
        if sources:
            recs = self._compiler.fuse(sources, merge_strategy)
        elif records is not None:
            recs = records
        else:
            recs = self._all_records

        struct_info: Dict[str, Any] = {}
        if self._structured:
            struct_info = {
                "quality_score": self._structured.quality_score,
                "anomaly_count": len(self._structured.anomalies),
                "field_types": {k: v.name for k, v in self._structured.field_types.items()},
            }

        self._compiled = self._compiler.compile(
            records=recs,
            name=name,
            split_config=split_config,
            label_field=label_field,
            balance_strategy=balance_strategy,
            source_info={"sources_count": len(self._raw_sources), **struct_info},
        )

        # Update dashboard manifest
        self._dashboard.update_dataset(
            field_stats=self._structured.field_stats if self._structured else [],
            null_pcts=self._structured.metadata.get("null_percentages", {}) if self._structured else {},
            quality_score=self._structured.quality_score if self._structured else 0.0,
            record_count=len(recs),
            anomaly_count=len(self._structured.anomalies) if self._structured else 0,
            manifest=self._compiled.manifest,
        )

        logger.info(
            "Dataset '%s' compiled (v%s): %d train / %d val / %d test",
            name, self._compiled.version,
            len(self._compiled.split.train),
            len(self._compiled.split.val),
            len(self._compiled.split.test),
        )
        return self._compiled

    def export_dataset(
        self,
        dataset: Optional[CompiledDataset] = None,
        output_dir: Optional[Union[str, Path]] = None,
        fmt: Optional[str] = None,
    ) -> Dict[str, Path]:
        """Export a compiled dataset.  Uses last compiled dataset if not provided."""
        ds = dataset or self._compiled
        if ds is None:
            raise RuntimeError("No dataset to export. Call compile_dataset() first.")
        out = Path(output_dir) if output_dir else self._config.output_dir / "datasets"
        export_fmt = fmt or self._config.default_export_format
        return self._compiler.export(ds, out, export_fmt)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        dataset: Optional[CompiledDataset] = None,
        config: Optional[TrainingConfig] = None,
        train_fn: Optional[Callable[..., Tuple[float, float]]] = None,
        dataset_info: Optional[Dict[str, Any]] = None,
    ) -> TrainingResult:
        """
        Run automated training on a compiled dataset.

        Parameters
        ----------
        dataset : CompiledDataset (uses last compiled if None)
        config : TrainingConfig
        train_fn : user-supplied training function
        dataset_info : hint dict for auto model selection
        """
        ds = dataset or self._compiled
        if ds is None:
            raise RuntimeError("No compiled dataset. Call compile_dataset() first.")

        train_records = ds.split.train
        val_records = ds.split.val

        if dataset_info is None and self._structured:
            has_text = any(
                v.name == "TEXTUAL"
                for v in self._structured.field_types.values()
            )
            dataset_info = {
                "record_count": len(train_records),
                "field_count": len(self._structured.field_types),
                "has_text": has_text,
            }

        result = self._trainer.train(
            train_records=train_records,
            val_records=val_records,
            config=config,
            train_fn=train_fn,
            dataset_info=dataset_info,
        )
        self._last_train_result = result

        # Update dashboard training history
        history = [m.to_dict() for m in result.metrics_history]
        self._dashboard.update_training(history)

        return result

    def hpo_search(
        self,
        n_trials: int = 5,
        base_config: Optional[TrainingConfig] = None,
        search_space: Optional[Dict[str, Any]] = None,
        train_fn: Optional[Callable[..., Tuple[float, float]]] = None,
        dataset: Optional[CompiledDataset] = None,
    ) -> Tuple[TrainingConfig, List[TrainingResult]]:
        """Hyperparameter optimisation search over the compiled dataset."""
        ds = dataset or self._compiled
        if ds is None:
            raise RuntimeError("No compiled dataset. Call compile_dataset() first.")
        return self._trainer.hpo_search(
            train_records=ds.split.train,
            val_records=ds.split.val,
            base_config=base_config,
            search_space=search_space,
            n_trials=n_trials,
            train_fn=train_fn,
        )

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def print_report(self) -> None:
        """Print a full analytics report to stdout."""
        self._dashboard.print_summary()
        if self._last_train_result:
            print("\nTraining Summary:")
            summary = self._last_train_result.summary()
            for k, v in summary.items():
                print(f"  {k}: {v}")

    def save_report(
        self,
        path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """Save an HTML report to disk."""
        out = Path(path) if path else self._config.output_dir / "report.html"
        return self._dashboard.save_html(out)

    def serve_dashboard(self, port: Optional[int] = None) -> None:
        """Start the web dashboard server."""
        self._dashboard.serve(port=port or self._config.dashboard_port)

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def run_pipeline(
        self,
        files: Optional[List[Union[str, Path]]] = None,
        records: Optional[List[Record]] = None,
        dataset_name: str = "godmode_dataset",
        label_field: Optional[str] = None,
        balance_strategy: Optional[str] = None,
        split_config: Optional[SplitConfig] = None,
        export_fmt: Optional[str] = None,
        train_config: Optional[TrainingConfig] = None,
        train_fn: Optional[Callable[..., Tuple[float, float]]] = None,
        run_training: bool = True,
        save_report: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute the full data → structure → compile → train → report pipeline.

        Parameters
        ----------
        files : paths to input files to ingest
        records : pre-parsed records to use instead
        dataset_name : name for the compiled dataset
        label_field : classification target field
        balance_strategy : 'oversample' | 'undersample' | None
        split_config : train/val/test split ratios
        export_fmt : export format (jsonl, csv, json, huggingface…)
        train_config : AutoTrainer configuration
        train_fn : custom training function
        run_training : whether to run the training step
        save_report : whether to save an HTML report

        Returns
        -------
        dict with keys: dataset, training_result, export_paths, report_path
        """
        logger.info("Starting DataBlob Godmode pipeline …")

        # 1. Ingest
        if files:
            for f in files:
                self.ingest_file(f)
        if records:
            self.ingest_records(records, "pipeline_input")

        # 2. Structure
        structured = self.structure(source_name=dataset_name)
        logger.info("Structuring complete. Quality: %.1f/100", structured.quality_score)

        # 3. Compile
        compiled = self.compile_dataset(
            name=dataset_name,
            label_field=label_field,
            balance_strategy=balance_strategy,
            split_config=split_config,
        )

        # 4. Export
        export_paths = self.export_dataset(
            compiled,
            fmt=export_fmt or self._config.default_export_format,
        )

        # 5. Train
        train_result = None
        if run_training:
            train_result = self.train(compiled, config=train_config, train_fn=train_fn)

        # 6. Report
        report_path = None
        if save_report:
            report_path = self.save_report()

        logger.info("Pipeline complete.")
        return {
            "dataset": compiled,
            "training_result": train_result,
            "export_paths": {k: str(v) for k, v in export_paths.items()},
            "report_path": str(report_path) if report_path else None,
        }

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def save_state(self, path: Optional[Union[str, Path]] = None) -> Path:
        """Save kit state (records + manifest) to disk as JSON."""
        out = Path(path) if path else self._config.output_dir / "kit_state.json"
        state = {
            "version": self.VERSION,
            "record_count": len(self._all_records),
            "source_count": len(self._raw_sources),
            "compiled_dataset": self._compiled.manifest if self._compiled else None,
            "training_result": self._last_train_result.summary() if self._last_train_result else None,
        }
        out.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        logger.info("Kit state saved to %s", out)
        return out

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DataBlobGodmodeKit(v{self.VERSION}, "
            f"records={len(self._all_records)}, "
            f"output={self._config.output_dir})"
        )
