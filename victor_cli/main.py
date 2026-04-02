#!/usr/bin/env python3
"""
victor – production CLI for Victor LLM.

Subcommands
-----------
  prepare   Validate and preprocess a dataset folder.
  train     Fine-tune or train from scratch on a dataset folder.
  eval      Evaluate a trained checkpoint on a dataset split.
  predict   Run inference on one or more prompts.
  benchmark Measure latency, throughput and memory of a checkpoint.

Examples
--------
  victor prepare  --dataset datasets/example_dataset
  victor train    --dataset datasets/example_dataset --epochs 3
  victor eval     --dataset datasets/example_dataset --checkpoint runs/my_run
  victor predict  --prompt "Hello, Victor!"
  victor benchmark --checkpoint runs/my_run --prompts 20
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger("victor")


# ---------------------------------------------------------------------------
# Logging bootstrap
# ---------------------------------------------------------------------------

def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    return Path(__file__).parent.parent.resolve()


def _default_artifacts_dir() -> Path:
    return _repo_root() / "runs"


def _resolve_dataset(dataset_arg: str) -> Path:
    p = Path(dataset_arg).expanduser()
    if not p.is_absolute():
        # Try relative to cwd first, then relative to repo root.
        cwd_p = (Path.cwd() / p).resolve()
        if cwd_p.exists():
            return cwd_p
        root_p = (_repo_root() / p).resolve()
        if root_p.exists():
            return root_p
        return cwd_p  # Return cwd-relative; error will be raised downstream.
    return p.resolve()


# ---------------------------------------------------------------------------
# Subcommand: prepare
# ---------------------------------------------------------------------------

def cmd_prepare(args: argparse.Namespace) -> int:
    """Validate dataset layout and report statistics."""
    from victor_cli.dataset import prepare_dataset

    dataset_dir = _resolve_dataset(args.dataset)
    return prepare_dataset(dataset_dir, verbose=args.verbose)


# ---------------------------------------------------------------------------
# Subcommand: train
# ---------------------------------------------------------------------------

def cmd_train(args: argparse.Namespace) -> int:
    """Train / fine-tune on a dataset folder."""
    from victor_cli.training import run_training

    dataset_dir = _resolve_dataset(args.dataset)
    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else _default_artifacts_dir()
    )
    return run_training(
        dataset_dir=dataset_dir,
        output_dir=output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        model_type=args.model_type,
        checkpoint=args.checkpoint,
        config_file=args.config,
        seed=args.seed,
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Subcommand: eval
# ---------------------------------------------------------------------------

def cmd_eval(args: argparse.Namespace) -> int:
    """Evaluate a checkpoint on a dataset split."""
    from victor_cli.evaluation import run_eval

    dataset_dir = _resolve_dataset(args.dataset)
    return run_eval(
        dataset_dir=dataset_dir,
        checkpoint=args.checkpoint,
        split=args.split,
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Subcommand: predict
# ---------------------------------------------------------------------------

def cmd_predict(args: argparse.Namespace) -> int:
    """Run inference on prompts."""
    from victor_cli.inference import run_predict

    prompts: list[str] = []
    if args.prompt:
        prompts.extend(args.prompt)
    if args.prompts_file:
        pf = Path(args.prompts_file).expanduser()
        for line in pf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                prompts.append(line)

    if not prompts:
        logger.error("Provide at least one prompt via --prompt or --prompts-file.")
        return 1

    return run_predict(
        prompts=prompts,
        checkpoint=args.checkpoint,
        max_tokens=args.max_tokens,
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Subcommand: benchmark
# ---------------------------------------------------------------------------

def cmd_benchmark(args: argparse.Namespace) -> int:
    """Benchmark inference latency / throughput / memory."""
    from victor_cli.benchmark import run_benchmark

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else _repo_root() / "benchmarks" / "results"
    )
    return run_benchmark(
        checkpoint=args.checkpoint,
        num_prompts=args.prompts,
        max_tokens=args.max_tokens,
        output_dir=output_dir,
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="victor",
        description="Victor LLM – production CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")

    subs = parser.add_subparsers(dest="command", metavar="<command>")
    subs.required = True

    # ---- prepare ----
    p_prep = subs.add_parser("prepare", help="Validate and preprocess a dataset folder.")
    p_prep.add_argument("--dataset", required=True, metavar="DIR", help="Path to dataset directory.")
    p_prep.set_defaults(func=cmd_prepare)

    # ---- train ----
    p_train = subs.add_parser("train", help="Train / fine-tune on a dataset folder.")
    p_train.add_argument("--dataset", required=True, metavar="DIR", help="Path to dataset directory.")
    p_train.add_argument("--output-dir", metavar="DIR", help="Directory to save run artifacts (default: ./runs).")
    p_train.add_argument("--epochs", type=int, default=5, help="Number of training epochs (default: 5).")
    p_train.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32).")
    p_train.add_argument("--lr", type=float, default=1e-3, help="Learning rate (default: 1e-3).")
    p_train.add_argument(
        "--model-type",
        default="auto",
        help="Model type: auto | classification | language_model (default: auto).",
    )
    p_train.add_argument("--checkpoint", metavar="PATH", help="Resume from or fine-tune a saved checkpoint.")
    p_train.add_argument("--config", metavar="FILE", help="YAML/JSON config file (overrides CLI flags).")
    p_train.add_argument("--seed", type=int, default=42, help="Random seed (default: 42).")
    p_train.set_defaults(func=cmd_train)

    # ---- eval ----
    p_eval = subs.add_parser("eval", help="Evaluate a checkpoint on a dataset split.")
    p_eval.add_argument("--dataset", required=True, metavar="DIR", help="Path to dataset directory.")
    p_eval.add_argument("--checkpoint", required=True, metavar="PATH", help="Checkpoint directory or file.")
    p_eval.add_argument(
        "--split",
        default="test",
        choices=["train", "valid", "test"],
        help="Dataset split to evaluate (default: test).",
    )
    p_eval.set_defaults(func=cmd_eval)

    # ---- predict ----
    p_pred = subs.add_parser("predict", help="Run inference on one or more prompts.")
    p_pred.add_argument("--prompt", nargs="+", metavar="TEXT", help="One or more prompt strings.")
    p_pred.add_argument("--prompts-file", metavar="FILE", help="File with one prompt per line.")
    p_pred.add_argument("--checkpoint", metavar="PATH", help="Checkpoint to use for inference.")
    p_pred.add_argument("--max-tokens", type=int, default=64, help="Maximum tokens to generate (default: 64).")
    p_pred.set_defaults(func=cmd_predict)

    # ---- benchmark ----
    p_bench = subs.add_parser("benchmark", help="Benchmark inference performance.")
    p_bench.add_argument("--checkpoint", metavar="PATH", help="Checkpoint to benchmark.")
    p_bench.add_argument(
        "--prompts", type=int, default=10, metavar="N", help="Number of synthetic prompts (default: 10)."
    )
    p_bench.add_argument("--max-tokens", type=int, default=64, help="Tokens per generation (default: 64).")
    p_bench.add_argument(
        "--output-dir", metavar="DIR", help="Where to save JSON results (default: benchmarks/results)."
    )
    p_bench.set_defaults(func=cmd_benchmark)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
