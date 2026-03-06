"""
dataset_compiler.py - Smart Dataset Compiler
Part of the DataBlob Godmode Toolkit for Victor LLM

Features:
- Multi-source data fusion and merge strategies
- Automatic train/val/test split generation
- Class balance detection and sampling strategies
- Dataset versioning and tracking
- Export to multiple ML framework formats
- Dataset manifest generation with statistics
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

Record = Dict[str, Any]


# ---------------------------------------------------------------------------
# Split configuration
# ---------------------------------------------------------------------------

class SplitConfig:
    """Configuration for train/val/test splitting."""

    def __init__(
        self,
        train: float = 0.7,
        val: float = 0.15,
        test: float = 0.15,
        stratify_field: Optional[str] = None,
        shuffle: bool = True,
        seed: int = 42,
    ) -> None:
        total = train + val + test
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"train+val+test must sum to 1.0, got {total:.4f}")
        self.train = train
        self.val = val
        self.test = test
        self.stratify_field = stratify_field
        self.shuffle = shuffle
        self.seed = seed


# ---------------------------------------------------------------------------
# Dataset split result
# ---------------------------------------------------------------------------

class DatasetSplit:
    """Holds train/val/test record lists."""

    def __init__(
        self,
        train: List[Record],
        val: List[Record],
        test: List[Record],
    ) -> None:
        self.train = train
        self.val = val
        self.test = test

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DatasetSplit(train={len(self.train)}, "
            f"val={len(self.val)}, test={len(self.test)})"
        )

    @property
    def total(self) -> int:
        return len(self.train) + len(self.val) + len(self.test)


# ---------------------------------------------------------------------------
# Merge strategies
# ---------------------------------------------------------------------------

class MergeStrategy:
    UNION = "union"       # All records from all sources (may have schema gaps)
    INTERSECTION = "intersection"  # Only fields present in ALL sources
    CONCAT = "concat"     # Simple concatenation (default)

    ALL = {UNION, INTERSECTION, CONCAT}


# ---------------------------------------------------------------------------
# Compiled dataset container
# ---------------------------------------------------------------------------

class CompiledDataset:
    """A compiled, version-tracked dataset ready for ML training."""

    def __init__(
        self,
        name: str,
        split: DatasetSplit,
        manifest: Dict[str, Any],
        version: str = "",
    ) -> None:
        self.name = name
        self.split = split
        self.manifest = manifest
        self.version = version or self._generate_version(split)

    @staticmethod
    def _generate_version(split: DatasetSplit) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        content_hash = hashlib.md5(
            json.dumps(
                [split.train[:5], split.val[:5], split.test[:5]],
                default=str,
                sort_keys=True,
            ).encode()
        ).hexdigest()[:8]
        return f"{ts}-{content_hash}"

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CompiledDataset(name={self.name!r}, version={self.version!r}, "
            f"total={self.split.total})"
        )


# ---------------------------------------------------------------------------
# Splitter
# ---------------------------------------------------------------------------

class Splitter:
    """Split records into train/val/test sets."""

    def split(
        self,
        records: List[Record],
        config: SplitConfig,
    ) -> DatasetSplit:
        if not records:
            return DatasetSplit([], [], [])

        rng = random.Random(config.seed)

        if config.stratify_field:
            return self._stratified_split(records, config, rng)
        return self._random_split(records, config, rng)

    @staticmethod
    def _random_split(
        records: List[Record],
        config: SplitConfig,
        rng: random.Random,
    ) -> DatasetSplit:
        data = list(records)
        if config.shuffle:
            rng.shuffle(data)

        n = len(data)
        n_train = int(n * config.train)
        n_val = int(n * config.val)

        return DatasetSplit(
            train=data[:n_train],
            val=data[n_train: n_train + n_val],
            test=data[n_train + n_val:],
        )

    @staticmethod
    def _stratified_split(
        records: List[Record],
        config: SplitConfig,
        rng: random.Random,
    ) -> DatasetSplit:
        """Stratify by config.stratify_field so each split mirrors class distribution."""
        field = config.stratify_field
        buckets: Dict[Any, List[Record]] = {}
        for rec in records:
            label = rec.get(field, "_missing")
            buckets.setdefault(label, []).append(rec)

        train: List[Record] = []
        val: List[Record] = []
        test: List[Record] = []

        for label_records in buckets.values():
            sub = list(label_records)
            if config.shuffle:
                rng.shuffle(sub)
            n = len(sub)
            n_train = max(1, int(n * config.train))
            n_val = max(0, int(n * config.val))
            train.extend(sub[:n_train])
            val.extend(sub[n_train: n_train + n_val])
            test.extend(sub[n_train + n_val:])

        if config.shuffle:
            rng.shuffle(train)
            rng.shuffle(val)
            rng.shuffle(test)

        return DatasetSplit(train=train, val=val, test=test)


# ---------------------------------------------------------------------------
# Class balance analyzer
# ---------------------------------------------------------------------------

class ClassBalanceAnalyzer:
    """Analyse and rebalance class distributions."""

    def analyse(
        self, records: List[Record], label_field: str
    ) -> Dict[str, Any]:
        """Return class counts and imbalance ratio."""
        labels = [str(rec.get(label_field, "_missing")) for rec in records]
        counter = Counter(labels)
        total = sum(counter.values())
        if not counter:
            return {"counts": {}, "imbalance_ratio": 1.0, "balanced": True}

        counts = dict(counter.most_common())
        max_count = max(counts.values())
        min_count = min(counts.values())
        imbalance_ratio = max_count / min_count if min_count else float("inf")
        balanced = imbalance_ratio <= 3.0

        return {
            "counts": counts,
            "imbalance_ratio": round(imbalance_ratio, 4),
            "balanced": balanced,
            "total": total,
        }

    def oversample(
        self,
        records: List[Record],
        label_field: str,
        seed: int = 42,
    ) -> List[Record]:
        """Simple random oversample minority classes to match majority class size."""
        rng = random.Random(seed)
        buckets: Dict[Any, List[Record]] = {}
        for rec in records:
            label = rec.get(label_field, "_missing")
            buckets.setdefault(label, []).append(rec)

        if not buckets:
            return records

        max_size = max(len(v) for v in buckets.values())
        result: List[Record] = []
        for label_records in buckets.values():
            result.extend(label_records)
            deficit = max_size - len(label_records)
            if deficit > 0:
                extras = rng.choices(label_records, k=deficit)
                result.extend(extras)

        rng.shuffle(result)
        return result

    def undersample(
        self,
        records: List[Record],
        label_field: str,
        seed: int = 42,
    ) -> List[Record]:
        """Random undersample majority classes to match minority class size."""
        rng = random.Random(seed)
        buckets: Dict[Any, List[Record]] = {}
        for rec in records:
            label = rec.get(label_field, "_missing")
            buckets.setdefault(label, []).append(rec)

        if not buckets:
            return records

        min_size = min(len(v) for v in buckets.values())
        result: List[Record] = []
        for label_records in buckets.values():
            result.extend(rng.sample(label_records, min(min_size, len(label_records))))

        rng.shuffle(result)
        return result


# ---------------------------------------------------------------------------
# Exporter
# ---------------------------------------------------------------------------

class DatasetExporter:
    """Export compiled datasets to various ML framework formats."""

    SUPPORTED_FORMATS = {"json", "jsonl", "csv", "huggingface", "pytorch", "tensorflow"}

    def export(
        self,
        dataset: CompiledDataset,
        output_dir: Union[str, Path],
        fmt: str = "jsonl",
    ) -> Dict[str, Path]:
        """
        Export dataset to *output_dir* in *fmt* format.
        Returns mapping of split name -> file path.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        fmt = fmt.lower()
        if fmt not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported export format: {fmt!r}. Choose from {self.SUPPORTED_FORMATS}")

        paths: Dict[str, Path] = {}
        splits = {
            "train": dataset.split.train,
            "val": dataset.split.val,
            "test": dataset.split.test,
        }

        for split_name, records in splits.items():
            if not records:
                continue
            if fmt == "json":
                path = self._write_json(records, output_dir, dataset.name, split_name)
            elif fmt == "jsonl":
                path = self._write_jsonl(records, output_dir, dataset.name, split_name)
            elif fmt == "csv":
                path = self._write_csv(records, output_dir, dataset.name, split_name)
            elif fmt in ("huggingface",):
                path = self._write_huggingface(records, output_dir, dataset.name, split_name)
            elif fmt == "pytorch":
                path = self._write_pytorch(records, output_dir, dataset.name, split_name)
            elif fmt == "tensorflow":
                path = self._write_tensorflow(records, output_dir, dataset.name, split_name)
            else:
                path = self._write_jsonl(records, output_dir, dataset.name, split_name)
            paths[split_name] = path
            logger.info("Exported %s split (%d records) -> %s", split_name, len(records), path)

        # Write manifest
        manifest_path = output_dir / f"{dataset.name}_manifest.json"
        with manifest_path.open("w", encoding="utf-8") as fh:
            json.dump(dataset.manifest, fh, indent=2, default=str)
        paths["manifest"] = manifest_path

        return paths

    # ------------------------------------------------------------------
    # Format writers
    # ------------------------------------------------------------------

    @staticmethod
    def _write_json(
        records: List[Record], out: Path, name: str, split: str
    ) -> Path:
        path = out / f"{name}_{split}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2, default=str)
        return path

    @staticmethod
    def _write_jsonl(
        records: List[Record], out: Path, name: str, split: str
    ) -> Path:
        path = out / f"{name}_{split}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, default=str) + "\n")
        return path

    @staticmethod
    def _write_csv(
        records: List[Record], out: Path, name: str, split: str
    ) -> Path:
        import csv as _csv

        path = out / f"{name}_{split}.csv"
        if not records:
            path.write_text("", encoding="utf-8")
            return path
        fieldnames = list(records[0].keys())
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = _csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
        return path

    @staticmethod
    def _write_huggingface(
        records: List[Record], out: Path, name: str, split: str
    ) -> Path:
        """HuggingFace Datasets compatible JSONL (same as JSONL but with .jsonl extension in a split dir)."""
        split_dir = out / name / split
        split_dir.mkdir(parents=True, exist_ok=True)
        path = split_dir / "data.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, default=str) + "\n")
        return path

    @staticmethod
    def _write_pytorch(
        records: List[Record], out: Path, name: str, split: str
    ) -> Path:
        """PyTorch-compatible JSON list file."""
        path = out / f"{name}_{split}_pt.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump({"data": records}, fh, default=str)
        return path

    @staticmethod
    def _write_tensorflow(
        records: List[Record], out: Path, name: str, split: str
    ) -> Path:
        """TensorFlow compatible JSONL."""
        path = out / f"{name}_{split}_tf.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, default=str) + "\n")
        return path


# ---------------------------------------------------------------------------
# Manifest generator
# ---------------------------------------------------------------------------

class ManifestGenerator:
    """Generate dataset manifest with statistics."""

    def generate(
        self,
        name: str,
        split: DatasetSplit,
        version: str,
        source_info: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        manifest = {
            "name": name,
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "split_sizes": {
                "train": len(split.train),
                "val": len(split.val),
                "test": len(split.test),
                "total": split.total,
            },
            "split_ratios": {
                "train": round(len(split.train) / split.total, 4) if split.total else 0.0,
                "val": round(len(split.val) / split.total, 4) if split.total else 0.0,
                "test": round(len(split.test) / split.total, 4) if split.total else 0.0,
            },
            "fields": self._extract_fields(split.train),
            "source_info": source_info or {},
        }
        if extra_metadata:
            manifest.update(extra_metadata)
        return manifest

    @staticmethod
    def _extract_fields(records: List[Record]) -> List[str]:
        if not records:
            return []
        return list(records[0].keys())


# ---------------------------------------------------------------------------
# Dataset compiler – public API
# ---------------------------------------------------------------------------

class DatasetCompiler:
    """
    High-level dataset compilation orchestrator.

    Usage::

        compiler = DatasetCompiler()

        # Fuse records from multiple sources
        records = compiler.fuse([source_a_records, source_b_records])

        # Compile into a versioned, split dataset
        dataset = compiler.compile(records, name="my_dataset")

        # Export
        paths = compiler.export(dataset, output_dir="./output", fmt="jsonl")
    """

    def __init__(self) -> None:
        self._splitter = Splitter()
        self._balance_analyzer = ClassBalanceAnalyzer()
        self._exporter = DatasetExporter()
        self._manifest_gen = ManifestGenerator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fuse(
        self,
        sources: List[List[Record]],
        strategy: str = MergeStrategy.CONCAT,
    ) -> List[Record]:
        """Merge multiple record lists using *strategy*."""
        if strategy not in MergeStrategy.ALL:
            raise ValueError(f"Unknown merge strategy: {strategy!r}")

        if strategy == MergeStrategy.CONCAT:
            result: List[Record] = []
            for src in sources:
                result.extend(src)
            return result

        if strategy == MergeStrategy.UNION:
            all_keys: set = set()
            for src in sources:
                for rec in src:
                    all_keys.update(rec.keys())
            result = []
            for src in sources:
                for rec in src:
                    filled = {k: rec.get(k, None) for k in all_keys}
                    result.append(filled)
            return result

        if strategy == MergeStrategy.INTERSECTION:
            if not sources:
                return []
            common_keys = set(sources[0][0].keys()) if sources[0] else set()
            for src in sources[1:]:
                if src:
                    common_keys &= set(src[0].keys())
            result = []
            for src in sources:
                for rec in src:
                    result.append({k: rec[k] for k in common_keys if k in rec})
            return result

        return []

    def compile(
        self,
        records: List[Record],
        name: str = "dataset",
        split_config: Optional[SplitConfig] = None,
        label_field: Optional[str] = None,
        balance_strategy: Optional[str] = None,
        source_info: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> CompiledDataset:
        """
        Compile records into a versioned :class:`CompiledDataset`.

        Parameters
        ----------
        records : list of dicts
        name : dataset name
        split_config : SplitConfig (defaults to 70/15/15)
        label_field : field used for stratification / balance analysis
        balance_strategy : 'oversample' | 'undersample' | None
        source_info : provenance metadata
        extra_metadata : additional manifest metadata
        """
        if split_config is None:
            split_config = SplitConfig(
                stratify_field=label_field,
            )

        # Balance adjustment
        if label_field and balance_strategy:
            if balance_strategy == "oversample":
                records = self._balance_analyzer.oversample(records, label_field)
            elif balance_strategy == "undersample":
                records = self._balance_analyzer.undersample(records, label_field)
            else:
                logger.warning("Unknown balance_strategy %r, skipping.", balance_strategy)

        # Split
        split = self._splitter.split(records, split_config)

        # Build version
        version = CompiledDataset._generate_version(split)

        # Generate manifest
        balance_info: Dict[str, Any] = {}
        if label_field:
            balance_info = self._balance_analyzer.analyse(records, label_field)

        manifest = self._manifest_gen.generate(
            name=name,
            split=split,
            version=version,
            source_info=source_info,
            extra_metadata={
                **(extra_metadata or {}),
                "balance_info": balance_info,
            },
        )

        logger.info(
            "Compiled dataset '%s' v%s: train=%d, val=%d, test=%d",
            name, version, len(split.train), len(split.val), len(split.test),
        )

        return CompiledDataset(name=name, split=split, manifest=manifest, version=version)

    def export(
        self,
        dataset: CompiledDataset,
        output_dir: Union[str, Path] = "./output",
        fmt: str = "jsonl",
    ) -> Dict[str, Path]:
        """Export dataset; returns mapping of split-name -> file path."""
        return self._exporter.export(dataset, output_dir, fmt)

    def analyse_balance(
        self, records: List[Record], label_field: str
    ) -> Dict[str, Any]:
        """Analyse class balance for *label_field*."""
        return self._balance_analyzer.analyse(records, label_field)
