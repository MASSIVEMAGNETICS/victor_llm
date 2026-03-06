"""
test_godmode_toolkit.py - Comprehensive Test Suite
DataBlob Godmode Toolkit for Victor LLM
"""

from __future__ import annotations

import csv
import io
import json
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Ensure repo root is on the path
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.resolve()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ===========================================================================
# smart_parser tests
# ===========================================================================

class TestFormatDetector(unittest.TestCase):
    def setUp(self):
        from smart_parser import FormatDetector, DataFormat
        self.detector = FormatDetector()
        self.DataFormat = DataFormat

    def test_detect_json_by_extension(self):
        fmt = self.detector.detect_bytes(b'{"a":1}', hint="file.json")
        self.assertEqual(fmt, self.DataFormat.JSON)

    def test_detect_csv_by_extension(self):
        fmt = self.detector.detect_bytes(b"a,b\n1,2\n", hint="file.csv")
        self.assertEqual(fmt, self.DataFormat.CSV)

    def test_detect_tsv_by_extension(self):
        fmt = self.detector.detect_bytes(b"a\tb\n1\t2\n", hint="file.tsv")
        self.assertEqual(fmt, self.DataFormat.TSV)

    def test_detect_xml_by_content(self):
        fmt = self.detector.detect_bytes(b"<root><item>x</item></root>")
        self.assertEqual(fmt, self.DataFormat.XML)

    def test_detect_jsonl_by_content(self):
        data = b'{"a":1}\n{"b":2}\n{"c":3}\n'
        fmt = self.detector.detect_bytes(data)
        self.assertEqual(fmt, self.DataFormat.JSONL)

    def test_detect_parquet_magic(self):
        fmt = self.detector.detect_bytes(b"PAR1" + b"\x00" * 100)
        self.assertEqual(fmt, self.DataFormat.PARQUET)

    def test_detect_text_fallback(self):
        fmt = self.detector.detect_bytes(b"just some plain text")
        self.assertEqual(fmt, self.DataFormat.TEXT)

    def test_detect_empty(self):
        fmt = self.detector.detect_bytes(b"")
        self.assertEqual(fmt, self.DataFormat.UNKNOWN)


class TestJSONParser(unittest.TestCase):
    def setUp(self):
        from smart_parser import JSONParser, DataFormat
        self.parser = JSONParser()
        self.DataFormat = DataFormat

    def test_parse_list(self):
        data = json.dumps([{"a": 1}, {"a": 2}]).encode()
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 2)
        self.assertEqual(result.records[0]["a"], 1)

    def test_parse_dict(self):
        data = json.dumps({"x": 10, "y": 20}).encode()
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.records[0]["x"], 10)

    def test_parse_scalar(self):
        data = b"42"
        result = self.parser.parse_bytes(data)
        self.assertEqual(result.records[0]["_value"], 42)

    def test_invalid_json(self):
        data = b"{bad json"
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 0)
        self.assertTrue(len(result.errors) > 0)

    def test_trailing_comma_repair(self):
        data = b'{"a":1,"b":2,}'
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 1)
        self.assertTrue(any("repaired" in e.lower() for e in result.errors))

    def test_schema_inference(self):
        data = json.dumps([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]).encode()
        result = self.parser.parse_bytes(data)
        schema_fields = {f["name"]: f["type"] for f in result.schema}
        self.assertIn("name", schema_fields)
        self.assertIn("age", schema_fields)


class TestJSONLParser(unittest.TestCase):
    def setUp(self):
        from smart_parser import JSONLParser
        self.parser = JSONLParser()

    def test_parse_multiple_lines(self):
        data = b'{"a": 1}\n{"a": 2}\n{"a": 3}\n'
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 3)

    def test_skip_empty_lines(self):
        data = b'{"a": 1}\n\n{"a": 2}\n'
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 2)

    def test_bad_lines_reported(self):
        data = b'{"a": 1}\nbad line\n{"a": 2}\n'
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 2)
        self.assertTrue(len(result.errors) > 0)

    def test_stream(self):
        data = b'{"x": 1}\n{"x": 2}\n'
        records = list(self.parser.parse_stream([data]))
        self.assertEqual(len(records), 2)


class TestXMLParser(unittest.TestCase):
    def setUp(self):
        from smart_parser import XMLParser
        self.parser = XMLParser()

    def test_parse_simple(self):
        data = b"<items><item id='1'><name>A</name></item><item id='2'><name>B</name></item></items>"
        result = self.parser.parse_bytes(data)
        self.assertGreater(len(result.records), 0)

    def test_repair_missing_root(self):
        data = b"<item>a</item><item>b</item>"
        result = self.parser.parse_bytes(data)
        self.assertTrue(any("repaired" in e.lower() for e in result.errors))

    def test_invalid_xml(self):
        data = b"<open_but_no_close"
        result = self.parser.parse_bytes(data)
        # Should have errors
        self.assertGreater(len(result.errors), 0)


class TestCSVParser(unittest.TestCase):
    def setUp(self):
        from smart_parser import CSVParser, DataFormat
        self.parser = CSVParser()
        self.DataFormat = DataFormat

    def test_parse_basic(self):
        data = "name,age,score\nAlice,30,9.5\nBob,25,8.0\n".encode()
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 2)
        self.assertEqual(result.records[0]["name"], "Alice")

    def test_auto_delimiter(self):
        data = "name;age\nAlice;30\nBob;25\n".encode()
        result = self.parser.parse_bytes(data)
        self.assertGreater(len(result.records), 0)

    def test_tsv(self):
        parser_tsv = __import__("smart_parser").CSVParser(delimiter="\t")
        data = "name\tage\nAlice\t30\n".encode()
        from smart_parser import DataFormat
        result = parser_tsv.parse_bytes(data, fmt=DataFormat.TSV)
        self.assertEqual(len(result.records), 1)


class TestTextParser(unittest.TestCase):
    def setUp(self):
        from smart_parser import TextParser
        self.parser = TextParser()

    def test_parse_lines(self):
        data = b"line one\nline two\nline three\n"
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 3)
        self.assertEqual(result.records[0]["_text"], "line one")

    def test_skip_blank_lines(self):
        data = b"line one\n\nline two\n"
        result = self.parser.parse_bytes(data)
        self.assertEqual(len(result.records), 2)


class TestSmartParser(unittest.TestCase):
    def setUp(self):
        from smart_parser import SmartParser
        self.parser = SmartParser()

    def test_parse_file_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump([{"a": 1}, {"a": 2}], f)
            fname = f.name
        try:
            result = self.parser.parse_file(fname)
            self.assertEqual(len(result.records), 2)
        finally:
            os.unlink(fname)

    def test_parse_file_not_found(self):
        result = self.parser.parse_file("/tmp/nonexistent_godmode_file.json")
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(len(result.records), 0)

    def test_parse_bytes_csv(self):
        data = b"x,y\n1,2\n3,4\n"
        result = self.parser.parse_bytes(data, hint="data.csv")
        self.assertEqual(len(result.records), 2)

    def test_stream_file(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False) as f:
            for i in range(10):
                f.write(json.dumps({"i": i}) + "\n")
            fname = f.name
        try:
            records = list(self.parser.stream_file(fname))
            self.assertEqual(len(records), 10)
        finally:
            os.unlink(fname)

    def test_infer_schema(self):
        records = [{"name": "A", "age": 30}, {"name": "B", "age": 25}]
        schema = self.parser.infer_schema(records)
        names = {f["name"] for f in schema}
        self.assertIn("name", names)
        self.assertIn("age", names)

    def test_check_corruption_valid_json(self):
        from smart_parser import DataFormat
        issues = self.parser.check_corruption(b'{"ok": true}', DataFormat.JSON)
        self.assertEqual(issues, [])

    def test_check_corruption_invalid_json(self):
        from smart_parser import DataFormat
        issues = self.parser.check_corruption(b"{bad}", DataFormat.JSON)
        self.assertGreater(len(issues), 0)


# ===========================================================================
# struct_engine tests
# ===========================================================================

class TestTypeInferrer(unittest.TestCase):
    def setUp(self):
        from struct_engine import TypeInferrer, FieldType
        self.inferrer = TypeInferrer()
        self.FieldType = FieldType

    def test_infer_int(self):
        self.assertEqual(self.inferrer.infer([1, 2, 3]), self.FieldType.NUMERICAL_INT)

    def test_infer_float(self):
        self.assertEqual(self.inferrer.infer([1.1, 2.2, 3.3]), self.FieldType.NUMERICAL_FLOAT)

    def test_infer_boolean(self):
        self.assertEqual(self.inferrer.infer([True, False, True]), self.FieldType.BOOLEAN)

    def test_infer_boolean_strings(self):
        self.assertEqual(self.inferrer.infer(["true", "false", "yes", "no"]), self.FieldType.BOOLEAN)

    def test_infer_temporal(self):
        self.assertEqual(self.inferrer.infer(["2024-01-01", "2024-06-15"]), self.FieldType.TEMPORAL)

    def test_infer_categorical(self):
        vals = ["cat", "dog", "cat", "bird", "dog", "cat", "dog", "cat", "bird", "dog"]
        self.assertEqual(self.inferrer.infer(vals), self.FieldType.CATEGORICAL)

    def test_infer_textual(self):
        vals = ["This is a unique long text sentence.", "Another completely different sentence.",
                "One more unique item here.", "Yet another unique one.", "And a fifth one."]
        ft = self.inferrer.infer(vals)
        self.assertIn(ft, (self.FieldType.TEXTUAL, self.FieldType.CATEGORICAL))

    def test_infer_null(self):
        self.assertEqual(self.inferrer.infer([None, None, ""]), self.FieldType.NULL)

    def test_infer_numeric_strings(self):
        result = self.inferrer.infer(["1", "2", "3.5"])
        self.assertEqual(result, self.FieldType.NUMERICAL_FLOAT)


class TestNormalizer(unittest.TestCase):
    def setUp(self):
        from struct_engine import Normalizer
        self.norm = Normalizer()

    def test_minmax(self):
        result = self.norm.normalize_numeric([0, 5, 10], "minmax")
        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[1], 0.5)
        self.assertAlmostEqual(result[2], 1.0)

    def test_zscore(self):
        result = self.norm.normalize_numeric([2, 4, 4, 4, 5, 5, 7, 9], "zscore")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 8)

    def test_none_values(self):
        result = self.norm.normalize_numeric([None, 5, 10], "minmax")
        self.assertIsNone(result[0])
        self.assertAlmostEqual(result[1], 0.0)
        self.assertAlmostEqual(result[2], 1.0)

    def test_normalize_text(self):
        self.assertEqual(self.norm.normalize_text("  Hello   World  "), "hello world")

    def test_normalize_boolean(self):
        self.assertTrue(self.norm.normalize_boolean("yes"))
        self.assertFalse(self.norm.normalize_boolean("no"))
        self.assertTrue(self.norm.normalize_boolean(True))
        self.assertIsNone(self.norm.normalize_boolean("maybe"))

    def test_parse_temporal(self):
        dt = self.norm.parse_temporal("2024-01-15")
        self.assertEqual(dt.year, 2024)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 15)

    def test_constant_minmax(self):
        result = self.norm.normalize_numeric([5, 5, 5], "minmax")
        self.assertEqual(result, [0.0, 0.0, 0.0])


class TestAnomalyDetector(unittest.TestCase):
    def setUp(self):
        from struct_engine import AnomalyDetector
        self.detector = AnomalyDetector(z_threshold=2.0)

    def test_numeric_outlier(self):
        values = [10, 11, 10, 12, 11, 10, 9, 11, 100]  # 100 is an outlier
        anomalies = self.detector.detect_numeric_outliers(values, "score")
        self.assertTrue(any(a["value"] == 100 for a in anomalies))

    def test_no_outliers(self):
        values = [1, 2, 3, 4, 5, 6, 7, 8]
        anomalies = self.detector.detect_numeric_outliers(values, "x")
        self.assertEqual(anomalies, [])

    def test_detect_duplicates(self):
        records = [{"a": 1, "b": 2}, {"a": 1, "b": 2}, {"a": 3, "b": 4}]
        dupes = self.detector.detect_duplicates(records)
        self.assertEqual(len(dupes), 1)
        self.assertEqual(dupes[0]["index"], 1)

    def test_detect_nulls(self):
        records = [{"a": 1, "b": None}, {"a": 2, "b": "x"}, {"a": None, "b": "y"}]
        null_pcts = self.detector.detect_nulls(records)
        self.assertAlmostEqual(null_pcts["b"], 100 / 3, places=1)
        self.assertAlmostEqual(null_pcts["a"], 100 / 3, places=1)


class TestQualityScorer(unittest.TestCase):
    def setUp(self):
        from struct_engine import QualityScorer
        self.scorer = QualityScorer()

    def test_perfect_score(self):
        score = self.scorer.score([{"a": 1}], [], {"a": 0.0})
        self.assertEqual(score, 100.0)

    def test_all_nulls(self):
        score = self.scorer.score([{"a": None}], [], {"a": 100.0})
        self.assertLess(score, 60.0)

    def test_empty_records(self):
        score = self.scorer.score([], [], {})
        self.assertEqual(score, 0.0)


class TestStructEngine(unittest.TestCase):
    def setUp(self):
        from struct_engine import StructEngine, FieldType
        self.engine = StructEngine()
        self.FieldType = FieldType

    def _make_records(self, n: int = 50) -> List[Dict]:
        rng = random.Random(42)
        return [
            {
                "name": rng.choice(["Alice", "Bob", "Carol"]),
                "age": rng.randint(20, 60),
                "score": round(rng.uniform(0, 100), 2),
                "active": rng.choice([True, False]),
                "joined": "2024-01-01",
            }
            for _ in range(n)
        ]

    def test_structure_returns_dataset(self):
        from struct_engine import StructuredDataset
        records = self._make_records()
        ds = self.engine.structure(records)
        self.assertIsInstance(ds, StructuredDataset)
        self.assertEqual(len(ds.records), len(records))
        self.assertGreater(ds.quality_score, 0)

    def test_field_types_inferred(self):
        records = self._make_records()
        ds = self.engine.structure(records)
        self.assertIn("age", ds.field_types)
        self.assertIn(ds.field_types["age"], (self.FieldType.NUMERICAL_INT, self.FieldType.NUMERICAL_FLOAT))

    def test_normalize(self):
        records = [{"x": 0}, {"x": 5}, {"x": 10}]
        normed = self.engine.normalize(records, strategies={"x": "minmax"})
        self.assertAlmostEqual(normed[0]["x"], 0.0)
        self.assertAlmostEqual(normed[1]["x"], 0.5)
        self.assertAlmostEqual(normed[2]["x"], 1.0)

    def test_enrich_metadata(self):
        records = self._make_records()
        meta = self.engine.enrich_metadata(records)
        self.assertIn("quality_score", meta)
        self.assertIn("field_types", meta)

    def test_validate_consistency(self):
        ds_a = [{"id": "1", "score": 100}]
        ds_b = [{"id": "1", "score": "bad_string"}]
        report = self.engine.validate_consistency({"a": ds_a, "b": ds_b})
        self.assertIn("consistent", report)
        self.assertIn("issues", report)

    def test_empty_records(self):
        from struct_engine import StructuredDataset
        ds = self.engine.structure([])
        self.assertIsInstance(ds, StructuredDataset)
        self.assertEqual(ds.quality_score, 0.0)


# ===========================================================================
# dataset_compiler tests
# ===========================================================================

class TestSplitter(unittest.TestCase):
    def setUp(self):
        from dataset_compiler import Splitter, SplitConfig
        self.splitter = Splitter()
        self.SplitConfig = SplitConfig

    def _make_records(self, n=100):
        return [{"i": i, "label": i % 3} for i in range(n)]

    def test_basic_split(self):
        records = self._make_records(100)
        cfg = self.SplitConfig(train=0.7, val=0.15, test=0.15)
        split = self.splitter.split(records, cfg)
        self.assertEqual(split.total, 100)
        self.assertAlmostEqual(len(split.train) / 100, 0.7, delta=0.02)

    def test_stratified_split(self):
        records = self._make_records(90)
        cfg = self.SplitConfig(train=0.7, val=0.15, test=0.15, stratify_field="label")
        split = self.splitter.split(records, cfg)
        self.assertEqual(split.total, 90)

    def test_empty_records(self):
        cfg = self.SplitConfig()
        split = self.splitter.split([], cfg)
        self.assertEqual(split.total, 0)

    def test_split_config_invalid(self):
        with self.assertRaises(ValueError):
            self.SplitConfig(train=0.8, val=0.3, test=0.3)


class TestClassBalanceAnalyzer(unittest.TestCase):
    def setUp(self):
        from dataset_compiler import ClassBalanceAnalyzer
        self.analyser = ClassBalanceAnalyzer()

    def test_balanced(self):
        records = [{"label": i % 2} for i in range(100)]
        result = self.analyser.analyse(records, "label")
        self.assertTrue(result["balanced"])
        self.assertAlmostEqual(result["imbalance_ratio"], 1.0)

    def test_imbalanced(self):
        records = [{"label": "A"}] * 90 + [{"label": "B"}] * 10
        result = self.analyser.analyse(records, "label")
        self.assertFalse(result["balanced"])
        self.assertAlmostEqual(result["imbalance_ratio"], 9.0)

    def test_oversample(self):
        records = [{"label": "A"}] * 10 + [{"label": "B"}] * 50
        oversampled = self.analyser.oversample(records, "label")
        from collections import Counter
        counts = Counter(r["label"] for r in oversampled)
        self.assertEqual(counts["A"], counts["B"])

    def test_undersample(self):
        records = [{"label": "A"}] * 10 + [{"label": "B"}] * 50
        undersampled = self.analyser.undersample(records, "label")
        from collections import Counter
        counts = Counter(r["label"] for r in undersampled)
        self.assertEqual(counts["A"], counts["B"])
        self.assertEqual(counts["A"], 10)


class TestDatasetExporter(unittest.TestCase):
    def setUp(self):
        from dataset_compiler import DatasetExporter, DatasetSplit, CompiledDataset
        self.exporter = DatasetExporter()
        self.tmp = tempfile.mkdtemp()
        records = [{"a": i, "b": f"x{i}"} for i in range(10)]
        split = DatasetSplit(
            train=records[:7],
            val=records[7:9],
            test=records[9:],
        )
        self.dataset = CompiledDataset(
            name="test_ds",
            split=split,
            manifest={"name": "test_ds", "version": "test"},
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_export_jsonl(self):
        paths = self.exporter.export(self.dataset, self.tmp, "jsonl")
        self.assertIn("train", paths)
        self.assertTrue(paths["train"].exists())
        lines = paths["train"].read_text().strip().splitlines()
        self.assertEqual(len(lines), 7)

    def test_export_json(self):
        paths = self.exporter.export(self.dataset, self.tmp, "json")
        self.assertIn("train", paths)
        data = json.loads(paths["train"].read_text())
        self.assertEqual(len(data), 7)

    def test_export_csv(self):
        paths = self.exporter.export(self.dataset, self.tmp, "csv")
        self.assertIn("train", paths)
        with open(paths["train"]) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 7)

    def test_export_huggingface(self):
        paths = self.exporter.export(self.dataset, self.tmp, "huggingface")
        self.assertIn("train", paths)
        self.assertTrue(paths["train"].exists())

    def test_export_unsupported(self):
        with self.assertRaises(ValueError):
            self.exporter.export(self.dataset, self.tmp, "avro")

    def test_manifest_written(self):
        paths = self.exporter.export(self.dataset, self.tmp, "jsonl")
        self.assertIn("manifest", paths)
        manifest = json.loads(paths["manifest"].read_text())
        self.assertEqual(manifest["name"], "test_ds")


class TestDatasetCompiler(unittest.TestCase):
    def setUp(self):
        from dataset_compiler import DatasetCompiler
        self.compiler = DatasetCompiler()
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _records(self, n=100, label_range=2):
        rng = random.Random(0)
        return [{"x": rng.random(), "label": i % label_range} for i in range(n)]

    def test_compile_basic(self):
        from dataset_compiler import CompiledDataset
        records = self._records(100)
        ds = self.compiler.compile(records, name="test")
        self.assertIsInstance(ds, CompiledDataset)
        self.assertEqual(ds.split.total, 100)
        self.assertIsNotNone(ds.version)

    def test_fuse_concat(self):
        a = [{"x": 1}] * 10
        b = [{"x": 2}] * 20
        fused = self.compiler.fuse([a, b], "concat")
        self.assertEqual(len(fused), 30)

    def test_fuse_union(self):
        a = [{"x": 1}] * 5
        b = [{"y": 2}] * 5
        fused = self.compiler.fuse([a, b], "union")
        self.assertEqual(len(fused), 10)
        self.assertIn("x", fused[0])
        self.assertIn("y", fused[0])

    def test_fuse_intersection(self):
        a = [{"x": 1, "z": 3}] * 5
        b = [{"x": 2, "y": 4}] * 5
        fused = self.compiler.fuse([a, b], "intersection")
        self.assertEqual(len(fused), 10)
        self.assertIn("x", fused[0])
        self.assertNotIn("z", fused[0])
        self.assertNotIn("y", fused[0])

    def test_fuse_invalid_strategy(self):
        with self.assertRaises(ValueError):
            self.compiler.fuse([[]], "invalid_strategy")

    def test_compile_with_balance(self):
        records = [{"x": i, "label": "A" if i < 80 else "B"} for i in range(100)]
        ds = self.compiler.compile(
            records, name="balanced",
            label_field="label",
            balance_strategy="oversample",
        )
        self.assertIsNotNone(ds)

    def test_compile_manifest_fields(self):
        records = self._records(50)
        ds = self.compiler.compile(records, name="mf")
        self.assertIn("name", ds.manifest)
        self.assertIn("version", ds.manifest)
        self.assertIn("split_sizes", ds.manifest)

    def test_export(self):
        records = self._records(50)
        ds = self.compiler.compile(records, name="exp")
        paths = self.compiler.export(ds, self.tmp, "jsonl")
        self.assertIn("train", paths)


# ===========================================================================
# auto_trainer tests
# ===========================================================================

class TestTrainingConfig(unittest.TestCase):
    def test_default_run_id(self):
        from auto_trainer import TrainingConfig
        cfg = TrainingConfig()
        self.assertTrue(cfg.run_id.startswith("run-"))

    def test_custom_run_id(self):
        from auto_trainer import TrainingConfig
        cfg = TrainingConfig(run_id="my-run")
        self.assertEqual(cfg.run_id, "my-run")

    def test_pretrained_fields_defaults(self):
        """TrainingConfig should expose pretrained fine-tuning fields."""
        from auto_trainer import TrainingConfig
        cfg = TrainingConfig()
        self.assertIsNone(cfg.pretrained_model_path)
        self.assertFalse(cfg.freeze_embedding)
        self.assertEqual(cfg.freeze_layers, [])

    def test_pretrained_fields_set(self):
        """Pretrained fine-tuning fields should be settable."""
        from auto_trainer import TrainingConfig
        cfg = TrainingConfig(
            pretrained_model_path="/tmp/model.pt",
            freeze_embedding=True,
            freeze_layers=[0, 1, 2],
            learning_rate=5e-5,
        )
        self.assertEqual(cfg.pretrained_model_path, "/tmp/model.pt")
        self.assertTrue(cfg.freeze_embedding)
        self.assertEqual(cfg.freeze_layers, [0, 1, 2])
        self.assertAlmostEqual(cfg.learning_rate, 5e-5)


class TestLoadPretrainedCheckpoint(unittest.TestCase):
    """Tests for models.load_pretrained_checkpoint."""

    def test_missing_file_raises(self):
        from models import load_pretrained_checkpoint
        with self.assertRaises(FileNotFoundError):
            load_pretrained_checkpoint("/nonexistent/path/model.pt")

    def test_load_returns_dict_with_model_state(self):
        """A checkpoint saved with torch.save should be loadable."""
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch not installed")

        from models import load_pretrained_checkpoint

        tmp_dir = tempfile.mkdtemp()
        ckpt_path = os.path.join(tmp_dir, "test_checkpoint.pt")
        fake_ckpt = {
            "model_state_dict": {"layer.weight": torch.zeros(3, 3)},
            "epoch": 5,
            "global_step": 100,
            "best_val_loss": 0.42,
            "config": {"architecture": {}},
        }
        torch.save(fake_ckpt, ckpt_path)

        loaded = load_pretrained_checkpoint(ckpt_path)
        self.assertIn("model_state_dict", loaded)
        self.assertEqual(loaded["epoch"], 5)
        self.assertAlmostEqual(loaded["best_val_loss"], 0.42)

        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


class TestPretrainedWeightsAndFreezing(unittest.TestCase):
    """Tests for load_pretrained_weights and freeze_model_layers in train_sota_model."""

    def _make_model(self):
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch not installed")
        from models.transformer_model import load_model_from_config
        config_path = Path(__file__).parent / "models" / "blank_slate.json"
        if not config_path.exists():
            self.skipTest("blank_slate.json not found")
        # Use a tiny config to keep tests fast
        import json
        with open(config_path) as f:
            cfg = json.load(f)
        cfg["architecture"]["num_layers"] = 2
        cfg["architecture"]["hidden_size"] = 64
        cfg["architecture"]["num_attention_heads"] = 2
        cfg["architecture"]["intermediate_size"] = 128
        cfg["architecture"]["max_position_embeddings"] = 32
        cfg["architecture"]["vocab_size"] = 256
        from models.transformer_model import VictorTransformerModel
        return VictorTransformerModel(cfg)

    def test_freeze_embedding_disables_grad(self):
        """freeze_model_layers with freeze_embedding=True should disable gradients."""
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch not installed")
        from train_sota_model import freeze_model_layers
        model = self._make_model()
        freeze_model_layers(model, freeze_embedding=True)
        for param in model.token_embedding.parameters():
            self.assertFalse(param.requires_grad)
        for param in model.position_embedding.parameters():
            self.assertFalse(param.requires_grad)
        # Other parameters should still be trainable
        self.assertTrue(any(p.requires_grad for p in model.blocks.parameters()))

    def test_freeze_specific_layer(self):
        """Freezing a specific block index should only affect that block."""
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch not installed")
        from train_sota_model import freeze_model_layers
        model = self._make_model()
        freeze_model_layers(model, freeze_layers=[0])
        for param in model.blocks[0].parameters():
            self.assertFalse(param.requires_grad)
        if len(model.blocks) > 1:
            self.assertTrue(any(p.requires_grad for p in model.blocks[1].parameters()))

    def test_freeze_out_of_range_layer_is_ignored(self):
        """An out-of-range layer index should not crash."""
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch not installed")
        from train_sota_model import freeze_model_layers
        model = self._make_model()
        # Should not raise
        freeze_model_layers(model, freeze_layers=[999])

    def test_load_pretrained_weights_compatible(self):
        """load_pretrained_weights should populate model parameters from a checkpoint."""
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch not installed")
        from train_sota_model import load_pretrained_weights

        model = self._make_model()

        # Save a checkpoint using the current model's weights as the "pretrained" source
        import tempfile
        tmp_dir = tempfile.mkdtemp()
        ckpt_path = os.path.join(tmp_dir, "pretrained.pt")
        torch.save({"model_state_dict": model.state_dict(), "epoch": 3}, ckpt_path)

        # Mutate the model weights so they differ
        with torch.no_grad():
            for p in model.parameters():
                p.fill_(0.0)

        # Load should restore original weights
        checkpoint = load_pretrained_weights(model, ckpt_path)
        self.assertEqual(checkpoint["epoch"], 3)
        # At least some weights should be non-zero after loading
        total_norm = sum(p.abs().sum().item() for p in model.parameters())
        self.assertGreater(total_norm, 0.0)

        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_load_pretrained_weights_partial(self):
        """load_pretrained_weights should skip weights with mismatched shapes."""
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch not installed")
        from train_sota_model import load_pretrained_weights

        model = self._make_model()

        # Build a checkpoint with one mismatched tensor
        state = {k: v.clone() for k, v in model.state_dict().items()}
        first_key = next(iter(state))
        state[first_key] = torch.zeros(99, 99)  # Intentional shape mismatch

        import tempfile
        tmp_dir = tempfile.mkdtemp()
        ckpt_path = os.path.join(tmp_dir, "partial.pt")
        torch.save({"model_state_dict": state, "epoch": 1}, ckpt_path)

        # Should not raise; mismatched key is skipped
        load_pretrained_weights(model, ckpt_path)

        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


class TestModelSelector(unittest.TestCase):
    def setUp(self):
        from auto_trainer import ModelSelector
        self.selector = ModelSelector()

    def test_classification(self):
        result = self.selector.select({"task_type": "classification", "num_classes": 2})
        self.assertIn("classification", result)

    def test_multiclass(self):
        result = self.selector.select({"task_type": "classification", "num_classes": 5})
        self.assertIn("multiclass", result)

    def test_regression(self):
        result = self.selector.select({"task_type": "regression"})
        self.assertEqual(result, "regression")

    def test_language_model(self):
        result = self.selector.select({"task_type": "language"})
        self.assertEqual(result, "language_model")

    def test_text_classification(self):
        result = self.selector.select({"task_type": "classification", "has_text": True})
        self.assertEqual(result, "text_classification")

    def test_fallback(self):
        result = self.selector.select({})
        self.assertIsNotNone(result)


class TestHyperparamOptimizer(unittest.TestCase):
    def setUp(self):
        from auto_trainer import HyperparamOptimizer, TrainingConfig
        self.hpo = HyperparamOptimizer()
        self.base_cfg = TrainingConfig()

    def test_random_config(self):
        from auto_trainer import TrainingConfig
        cfg = self.hpo.random_config(self.base_cfg, seed=0)
        self.assertIsInstance(cfg, TrainingConfig)
        self.assertNotEqual(cfg.run_id, self.base_cfg.run_id)

    def test_grid_configs(self):
        configs = self.hpo.grid_configs(
            self.base_cfg,
            {"learning_rate": [1e-3, 1e-4], "batch_size": [16, 32]},
        )
        self.assertEqual(len(configs), 4)

    def test_random_config_custom_space(self):
        space = {"learning_rate": [1e-5, 1e-4]}
        cfg = self.hpo.random_config(self.base_cfg, space, seed=0)
        self.assertIn(cfg.learning_rate, [1e-5, 1e-4])


class TestCheckpointManager(unittest.TestCase):
    def setUp(self):
        from auto_trainer import CheckpointManager, TrainingConfig
        self.tmp = tempfile.mkdtemp()
        self.manager = CheckpointManager(self.tmp)
        self.cfg = TrainingConfig(run_id="test-run")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_and_load(self):
        ckpt = self.manager.save("test-run", 1, 10, 0.5, self.cfg)
        self.assertTrue(Path(ckpt.path).exists())
        data = self.manager.load(ckpt.path)
        self.assertEqual(data["epoch"], 1)

    def test_best_checkpoint(self):
        self.manager.save("test-run", 1, 10, 0.8, self.cfg)
        self.manager.save("test-run", 2, 20, 0.5, self.cfg)
        self.manager.save("test-run", 3, 30, 0.7, self.cfg)
        best = self.manager.best_checkpoint()
        self.assertAlmostEqual(best.val_loss, 0.5)


class TestAutoTrainer(unittest.TestCase):
    def setUp(self):
        from auto_trainer import AutoTrainer, TrainingConfig
        self.tmp = tempfile.mkdtemp()
        self.trainer = AutoTrainer(checkpoint_dir=self.tmp)
        self.TrainingConfig = TrainingConfig

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _records(self, n=30):
        return [{"x": i, "y": i * 2} for i in range(n)]

    def test_train_stub(self):
        from auto_trainer import TrainingResult
        train_recs = self._records(30)
        val_recs = self._records(10)
        cfg = self.TrainingConfig(epochs=3, run_id="test-stub")
        result = self.trainer.train(train_recs, val_recs, cfg)
        self.assertIsInstance(result, TrainingResult)
        self.assertGreater(len(result.metrics_history), 0)

    def test_custom_train_fn(self):
        counter = {"calls": 0}

        def my_fn(batch, cfg):
            counter["calls"] += 1
            return 0.5, 0.6

        records = self._records(10)
        cfg = self.TrainingConfig(epochs=2, run_id="custom-fn")
        result = self.trainer.train(records, [], cfg, train_fn=my_fn)
        self.assertGreater(counter["calls"], 0)

    def test_early_stopping(self):
        call_count = {"n": 0}

        def flat_fn(batch, cfg):
            call_count["n"] += 1
            return 0.5, 0.5  # constant val_loss - no improvement

        records = self._records(20)
        cfg = self.TrainingConfig(
            epochs=20,
            early_stopping_patience=2,
            run_id="early-stop",
        )
        result = self.trainer.train(records, records, cfg, train_fn=flat_fn)
        self.assertTrue(result.stopped_early)

    def test_hpo_search(self):
        records = self._records(20)
        cfg = self.TrainingConfig(epochs=2, run_id="hpo-base")
        best_cfg, results = self.trainer.hpo_search(records, records, cfg, n_trials=2)
        self.assertEqual(len(results), 2)
        self.assertIsNotNone(best_cfg)

    def test_model_selection(self):
        mt = self.trainer.select_model_type({"task_type": "classification"})
        self.assertIsNotNone(mt)


# ===========================================================================
# analytics_dashboard tests
# ===========================================================================

class TestASCIIChart(unittest.TestCase):
    def setUp(self):
        from analytics_dashboard import ASCIIChart
        self.chart = ASCIIChart

    def test_bar(self):
        bar = self.chart.bar(5, 10, "test")
        self.assertIn("50.0%", bar)

    def test_histogram(self):
        hist = self.chart.histogram([1.0, 2.0, 3.0, 4.0, 5.0], bins=5)
        self.assertIsInstance(hist, str)
        self.assertGreater(len(hist), 0)

    def test_histogram_empty(self):
        hist = self.chart.histogram([])
        self.assertEqual(hist, "(no data)")


class TestQualityHeatmap(unittest.TestCase):
    def setUp(self):
        from analytics_dashboard import QualityHeatmap
        self.hm = QualityHeatmap()

    def test_ascii_heatmap(self):
        result = self.hm.ascii_heatmap({"field_a": 10.0, "field_b": 75.0})
        self.assertIn("field_a", result)
        self.assertIn("field_b", result)

    def test_html_heatmap(self):
        result = self.hm.html_heatmap({"field_a": 0.0, "field_b": 100.0})
        self.assertIn("<table", result)
        self.assertIn("field_a", result)
        self.assertIn("field_b", result)

    def test_empty(self):
        result = self.hm.ascii_heatmap({})
        self.assertEqual(result, "(no data)")


class TestHTMLDashboard(unittest.TestCase):
    def setUp(self):
        from analytics_dashboard import HTMLDashboard
        self.dash = HTMLDashboard()

    def test_generates_html(self):
        html = self.dash.generate(title="Test Dashboard")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Test Dashboard", html)

    def test_includes_stats(self):
        stats = [{"field": "age", "type": "NUMERICAL_INT", "null_pct": 5.0, "unique_count": 30}]
        html = self.dash.generate(dataset_stats=stats, record_count=100)
        self.assertIn("age", html)

    def test_includes_training(self):
        history = [{"epoch": 1, "train_loss": 0.5, "val_loss": 0.6}]
        html_str = self.dash.generate(training_history=history)
        self.assertIn("Training Progress", html_str)


class TestAnalyticsDashboard(unittest.TestCase):
    def setUp(self):
        from analytics_dashboard import AnalyticsDashboard
        self.dash = AnalyticsDashboard()

    def test_update_dataset(self):
        self.dash.update_dataset(
            field_stats=[{"field": "x", "type": "INT", "null_pct": 0.0, "unique_count": 5}],
            null_pcts={"x": 0.0},
            quality_score=95.0,
            record_count=100,
        )
        self.assertEqual(self.dash._quality_score, 95.0)

    def test_render_html(self):
        html_str = self.dash.render_html("My Test")
        self.assertIn("<!DOCTYPE html>", html_str)

    def test_save_html(self):
        tmp = tempfile.mkdtemp()
        try:
            path = self.dash.save_html(Path(tmp) / "report.html")
            self.assertTrue(path.exists())
            content = path.read_text()
            self.assertIn("<!DOCTYPE html>", content)
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_print_summary(self):
        """Should not raise."""
        self.dash.update_dataset([], {}, 80.0, 50)
        import io as _io
        import contextlib
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.dash.print_summary()
        output = buf.getvalue()
        self.assertIn("80.0", output)


# ===========================================================================
# data_blob_godmode_kit integration tests
# ===========================================================================

class TestDataBlobGodmodeKit(unittest.TestCase):
    def setUp(self):
        from data_blob_godmode_kit import DataBlobGodmodeKit, GodmodeConfig
        self.tmp = tempfile.mkdtemp()
        cfg = GodmodeConfig(output_dir=self.tmp)
        self.kit = DataBlobGodmodeKit(config=cfg)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_json_file(self, n=50) -> str:
        rng = random.Random(1)
        records = [
            {"name": rng.choice(["Alice", "Bob"]), "score": rng.random(), "label": rng.randint(0, 1)}
            for _ in range(n)
        ]
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=self.tmp)
        json.dump(records, f)
        f.close()
        return f.name

    def test_ingest_file(self):
        fname = self._make_json_file(20)
        result = self.kit.ingest_file(fname)
        self.assertEqual(len(result.records), 20)
        self.assertEqual(len(self.kit.records), 20)

    def test_ingest_bytes(self):
        data = json.dumps([{"x": 1}, {"x": 2}]).encode()
        result = self.kit.ingest_bytes(data, hint="data.json")
        self.assertEqual(len(result.records), 2)

    def test_ingest_records(self):
        self.kit.ingest_records([{"a": 1}, {"a": 2}])
        self.assertEqual(len(self.kit.records), 2)

    def test_structure(self):
        from struct_engine import StructuredDataset
        self.kit.ingest_records([{"x": i, "y": i * 2} for i in range(20)])
        ds = self.kit.structure()
        self.assertIsInstance(ds, StructuredDataset)
        self.assertGreater(ds.quality_score, 0)

    def test_compile_dataset(self):
        from dataset_compiler import CompiledDataset
        fname = self._make_json_file(50)
        self.kit.ingest_file(fname)
        compiled = self.kit.compile_dataset(name="test")
        self.assertIsInstance(compiled, CompiledDataset)
        self.assertEqual(compiled.split.total, 50)

    def test_export_dataset(self):
        fname = self._make_json_file(30)
        self.kit.ingest_file(fname)
        compiled = self.kit.compile_dataset(name="exp_test")
        paths = self.kit.export_dataset(compiled, fmt="jsonl")
        self.assertIn("train", paths)

    def test_train(self):
        from auto_trainer import TrainingResult, TrainingConfig
        fname = self._make_json_file(40)
        self.kit.ingest_file(fname)
        compiled = self.kit.compile_dataset()
        cfg = TrainingConfig(epochs=2, run_id="kit-train-test")
        result = self.kit.train(compiled, config=cfg)
        self.assertIsInstance(result, TrainingResult)

    def test_pipeline(self):
        fname = self._make_json_file(40)
        pipeline_result = self.kit.run_pipeline(
            files=[fname],
            dataset_name="pipeline_test",
            run_training=True,
        )
        self.assertIn("dataset", pipeline_result)
        self.assertIn("export_paths", pipeline_result)

    def test_save_state(self):
        fname = self._make_json_file(20)
        self.kit.ingest_file(fname)
        self.kit.compile_dataset()
        state_path = self.kit.save_state()
        self.assertTrue(state_path.exists())
        state = json.loads(state_path.read_text())
        self.assertEqual(state["record_count"], 20)

    def test_clear_records(self):
        self.kit.ingest_records([{"a": 1}])
        self.kit.clear_records()
        self.assertEqual(len(self.kit.records), 0)

    def test_normalize(self):
        self.kit.ingest_records([{"v": 0}, {"v": 5}, {"v": 10}])
        normed = self.kit.normalize()
        self.assertAlmostEqual(normed[0]["v"], 0.0)
        self.assertAlmostEqual(normed[2]["v"], 1.0)


# ===========================================================================
# cli_godmode tests
# ===========================================================================

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_json_file(self, n=20) -> str:
        records = [{"x": i, "label": i % 2} for i in range(n)]
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=self.tmp)
        json.dump(records, f)
        f.close()
        return f.name

    def test_parse_cmd(self):
        from cli_godmode import main
        fname = self._make_json_file()
        ret = main(["parse", fname])
        self.assertEqual(ret, 0)

    def test_parse_cmd_json_format(self):
        from cli_godmode import main
        fname = self._make_json_file()
        import io as _io, contextlib
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            ret = main(["parse", fname, "--format", "json"])
        self.assertEqual(ret, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("record_count", output)

    def test_structure_cmd(self):
        from cli_godmode import main
        fname = self._make_json_file()
        ret = main(["structure", fname])
        self.assertEqual(ret, 0)

    def test_compile_cmd(self):
        from cli_godmode import main
        fname = self._make_json_file()
        ret = main(["compile", fname, "--name", "cli_test", "--output-dir", self.tmp])
        self.assertEqual(ret, 0)

    def test_train_cmd(self):
        from cli_godmode import main
        fname = self._make_json_file()
        ret = main(["train", fname, "--epochs", "2", "--output-dir", self.tmp])
        self.assertEqual(ret, 0)

    def test_pipeline_cmd(self):
        from cli_godmode import main
        fname = self._make_json_file()
        ret = main(["pipeline", fname, "--name", "pipe_test", "--epochs", "2", "--output-dir", self.tmp])
        self.assertEqual(ret, 0)

    def test_no_command_shows_help(self):
        from cli_godmode import main
        ret = main([])
        self.assertEqual(ret, 0)

    def test_build_parser(self):
        from cli_godmode import build_parser
        parser = build_parser()
        self.assertIsNotNone(parser)


# ===========================================================================
# Edge cases & stress tests
# ===========================================================================

class TestEdgeCases(unittest.TestCase):
    def test_empty_json_array(self):
        from smart_parser import SmartParser
        p = SmartParser()
        result = p.parse_bytes(b"[]", hint="x.json")
        self.assertEqual(result.records, [])

    def test_deeply_nested_json(self):
        from smart_parser import JSONParser
        p = JSONParser()
        data = json.dumps([{"a": {"b": {"c": 1}}}]).encode()
        result = p.parse_bytes(data)
        self.assertEqual(len(result.records), 1)

    def test_unicode_in_records(self):
        from smart_parser import JSONParser
        p = JSONParser()
        data = json.dumps([{"text": "こんにちは世界 🌍"}]).encode("utf-8")
        result = p.parse_bytes(data)
        self.assertEqual(result.records[0]["text"], "こんにちは世界 🌍")

    def test_large_csv(self):
        from smart_parser import SmartParser
        lines = ["id,value"] + [f"{i},{i*2}" for i in range(1000)]
        data = "\n".join(lines).encode()
        p = SmartParser()
        result = p.parse_bytes(data, hint="big.csv")
        self.assertEqual(len(result.records), 1000)

    def test_compiler_single_record(self):
        from dataset_compiler import DatasetCompiler
        c = DatasetCompiler()
        records = [{"x": 1}]
        ds = c.compile(records, name="single")
        self.assertEqual(ds.split.total, 1)

    def test_trainer_no_val_records(self):
        from auto_trainer import AutoTrainer, TrainingConfig
        t = AutoTrainer(checkpoint_dir=tempfile.mkdtemp())
        cfg = TrainingConfig(epochs=2, run_id="no-val")
        result = t.train([{"x": i} for i in range(10)], [], cfg)
        self.assertGreater(len(result.metrics_history), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
