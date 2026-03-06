"""
cli_godmode.py - Command-Line Interface for the DataBlob Godmode Toolkit
Part of the Victor LLM ecosystem

Subcommands:
  parse       - Parse a data file and print records / schema
  structure   - Analyse and structure a dataset
  compile     - Compile a dataset from one or more files
  train       - Run automated training on a compiled dataset
  pipeline    - Run the full end-to-end pipeline
  dashboard   - Launch the analytics web dashboard
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cli_godmode")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, default=str))


def _import_kit():
    """Lazy-import the kit to keep startup fast."""
    from data_blob_godmode_kit import DataBlobGodmodeKit, GodmodeConfig
    return DataBlobGodmodeKit, GodmodeConfig


# ---------------------------------------------------------------------------
# Subcommand: parse
# ---------------------------------------------------------------------------

def cmd_parse(args: argparse.Namespace) -> int:
    from smart_parser import SmartParser, DataFormat

    parser = SmartParser()
    result = parser.parse_file(args.file)

    if args.format == "json":
        output: Dict[str, Any] = {
            "source": result.source,
            "format": result.format.name,
            "record_count": len(result.records),
            "schema": result.schema,
            "errors": result.errors,
            "metadata": result.metadata,
        }
        if args.show_records:
            output["records"] = result.records[: args.limit]
        _print_json(output)
    else:
        print(f"Source  : {result.source}")
        print(f"Format  : {result.format.name}")
        print(f"Records : {len(result.records)}")
        print(f"Errors  : {len(result.errors)}")
        if result.errors:
            for err in result.errors[:5]:
                print(f"  ⚠  {err}")
        print(f"\nSchema ({len(result.schema)} fields):")
        for field in result.schema:
            print(f"  {field['name']:<30} {field['type']:<15} nullable={field.get('nullable', '?')}")
        if args.show_records and result.records:
            print(f"\nSample records (first {min(args.limit, len(result.records))}):")
            for rec in result.records[: args.limit]:
                print(" ", json.dumps(rec, default=str))
    return 0


# ---------------------------------------------------------------------------
# Subcommand: structure
# ---------------------------------------------------------------------------

def cmd_structure(args: argparse.Namespace) -> int:
    from smart_parser import SmartParser
    from struct_engine import StructEngine

    parser = SmartParser()
    result = parser.parse_file(args.file)
    if result.errors and not result.records:
        print(f"Error: could not parse {args.file}: {result.errors}", file=sys.stderr)
        return 1

    engine = StructEngine()
    dataset = engine.structure(result.records, source_name=str(args.file))

    if args.format == "json":
        _print_json({
            "quality_score": dataset.quality_score,
            "record_count": len(dataset.records),
            "field_types": {k: v.name for k, v in dataset.field_types.items()},
            "anomaly_count": len(dataset.anomalies),
            "field_stats": dataset.field_stats,
            "anomalies": dataset.anomalies[:20],
            "metadata": dataset.metadata,
        })
    else:
        print(f"Quality score : {dataset.quality_score:.1f}/100")
        print(f"Records       : {len(dataset.records)}")
        print(f"Fields        : {len(dataset.field_types)}")
        print(f"Anomalies     : {len(dataset.anomalies)}")
        print()
        print(f"{'Field':<30} {'Type':<20} {'Null%':>6}")
        print("-" * 60)
        null_pcts = dataset.metadata.get("null_percentages", {})
        for fname, ftype in sorted(dataset.field_types.items()):
            null_p = null_pcts.get(fname, 0.0)
            print(f"{fname:<30} {ftype.name:<20} {null_p:>5.1f}%")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: compile
# ---------------------------------------------------------------------------

def cmd_compile(args: argparse.Namespace) -> int:
    DataBlobGodmodeKit, GodmodeConfig = _import_kit()

    cfg = GodmodeConfig(
        output_dir=args.output_dir,
        default_export_format=args.export_fmt,
    )
    kit = DataBlobGodmodeKit(config=cfg)

    for f in args.files:
        kit.ingest_file(f)

    if args.structure:
        kit.structure()

    from dataset_compiler import SplitConfig
    split_cfg = SplitConfig(
        train=args.train_ratio,
        val=args.val_ratio,
        test=1.0 - args.train_ratio - args.val_ratio,
        stratify_field=args.label_field,
        seed=args.seed,
    )

    dataset = kit.compile_dataset(
        name=args.name,
        split_config=split_cfg,
        label_field=args.label_field,
        balance_strategy=args.balance,
    )

    export_paths = kit.export_dataset(
        dataset,
        output_dir=Path(args.output_dir) / "datasets",
        fmt=args.export_fmt,
    )

    print(f"✅ Dataset '{args.name}' compiled (v{dataset.version})")
    print(f"   Train : {len(dataset.split.train)}")
    print(f"   Val   : {len(dataset.split.val)}")
    print(f"   Test  : {len(dataset.split.test)}")
    print("   Exported to:")
    for split_name, path in export_paths.items():
        print(f"     {split_name}: {path}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: train
# ---------------------------------------------------------------------------

def cmd_train(args: argparse.Namespace) -> int:
    DataBlobGodmodeKit, GodmodeConfig = _import_kit()

    cfg = GodmodeConfig(
        output_dir=args.output_dir,
        checkpoint_dir=args.checkpoint_dir or None,
    )
    kit = DataBlobGodmodeKit(config=cfg)

    for f in args.files:
        kit.ingest_file(f)

    kit.structure()

    dataset = kit.compile_dataset(
        name=args.name,
        label_field=args.label_field,
        balance_strategy=args.balance,
    )

    from auto_trainer import TrainingConfig
    train_cfg = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        model_type=args.model_type or "auto",
        output_dir=str(cfg.checkpoint_dir),
        seed=args.seed,
    )

    result = kit.train(dataset, config=train_cfg)
    summary = result.summary()

    print(f"\n✅ Training complete — run_id: {summary['run_id']}")
    print(f"   Epochs       : {summary['epochs']}")
    print(f"   Time         : {summary['total_time_seconds']:.1f}s")
    print(f"   Final train  : {summary['final_train_loss']}")
    print(f"   Best val     : {summary['best_val_loss']}")
    print(f"   Checkpoint   : {summary['best_checkpoint']}")

    if args.report:
        report = kit.save_report(Path(args.output_dir) / "report.html")
        print(f"   Report       : {report}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: pipeline
# ---------------------------------------------------------------------------

def cmd_pipeline(args: argparse.Namespace) -> int:
    DataBlobGodmodeKit, GodmodeConfig = _import_kit()

    cfg = GodmodeConfig(
        output_dir=args.output_dir,
        default_export_format=args.export_fmt,
    )
    kit = DataBlobGodmodeKit(config=cfg)

    from auto_trainer import TrainingConfig
    train_cfg = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        model_type=args.model_type or "auto",
        seed=args.seed,
    )

    pipeline_result = kit.run_pipeline(
        files=args.files,
        dataset_name=args.name,
        label_field=args.label_field,
        balance_strategy=args.balance,
        export_fmt=args.export_fmt,
        train_config=train_cfg,
        run_training=not args.no_train,
        save_report=True,
    )

    print(f"\n✅ Pipeline complete!")
    ds = pipeline_result["dataset"]
    print(f"   Dataset : {ds.name} v{ds.version}")
    print(f"   Report  : {pipeline_result['report_path']}")
    if pipeline_result.get("training_result"):
        tr = pipeline_result["training_result"]
        print(f"   Run ID  : {tr.run_id}")
        print(f"   Best val loss : {tr.summary().get('best_val_loss')}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: dashboard
# ---------------------------------------------------------------------------

def cmd_dashboard(args: argparse.Namespace) -> int:
    import time as _time

    DataBlobGodmodeKit, GodmodeConfig = _import_kit()

    cfg = GodmodeConfig(
        output_dir=args.output_dir,
        dashboard_port=args.port,
    )
    kit = DataBlobGodmodeKit(config=cfg)

    # Load data if files given
    for f in (args.files or []):
        kit.ingest_file(f)
    if kit.records:
        kit.structure()
    if kit.records and not kit.compiled_dataset:
        kit.compile_dataset()

    kit.serve_dashboard(port=args.port)

    print(f"Dashboard running at http://127.0.0.1:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            _time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
        kit.stop_server() if hasattr(kit, 'stop_server') else None
    return 0


# ---------------------------------------------------------------------------
# CLI parser setup
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="godmode",
        description="DataBlob Godmode Toolkit — Victor LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  godmode parse data.json --show-records\n"
            "  godmode structure data.csv\n"
            "  godmode compile data.json data.csv --name myds --export-fmt jsonl\n"
            "  godmode train data.json --epochs 5 --label target\n"
            "  godmode pipeline data.json --name exp1 --epochs 10\n"
            "  godmode dashboard data.json --port 8787\n"
        ),
    )
    root.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    subs = root.add_subparsers(dest="command")

    # -- parse --
    p_parse = subs.add_parser("parse", help="Parse a data file")
    p_parse.add_argument("file", help="Path to data file")
    p_parse.add_argument("--show-records", action="store_true", help="Print sample records")
    p_parse.add_argument("--limit", type=int, default=5, help="Max records to show")
    p_parse.add_argument("--format", choices=["text", "json"], default="text")

    # -- structure --
    p_struct = subs.add_parser("structure", help="Analyse and structure a dataset")
    p_struct.add_argument("file", help="Path to data file")
    p_struct.add_argument("--format", choices=["text", "json"], default="text")

    # -- compile --
    p_compile = subs.add_parser("compile", help="Compile a dataset")
    p_compile.add_argument("files", nargs="+", help="Input files")
    p_compile.add_argument("--name", default="dataset", help="Dataset name")
    p_compile.add_argument("--output-dir", default="./godmode_output", help="Output directory")
    p_compile.add_argument("--export-fmt", default="jsonl", choices=["jsonl", "json", "csv", "huggingface", "pytorch", "tensorflow"])
    p_compile.add_argument("--label-field", default=None)
    p_compile.add_argument("--balance", default=None, choices=["oversample", "undersample"])
    p_compile.add_argument("--train-ratio", type=float, default=0.7)
    p_compile.add_argument("--val-ratio", type=float, default=0.15)
    p_compile.add_argument("--seed", type=int, default=42)
    p_compile.add_argument("--structure", action="store_true", help="Run structuring step")

    # -- train --
    p_train = subs.add_parser("train", help="Run automated training")
    p_train.add_argument("files", nargs="+", help="Input files")
    p_train.add_argument("--name", default="dataset")
    p_train.add_argument("--output-dir", default="./godmode_output")
    p_train.add_argument("--checkpoint-dir", default=None)
    p_train.add_argument("--label-field", default=None)
    p_train.add_argument("--balance", default=None, choices=["oversample", "undersample"])
    p_train.add_argument("--epochs", type=int, default=5)
    p_train.add_argument("--batch-size", type=int, default=32)
    p_train.add_argument("--lr", type=float, default=1e-3)
    p_train.add_argument("--model-type", default=None)
    p_train.add_argument("--seed", type=int, default=42)
    p_train.add_argument("--report", action="store_true")

    # -- pipeline --
    p_pipe = subs.add_parser("pipeline", help="Full end-to-end pipeline")
    p_pipe.add_argument("files", nargs="+", help="Input files")
    p_pipe.add_argument("--name", default="dataset")
    p_pipe.add_argument("--output-dir", default="./godmode_output")
    p_pipe.add_argument("--export-fmt", default="jsonl")
    p_pipe.add_argument("--label-field", default=None)
    p_pipe.add_argument("--balance", default=None, choices=["oversample", "undersample"])
    p_pipe.add_argument("--epochs", type=int, default=5)
    p_pipe.add_argument("--batch-size", type=int, default=32)
    p_pipe.add_argument("--lr", type=float, default=1e-3)
    p_pipe.add_argument("--model-type", default=None)
    p_pipe.add_argument("--seed", type=int, default=42)
    p_pipe.add_argument("--no-train", action="store_true", help="Skip training step")

    # -- dashboard --
    p_dash = subs.add_parser("dashboard", help="Launch analytics dashboard")
    p_dash.add_argument("files", nargs="*", help="Optional data files to load")
    p_dash.add_argument("--output-dir", default="./godmode_output")
    p_dash.add_argument("--port", type=int, default=8787)

    return root


def main(argv: Optional[List[str]] = None) -> int:
    root = build_parser()
    args = root.parse_args(argv)
    _setup_logging(getattr(args, "verbose", False))

    dispatch = {
        "parse": cmd_parse,
        "structure": cmd_structure,
        "compile": cmd_compile,
        "train": cmd_train,
        "pipeline": cmd_pipeline,
        "dashboard": cmd_dashboard,
    }

    if not args.command:
        root.print_help()
        return 0

    handler = dispatch.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        logger.error("Command failed: %s", exc, exc_info=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
