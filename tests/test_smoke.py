"""
tests/test_smoke.py – fast smoke tests for Victor LLM.

Tests:
  1. Import / package sanity checks.
  2. CLI help and command wiring.
  3. Dataset prepare on example_dataset.
  4. Tiny training run (2 epochs, few samples) completes quickly.
  5. Inference on a known prompt returns non-empty output.
  6. Benchmark runs and produces a result file.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DATASET = REPO_ROOT / "datasets" / "example_dataset"


# ---------------------------------------------------------------------------
# 1. Import smoke tests
# ---------------------------------------------------------------------------

class TestImports:
    def test_smart_parser_importable(self):
        import smart_parser  # noqa: F401

    def test_auto_trainer_importable(self):
        import auto_trainer  # noqa: F401

    def test_data_blob_godmode_kit_importable(self):
        import data_blob_godmode_kit  # noqa: F401

    def test_dataset_compiler_importable(self):
        import dataset_compiler  # noqa: F401

    def test_cli_godmode_importable(self):
        import cli_godmode  # noqa: F401

    def test_victor_cli_main_importable(self):
        from victor_cli.main import build_parser  # noqa: F401

    def test_victor_cli_dataset_importable(self):
        from victor_cli.dataset import prepare_dataset  # noqa: F401

    def test_victor_cli_training_importable(self):
        from victor_cli.training import run_training  # noqa: F401

    def test_victor_cli_inference_importable(self):
        from victor_cli.inference import run_predict  # noqa: F401

    def test_victor_cli_benchmark_importable(self):
        from victor_cli.benchmark import run_benchmark  # noqa: F401

    def test_fractal_tokenizer_importable(self):
        from victor_core.nlp.fractal_tokenizer import FractalTokenKernel_v1_1_0  # noqa: F401


# ---------------------------------------------------------------------------
# 2. CLI help / command wiring
# ---------------------------------------------------------------------------

class TestCLI:
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(REPO_ROOT / "victor_cli_entry.py"), *args]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_help_exits_zero(self):
        result = self._run("--help")
        assert result.returncode == 0
        assert "victor" in result.stdout.lower()

    def test_prepare_help(self):
        result = self._run("prepare", "--help")
        assert result.returncode == 0
        assert "--dataset" in result.stdout

    def test_train_help(self):
        result = self._run("train", "--help")
        assert result.returncode == 0
        assert "--epochs" in result.stdout

    def test_eval_help(self):
        result = self._run("eval", "--help")
        assert result.returncode == 0
        assert "--checkpoint" in result.stdout

    def test_predict_help(self):
        result = self._run("predict", "--help")
        assert result.returncode == 0
        assert "--prompt" in result.stdout

    def test_benchmark_help(self):
        result = self._run("benchmark", "--help")
        assert result.returncode == 0
        assert "--prompts" in result.stdout

    def test_unknown_subcommand_exits_nonzero(self):
        result = self._run("unknown_subcommand")
        assert result.returncode != 0

    def test_victor_cli_main_build_parser(self):
        from victor_cli.main import build_parser

        parser = build_parser()
        assert parser is not None

    def test_victor_cli_prepare_parses(self):
        from victor_cli.main import build_parser

        parser = build_parser()
        args = parser.parse_args(["prepare", "--dataset", "some/path"])
        assert args.command == "prepare"
        assert args.dataset == "some/path"

    def test_victor_cli_train_defaults(self):
        from victor_cli.main import build_parser

        parser = build_parser()
        args = parser.parse_args(["train", "--dataset", "some/path"])
        assert args.epochs == 5
        assert args.batch_size == 32
        assert abs(args.lr - 1e-3) < 1e-10  # use approx for float comparison


# ---------------------------------------------------------------------------
# 3. Dataset prepare
# ---------------------------------------------------------------------------

class TestDatasetPrepare:
    def test_example_dataset_exists(self):
        assert EXAMPLE_DATASET.exists(), f"Example dataset missing: {EXAMPLE_DATASET}"

    def test_train_split_exists(self):
        assert (EXAMPLE_DATASET / "train.jsonl").exists()

    def test_valid_split_exists(self):
        assert (EXAMPLE_DATASET / "valid.jsonl").exists()

    def test_test_split_exists(self):
        assert (EXAMPLE_DATASET / "test.jsonl").exists()

    def test_prepare_returns_zero(self):
        from victor_cli.dataset import prepare_dataset

        rc = prepare_dataset(EXAMPLE_DATASET, verbose=False)
        assert rc == 0

    def test_prepare_nonexistent_dir_returns_one(self):
        from victor_cli.dataset import prepare_dataset

        rc = prepare_dataset(Path("/nonexistent/dataset/path"))
        assert rc == 1

    def test_load_split_returns_records(self):
        from victor_cli.dataset import load_split

        records = load_split(EXAMPLE_DATASET, "train")
        assert len(records) >= 1
        assert isinstance(records[0], dict)

    def test_train_split_has_text_and_label(self):
        from victor_cli.dataset import load_split

        records = load_split(EXAMPLE_DATASET, "train")
        assert all("text" in r and "label" in r for r in records)

    def test_dataset_yaml_present(self):
        assert (EXAMPLE_DATASET / "dataset.yaml").exists()

    def test_prepare_missing_train_split(self, tmp_path):
        from victor_cli.dataset import prepare_dataset

        (tmp_path / "valid.jsonl").write_text('{"text": "x"}\n')
        rc = prepare_dataset(tmp_path)
        assert rc == 1  # missing train.jsonl

    def test_prepare_invalid_jsonl(self, tmp_path):
        from victor_cli.dataset import prepare_dataset

        (tmp_path / "train.jsonl").write_text("not json\n{valid}\n")
        rc = prepare_dataset(tmp_path)
        # Should still return 0 (warnings only), but with error count > 0.
        assert rc == 0


# ---------------------------------------------------------------------------
# 4. Tiny training run
# ---------------------------------------------------------------------------

class TestTraining:
    def test_tiny_training_completes(self, tmp_path):
        from victor_cli.training import run_training

        rc = run_training(
            dataset_dir=EXAMPLE_DATASET,
            output_dir=tmp_path / "runs",
            epochs=1,
            batch_size=4,
            lr=1e-3,
            model_type="classification",
            seed=0,
        )
        assert rc == 0

    def test_training_produces_summary(self, tmp_path):
        from victor_cli.training import run_training

        output_dir = tmp_path / "runs"
        rc = run_training(
            dataset_dir=EXAMPLE_DATASET,
            output_dir=output_dir,
            epochs=1,
            batch_size=4,
            lr=1e-3,
            seed=99,
        )
        assert rc == 0
        summaries = list(output_dir.rglob("training_summary.json"))
        assert len(summaries) == 1
        summary = json.loads(summaries[0].read_text())
        assert "run_id" in summary
        assert summary.get("epochs", summary.get("epochs_completed", 0)) >= 1

    def test_training_produces_checkpoint(self, tmp_path):
        from victor_cli.training import run_training

        output_dir = tmp_path / "runs"
        run_training(
            dataset_dir=EXAMPLE_DATASET,
            output_dir=output_dir,
            epochs=1,
            batch_size=4,
            seed=7,
        )
        checkpoints = list(output_dir.rglob("epoch_*.json"))
        assert len(checkpoints) >= 1

    def test_training_with_config_file(self, tmp_path):
        import json

        from victor_cli.training import run_training

        config = {"epochs": 1, "batch_size": 2, "seed": 11}
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps(config))

        rc = run_training(
            dataset_dir=EXAMPLE_DATASET,
            output_dir=tmp_path / "runs",
            epochs=5,  # will be overridden by config file
            batch_size=32,  # will be overridden
            config_file=str(cfg_file),
        )
        assert rc == 0


# ---------------------------------------------------------------------------
# 5. Inference
# ---------------------------------------------------------------------------

class TestInference:
    def test_predict_no_checkpoint_returns_zero(self, capsys):
        from victor_cli.inference import run_predict

        rc = run_predict(prompts=["Hello, Victor!"], checkpoint=None, max_tokens=16)
        assert rc == 0

    def test_predict_output_is_non_empty(self, capsys):
        from victor_cli.inference import run_predict

        run_predict(prompts=["Tell me about AI"], checkpoint=None, max_tokens=16)
        captured = capsys.readouterr()
        assert len(captured.out.strip()) > 0

    def test_predict_multiple_prompts(self, capsys):
        from victor_cli.inference import run_predict

        rc = run_predict(
            prompts=["First prompt", "Second prompt", "Third prompt"],
            checkpoint=None,
            max_tokens=8,
        )
        assert rc == 0
        captured = capsys.readouterr()
        # Expect 3 prompt/response pairs in output.
        assert captured.out.count("Prompt") >= 3

    def test_predict_empty_prompts_returns_one(self):
        from victor_cli.inference import run_predict

        rc = run_predict(prompts=[], checkpoint=None)
        assert rc == 1

    def test_simple_generate_returns_string(self):
        from victor_cli.inference import _simple_generate

        vocab = {"hello": 0, "world": 1, "victor": 2}
        rev_vocab = {0: "hello", 1: "world", 2: "victor"}
        result = _simple_generate("hello world", vocab, rev_vocab, max_tokens=5)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_predict_after_training(self, tmp_path):
        """Inference using a freshly trained checkpoint produces non-empty output."""
        from victor_cli.training import run_training
        from victor_cli.inference import run_predict
        import io
        from contextlib import redirect_stdout

        output_dir = tmp_path / "runs"
        run_training(
            dataset_dir=EXAMPLE_DATASET,
            output_dir=output_dir,
            epochs=1,
            batch_size=4,
            seed=5,
        )
        checkpoints = sorted(output_dir.rglob("epoch_*.json"))
        assert checkpoints, "No checkpoints produced."

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = run_predict(
                prompts=["Victor LLM"],
                checkpoint=str(checkpoints[-1]),
                max_tokens=10,
            )
        assert rc == 0
        assert len(buf.getvalue().strip()) > 0


# ---------------------------------------------------------------------------
# 6. Benchmark
# ---------------------------------------------------------------------------

class TestBenchmark:
    def test_benchmark_runs(self, tmp_path):
        from victor_cli.benchmark import run_benchmark

        rc = run_benchmark(
            checkpoint=None,
            num_prompts=3,
            max_tokens=8,
            output_dir=tmp_path / "results",
        )
        assert rc == 0

    def test_benchmark_produces_json(self, tmp_path):
        from victor_cli.benchmark import run_benchmark

        results_dir = tmp_path / "results"
        run_benchmark(
            checkpoint=None,
            num_prompts=3,
            max_tokens=8,
            output_dir=results_dir,
        )
        result_files = list(results_dir.glob("benchmark_*.json"))
        assert len(result_files) == 1
        data = json.loads(result_files[0].read_text())
        assert data["num_prompts"] == 3
        assert "latency_mean_s" in data
        assert "throughput_tokens_per_s" in data

    def test_benchmark_throughput_positive(self, tmp_path):
        from victor_cli.benchmark import run_benchmark

        results_dir = tmp_path / "results"
        run_benchmark(
            checkpoint=None,
            num_prompts=5,
            max_tokens=16,
            output_dir=results_dir,
        )
        data = json.loads(list(results_dir.glob("*.json"))[0].read_text())
        assert data["throughput_tokens_per_s"] > 0
