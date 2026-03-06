"""
struct_engine.py - Intelligent Data Structuring Engine
Part of the DataBlob Godmode Toolkit for Victor LLM

Features:
- Automatic data type inference (categorical, numerical, temporal, spatial, textual)
- Normalization and standardization across heterogeneous sources
- Relationship detection and entity linking
- Metadata extraction and enrichment
- Data quality scoring and anomaly detection
- Cross-blob consistency validation
"""

from __future__ import annotations

import logging
import math
import re
import statistics
from collections import Counter
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type system
# ---------------------------------------------------------------------------

class FieldType(Enum):
    CATEGORICAL = auto()
    NUMERICAL_INT = auto()
    NUMERICAL_FLOAT = auto()
    TEMPORAL = auto()
    SPATIAL = auto()
    TEXTUAL = auto()
    BOOLEAN = auto()
    NULL = auto()
    UNKNOWN = auto()


# Common temporal patterns
_TEMPORAL_PATTERNS = [
    re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?"),  # ISO 8601
    re.compile(r"^\d{2}/\d{2}/\d{4}"),                           # MM/DD/YYYY
    re.compile(r"^\d{2}-\d{2}-\d{4}"),                           # DD-MM-YYYY
    re.compile(r"^\d{4}/\d{2}/\d{2}"),                           # YYYY/MM/DD
    re.compile(r"^\w{3}\s+\d{1,2},?\s+\d{4}"),                   # Mon DD, YYYY
]

# Spatial patterns (lat/lon candidates)
_LAT_LON_PATTERN = re.compile(
    r"^-?\d{1,3}\.\d+,\s*-?\d{1,3}\.\d+$"
)

Record = Dict[str, Any]


# ---------------------------------------------------------------------------
# Field type inferrer
# ---------------------------------------------------------------------------

class TypeInferrer:
    """Infer the semantic type of a field from its values."""

    # If a string field has <= this fraction of unique values, call it categorical
    CATEGORICAL_RATIO_THRESHOLD = 0.5
    # Minimum number of values to make a reliable inference
    MIN_SAMPLE_SIZE = 5

    def infer(self, values: List[Any]) -> FieldType:
        non_null = [v for v in values if v is not None and v != ""]
        if not non_null:
            return FieldType.NULL

        if all(isinstance(v, bool) for v in non_null):
            return FieldType.BOOLEAN

        if all(isinstance(v, int) for v in non_null):
            return FieldType.NUMERICAL_INT

        if all(isinstance(v, float) for v in non_null):
            return FieldType.NUMERICAL_FLOAT

        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in non_null):
            return FieldType.NUMERICAL_FLOAT

        str_values = [str(v) for v in non_null]

        if self._all_temporal(str_values):
            return FieldType.TEMPORAL

        if self._all_spatial(str_values):
            return FieldType.SPATIAL

        if self._all_bool_like(str_values):
            return FieldType.BOOLEAN

        num_count = sum(1 for v in str_values if self._is_numeric(v))
        if num_count == len(str_values):
            # Check if any contain a decimal point
            if any("." in v for v in str_values):
                return FieldType.NUMERICAL_FLOAT
            return FieldType.NUMERICAL_INT

        # Categorical vs textual
        if len(non_null) >= self.MIN_SAMPLE_SIZE:
            unique_ratio = len(set(str_values)) / len(str_values)
            avg_len = sum(len(v) for v in str_values) / len(str_values)
            if unique_ratio <= self.CATEGORICAL_RATIO_THRESHOLD and avg_len < 64:
                return FieldType.CATEGORICAL

        return FieldType.TEXTUAL

    @staticmethod
    def _all_temporal(values: List[str]) -> bool:
        return all(
            any(p.match(v) for p in _TEMPORAL_PATTERNS)
            for v in values
        )

    @staticmethod
    def _all_spatial(values: List[str]) -> bool:
        return all(_LAT_LON_PATTERN.match(v) for v in values)

    @staticmethod
    def _all_bool_like(values: List[str]) -> bool:
        bool_set = {"true", "false", "yes", "no", "1", "0", "t", "f", "y", "n"}
        return all(v.lower() in bool_set for v in values)

    @staticmethod
    def _is_numeric(value: str) -> bool:
        try:
            float(value.replace(",", ""))
            return True
        except ValueError:
            return False


# ---------------------------------------------------------------------------
# Field statistics
# ---------------------------------------------------------------------------

class FieldStats:
    """Compute descriptive statistics for a field."""

    def compute(self, name: str, values: List[Any], field_type: FieldType) -> Dict[str, Any]:
        total = len(values)
        null_count = sum(1 for v in values if v is None or v == "")
        non_null = [v for v in values if v is not None and v != ""]
        unique_count = len(set(str(v) for v in non_null))

        stats: Dict[str, Any] = {
            "field": name,
            "type": field_type.name,
            "total": total,
            "null_count": null_count,
            "null_pct": round(null_count / total * 100, 2) if total else 0.0,
            "unique_count": unique_count,
        }

        if field_type in (FieldType.NUMERICAL_INT, FieldType.NUMERICAL_FLOAT):
            nums = []
            for v in non_null:
                try:
                    nums.append(float(str(v).replace(",", "")))
                except ValueError:
                    pass
            if nums:
                stats["min"] = min(nums)
                stats["max"] = max(nums)
                stats["mean"] = statistics.mean(nums)
                stats["median"] = statistics.median(nums)
                if len(nums) > 1:
                    stats["std_dev"] = statistics.stdev(nums)
                else:
                    stats["std_dev"] = 0.0

        elif field_type == FieldType.CATEGORICAL:
            counter = Counter(str(v) for v in non_null)
            stats["top_values"] = counter.most_common(10)

        elif field_type == FieldType.TEXTUAL:
            lengths = [len(str(v)) for v in non_null]
            if lengths:
                stats["avg_length"] = statistics.mean(lengths)
                stats["max_length"] = max(lengths)
                stats["min_length"] = min(lengths)

        return stats


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------

class Normalizer:
    """Normalize / standardize field values."""

    def normalize_numeric(
        self,
        values: List[Any],
        strategy: str = "minmax",
    ) -> List[Optional[float]]:
        """
        Normalize numeric values.

        strategy: 'minmax' (scale to [0,1]) | 'zscore' (mean=0, std=1)
        """
        nums: List[Optional[float]] = []
        raw: List[float] = []
        for v in values:
            if v is None or v == "":
                nums.append(None)
            else:
                try:
                    raw.append(float(str(v).replace(",", "")))
                    nums.append(float(str(v).replace(",", "")))
                except ValueError:
                    nums.append(None)

        if not raw:
            return nums

        if strategy == "minmax":
            mn, mx = min(raw), max(raw)
            rng = mx - mn
            return [
                None if v is None else (0.0 if rng == 0 else (v - mn) / rng)
                for v in nums
            ]
        elif strategy == "zscore":
            mean = statistics.mean(raw)
            std = statistics.stdev(raw) if len(raw) > 1 else 0.0
            return [
                None if v is None else (0.0 if std == 0 else (v - mean) / std)
                for v in nums
            ]
        return nums

    @staticmethod
    def normalize_text(value: str) -> str:
        """Basic text normalization: strip, lower, collapse whitespace."""
        return re.sub(r"\s+", " ", value.strip().lower())

    @staticmethod
    def normalize_boolean(value: Any) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        s = str(value).lower().strip()
        if s in {"true", "yes", "1", "t", "y"}:
            return True
        if s in {"false", "no", "0", "f", "n"}:
            return False
        return None

    @staticmethod
    def parse_temporal(value: str) -> Optional[datetime]:
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        return None


# ---------------------------------------------------------------------------
# Anomaly detector
# ---------------------------------------------------------------------------

class AnomalyDetector:
    """Detect anomalous values using simple statistical methods."""

    def __init__(self, z_threshold: float = 3.0) -> None:
        self.z_threshold = z_threshold

    def detect_numeric_outliers(
        self, values: List[Any], field_name: str = ""
    ) -> List[Dict[str, Any]]:
        """Return list of anomaly dicts for numeric outliers (Z-score method)."""
        nums: List[Tuple[int, float]] = []
        for i, v in enumerate(values):
            if v is None or v == "":
                continue
            try:
                nums.append((i, float(str(v).replace(",", ""))))
            except ValueError:
                pass

        if len(nums) < 4:
            return []

        raw = [n for _, n in nums]
        mean = statistics.mean(raw)
        std = statistics.stdev(raw) if len(raw) > 1 else 0.0
        if std == 0:
            return []

        anomalies = []
        for idx, num in nums:
            z = abs(num - mean) / std
            if z > self.z_threshold:
                anomalies.append(
                    {
                        "field": field_name,
                        "index": idx,
                        "value": num,
                        "z_score": round(z, 4),
                        "type": "numeric_outlier",
                    }
                )
        return anomalies

    def detect_duplicates(
        self, records: List[Record], key_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Detect duplicate records. Uses all fields if *key_fields* not given."""
        seen: Dict[tuple, int] = {}
        dupes: List[Dict[str, Any]] = []
        for i, rec in enumerate(records):
            if key_fields:
                key = tuple(str(rec.get(k, "")) for k in key_fields)
            else:
                key = tuple(sorted((str(k), str(v)) for k, v in rec.items()))
            if key in seen:
                dupes.append(
                    {
                        "index": i,
                        "duplicate_of": seen[key],
                        "type": "duplicate_record",
                    }
                )
            else:
                seen[key] = i
        return dupes

    def detect_nulls(self, records: List[Record]) -> Dict[str, float]:
        """Return null percentage per field."""
        if not records:
            return {}
        all_keys = {k for rec in records for k in rec}
        result: Dict[str, float] = {}
        n = len(records)
        for k in all_keys:
            null_count = sum(1 for rec in records if rec.get(k) in (None, "", "null", "NULL", "N/A"))
            result[k] = round(null_count / n * 100, 2)
        return result


# ---------------------------------------------------------------------------
# Quality scorer
# ---------------------------------------------------------------------------

class QualityScorer:
    """Compute a 0-100 data quality score for a dataset."""

    def score(
        self,
        records: List[Record],
        anomalies: List[Dict[str, Any]],
        null_pcts: Dict[str, float],
    ) -> float:
        if not records:
            return 0.0

        n = len(records)

        # Null penalty (average null % across fields, capped at 100)
        avg_null = sum(null_pcts.values()) / len(null_pcts) if null_pcts else 0.0
        null_penalty = min(avg_null, 100.0)

        # Anomaly penalty
        anomaly_pct = min(len(anomalies) / n * 100, 100.0) if n else 0.0

        score = 100.0 - (null_penalty * 0.5) - (anomaly_pct * 0.5)
        return round(max(0.0, min(100.0, score)), 2)


# ---------------------------------------------------------------------------
# Relationship detector
# ---------------------------------------------------------------------------

class RelationshipDetector:
    """Detect potential foreign-key / entity relationships between field values."""

    def detect(
        self,
        datasets: Dict[str, List[Record]],
    ) -> List[Dict[str, Any]]:
        """
        Compare string fields across datasets and report high-overlap pairs.
        Returns list of potential relationship dicts.
        """
        # Build field value sets
        field_sets: Dict[str, set] = {}
        for ds_name, records in datasets.items():
            if not records:
                continue
            for field in records[0]:
                values = {str(r.get(field, "")) for r in records if r.get(field) not in (None, "")}
                key = f"{ds_name}.{field}"
                field_sets[key] = values

        relationships = []
        keys = list(field_sets.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = keys[i], keys[j]
                sa, sb = field_sets[a], field_sets[b]
                if not sa or not sb:
                    continue
                # Jaccard similarity
                intersection = len(sa & sb)
                union = len(sa | sb)
                jaccard = intersection / union if union else 0.0
                if jaccard >= 0.5 and intersection >= 2:
                    relationships.append(
                        {
                            "field_a": a,
                            "field_b": b,
                            "jaccard": round(jaccard, 4),
                            "shared_values": intersection,
                        }
                    )
        return relationships


# ---------------------------------------------------------------------------
# Main StructEngine class
# ---------------------------------------------------------------------------

class StructuredDataset:
    """Holds a structured, annotated dataset."""

    def __init__(
        self,
        records: List[Record],
        field_types: Dict[str, FieldType],
        field_stats: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
        quality_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.records = records
        self.field_types = field_types
        self.field_stats = field_stats
        self.anomalies = anomalies
        self.quality_score = quality_score
        self.metadata: Dict[str, Any] = metadata or {}

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"StructuredDataset(records={len(self.records)}, "
            f"fields={len(self.field_types)}, quality={self.quality_score})"
        )


class StructEngine:
    """
    Intelligent data structuring and transformation engine.

    Usage::

        engine = StructEngine()
        dataset = engine.structure(records)
        normalized = engine.normalize(records, strategies={"age": "minmax"})
    """

    def __init__(self) -> None:
        self._inferrer = TypeInferrer()
        self._stats_calc = FieldStats()
        self._anomaly_detector = AnomalyDetector()
        self._quality_scorer = QualityScorer()
        self._normalizer = Normalizer()

    # ------------------------------------------------------------------
    # High-level API
    # ------------------------------------------------------------------

    def structure(
        self,
        records: List[Record],
        source_name: str = "dataset",
    ) -> StructuredDataset:
        """
        Analyse and annotate a list of raw records.
        Returns a :class:`StructuredDataset` with inferred types, stats, anomalies,
        and a quality score.
        """
        if not records:
            return StructuredDataset([], {}, [], [], 0.0, {"source": source_name})

        # Collect all fields
        all_fields: List[str] = list({k for rec in records for k in rec})

        # Infer types
        field_types: Dict[str, FieldType] = {}
        for field in all_fields:
            vals = [rec.get(field) for rec in records]
            field_types[field] = self._inferrer.infer(vals)

        # Compute field stats
        field_stats: List[Dict[str, Any]] = []
        for field, ftype in field_types.items():
            vals = [rec.get(field) for rec in records]
            stats = self._stats_calc.compute(field, vals, ftype)
            field_stats.append(stats)

        # Detect anomalies
        anomalies: List[Dict[str, Any]] = []
        for field, ftype in field_types.items():
            if ftype in (FieldType.NUMERICAL_INT, FieldType.NUMERICAL_FLOAT):
                vals = [rec.get(field) for rec in records]
                anomalies.extend(self._anomaly_detector.detect_numeric_outliers(vals, field))
        anomalies.extend(self._anomaly_detector.detect_duplicates(records))

        # Null percentages
        null_pcts = self._anomaly_detector.detect_nulls(records)

        # Quality score
        quality = self._quality_scorer.score(records, anomalies, null_pcts)

        metadata = {
            "source": source_name,
            "record_count": len(records),
            "field_count": len(all_fields),
            "null_percentages": null_pcts,
        }

        logger.info(
            "Structured %d records (%d fields) from '%s'. Quality: %.1f/100. Anomalies: %d",
            len(records),
            len(all_fields),
            source_name,
            quality,
            len(anomalies),
        )

        return StructuredDataset(records, field_types, field_stats, anomalies, quality, metadata)

    def normalize(
        self,
        records: List[Record],
        strategies: Optional[Dict[str, str]] = None,
        infer_types: bool = True,
    ) -> List[Record]:
        """
        Return a new list of records with numeric fields normalised.

        *strategies*: mapping of field -> 'minmax' | 'zscore'. Defaults to 'minmax'.
        """
        strategies = strategies or {}

        if infer_types:
            all_fields = list({k for rec in records for k in rec})
            field_types = {
                f: self._inferrer.infer([rec.get(f) for rec in records])
                for f in all_fields
            }
        else:
            field_types = {}

        normalised = [dict(rec) for rec in records]

        for field, ftype in field_types.items():
            if ftype not in (FieldType.NUMERICAL_INT, FieldType.NUMERICAL_FLOAT):
                continue
            strategy = strategies.get(field, "minmax")
            vals = [rec.get(field) for rec in records]
            normed = self._normalizer.normalize_numeric(vals, strategy)
            for rec, norm_val in zip(normalised, normed):
                rec[field] = norm_val

        return normalised

    def enrich_metadata(self, records: List[Record]) -> Dict[str, Any]:
        """
        Extract enriched metadata about the records (field types, stats, quality).
        Returns a metadata dict suitable for inclusion in a dataset manifest.
        """
        dataset = self.structure(records)
        return {
            "field_types": {k: v.name for k, v in dataset.field_types.items()},
            "field_stats": dataset.field_stats,
            "quality_score": dataset.quality_score,
            "anomaly_count": len(dataset.anomalies),
            "record_count": len(records),
        }

    def validate_consistency(
        self, datasets: Dict[str, List[Record]]
    ) -> Dict[str, Any]:
        """
        Cross-blob consistency validation.
        Checks that shared fields have compatible types across datasets.
        """
        issues: List[str] = []
        field_type_map: Dict[str, Dict[str, FieldType]] = {}

        for ds_name, records in datasets.items():
            if not records:
                continue
            for field in records[0]:
                vals = [rec.get(field) for rec in records]
                ft = self._inferrer.infer(vals)
                field_type_map.setdefault(field, {})[ds_name] = ft

        for field, type_by_ds in field_type_map.items():
            types = set(type_by_ds.values())
            if len(types) > 1:
                issues.append(
                    f"Field '{field}' has inconsistent types across datasets: "
                    + ", ".join(f"{ds}={ft.name}" for ds, ft in type_by_ds.items())
                )

        relationships = RelationshipDetector().detect(datasets)

        return {
            "consistent": len(issues) == 0,
            "issues": issues,
            "relationships": relationships,
        }
