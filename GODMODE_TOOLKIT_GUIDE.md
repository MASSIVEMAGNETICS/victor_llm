# GODMODE TOOLKIT GUIDE

## DataBlob Godmode Toolkit for Victor LLM

**Version:** 1.0.0  
**Status:** Production-Ready  
**License:** Victor LLM Ecosystem

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Module Reference](#module-reference)
   - [SmartParser](#smartparser)
   - [StructEngine](#structengine)
   - [DatasetCompiler](#datasetcompiler)
   - [AutoTrainer](#autotrainer)
   - [AnalyticsDashboard](#analyticsdashboard)
   - [DataBlobGodmodeKit](#datablob-godmode-kit)
6. [CLI Interface](#cli-interface)
7. [Integration with Victor LLM](#integration-with-victor-llm)
8. [Testing](#testing)
9. [Examples](#examples)

---

## Overview

The **DataBlob Godmode Toolkit** is a production-grade data ingestion, structuring, and AI training automation system designed for the Victor LLM ecosystem.  It provides:

- **Multi-format parsing** – JSON, JSONL, XML, CSV, TSV, Parquet, Protocol Buffers, binary, plain text
- **Intelligent structuring** – automatic type inference, normalization, quality scoring, anomaly detection
- **Smart dataset compilation** – train/val/test splits, class balance handling, multiple export formats
- **Automated training** – model selection, hyperparameter search, checkpointing, early stopping
- **Visual analytics** – ASCII dashboards, HTML reports, optional live web dashboard

The toolkit is implemented in pure Python with **zero mandatory external dependencies** (numpy, pandas, pyarrow are used when available for Parquet support but are otherwise optional).

---

## Architecture

```
DataBlobGodmodeKit (orchestrator)
├── SmartParser        → data_blob_godmode_kit → struct_engine → dataset_compiler → auto_trainer
│   ├── JSONParser
│   ├── JSONLParser
│   ├── XMLParser
│   ├── CSVParser / TSVParser
│   ├── TextParser
│   ├── BinaryParser
│   ├── ParquetParser  (optional: pyarrow / pandas)
│   └── ProtobufParser (stub, descriptor required)
├── StructEngine
│   ├── TypeInferrer
│   ├── FieldStats
│   ├── Normalizer
│   ├── AnomalyDetector
│   ├── QualityScorer
│   └── RelationshipDetector
├── DatasetCompiler
│   ├── Splitter
│   ├── ClassBalanceAnalyser
│   ├── DatasetExporter
│   └── ManifestGenerator
├── AutoTrainer
│   ├── ModelSelector
│   ├── HyperparamOptimizer
│   ├── CheckpointManager
│   ├── MetricsTracker
│   └── VictorTrainingHook
└── AnalyticsDashboard
    ├── ASCIIChart
    ├── QualityHeatmap
    ├── TrainingProgressDisplay
    ├── DatasetStatsVisualiser
    ├── HTMLDashboard
    └── DashboardServer
```

---

## Installation

No installation is required beyond Python 3.9+.  Optional dependencies enhance functionality:

```bash
# Optional: Parquet support
pip install pyarrow

# or
pip install pandas pyarrow

# Optional: faster CSV / type inference
pip install numpy
```

All toolkit files should reside in the same directory (the Victor LLM repository root):

```
victor_llm/
├── data_blob_godmode_kit.py
├── smart_parser.py
├── struct_engine.py
├── dataset_compiler.py
├── auto_trainer.py
├── analytics_dashboard.py
├── cli_godmode.py
└── test_godmode_toolkit.py
```

---

## Quick Start

### Python API

```python
from data_blob_godmode_kit import DataBlobGodmodeKit

kit = DataBlobGodmodeKit(output_dir="./my_output")

# Ingest data
kit.ingest_file("data.json")
kit.ingest_file("more_data.csv")

# Structure and analyse
dataset_info = kit.structure()
print(f"Quality score: {dataset_info.quality_score:.1f}/100")

# Compile a dataset
compiled = kit.compile_dataset(
    name="my_dataset",
    label_field="category",
    balance_strategy="oversample",
)

# Export to disk
paths = kit.export_dataset(compiled, fmt="jsonl")

# Train
result = kit.train(compiled)
print(result.summary())

# Generate HTML report
kit.save_report("report.html")
```

### Full Pipeline (One Call)

```python
from data_blob_godmode_kit import DataBlobGodmodeKit

kit = DataBlobGodmodeKit(output_dir="./output")
result = kit.run_pipeline(
    files=["train_data.json", "extra_data.csv"],
    dataset_name="my_experiment",
    label_field="label",
    balance_strategy="oversample",
    export_fmt="jsonl",
    run_training=True,
    save_report=True,
)
print(result["training_result"].summary())
```

---

## Module Reference

### SmartParser

**File:** `smart_parser.py`

Multi-format data parser with automatic format detection.

#### `SmartParser`

```python
from smart_parser import SmartParser, DataFormat

parser = SmartParser(chunk_size=65536)  # 64 KB streaming chunks

# Parse a file
result = parser.parse_file("data.json")

# Parse raw bytes with optional filename hint
result = parser.parse_bytes(raw_bytes, hint="data.csv")

# Stream a large file record-by-record
for record in parser.stream_file("huge_data.jsonl"):
    process(record)

# Check for corruption
issues = parser.check_corruption(data, DataFormat.JSON)

# Infer schema from records
schema = parser.infer_schema(records)
```

#### `ParseResult`

| Attribute  | Type                | Description                              |
|------------|---------------------|------------------------------------------|
| `format`   | `DataFormat`        | Detected or specified format             |
| `records`  | `List[dict]`        | Parsed records                           |
| `schema`   | `List[SchemaField]` | Inferred schema fields                   |
| `source`   | `str`               | Source file or identifier                |
| `errors`   | `List[str]`         | Parse errors / repair messages           |
| `metadata` | `dict`              | Format-specific metadata                 |

#### Supported Formats

| Format      | `DataFormat` enum  | Detection method             |
|-------------|-------------------|------------------------------|
| JSON        | `JSON`            | Extension or content heuristic |
| JSONL/NDJSON | `JSONL`          | Extension or content heuristic |
| XML         | `XML`             | Extension or leading `<`     |
| CSV         | `CSV`             | Extension or delimiter sniff |
| TSV         | `TSV`             | Extension or delimiter sniff |
| Parquet     | `PARQUET`         | Magic bytes `PAR1`           |
| Protobuf    | `PROTOBUF`        | Extension `.pb`/`.proto`     |
| Binary      | `BINARY`          | Magic bytes (ZIP, gzip, …)   |
| Plain text  | `TEXT`            | Fallback                     |

---

### StructEngine

**File:** `struct_engine.py`

Intelligent data structuring, type inference, normalization, and quality analysis.

#### `StructEngine`

```python
from struct_engine import StructEngine

engine = StructEngine()

# Analyse records
dataset = engine.structure(records, source_name="my_data")
print(f"Quality: {dataset.quality_score}")
print(f"Fields: {dataset.field_types}")

# Normalize numeric fields
normed = engine.normalize(records, strategies={"price": "minmax", "age": "zscore"})

# Enrich metadata
meta = engine.enrich_metadata(records)

# Cross-blob consistency validation
report = engine.validate_consistency({"train": train_recs, "test": test_recs})
```

#### Field Types

| Type              | Description                          |
|-------------------|--------------------------------------|
| `NUMERICAL_INT`   | Integer values                       |
| `NUMERICAL_FLOAT` | Floating-point values                |
| `CATEGORICAL`     | Low-cardinality string field         |
| `TEXTUAL`         | High-cardinality free text           |
| `TEMPORAL`        | Date/datetime strings                |
| `SPATIAL`         | Lat/lon coordinate strings           |
| `BOOLEAN`         | True/false or yes/no values          |
| `NULL`            | All values are null                  |

#### Normalization Strategies

| Strategy  | Description                        |
|-----------|------------------------------------|
| `minmax`  | Scale to [0, 1] range              |
| `zscore`  | Mean=0, Std=1 standardisation      |

---

### DatasetCompiler

**File:** `dataset_compiler.py`

Dataset compilation, splitting, class balancing, and multi-format export.

#### `DatasetCompiler`

```python
from dataset_compiler import DatasetCompiler, SplitConfig, MergeStrategy

compiler = DatasetCompiler()

# Fuse multiple record sources
fused = compiler.fuse([source_a, source_b], strategy="union")

# Compile with custom split
split_cfg = SplitConfig(train=0.8, val=0.1, test=0.1, stratify_field="label", seed=42)
dataset = compiler.compile(
    records,
    name="my_dataset",
    split_config=split_cfg,
    label_field="label",
    balance_strategy="oversample",
)

# Export
paths = compiler.export(dataset, output_dir="./output", fmt="jsonl")
```

#### Merge Strategies

| Strategy       | Description                                          |
|----------------|------------------------------------------------------|
| `concat`       | Simple concatenation, all fields from each source    |
| `union`        | All fields across all sources; missing → `None`      |
| `intersection` | Only fields shared by ALL sources                    |

#### Export Formats

| Format        | Description                                           |
|---------------|-------------------------------------------------------|
| `json`        | JSON array per split                                  |
| `jsonl`       | Newline-delimited JSON per split                      |
| `csv`         | CSV with header per split                             |
| `huggingface` | JSONL in HuggingFace Datasets directory structure     |
| `pytorch`     | JSON `{"data": [...]}` per split                      |
| `tensorflow`  | JSONL per split                                       |

---

### AutoTrainer

**File:** `auto_trainer.py`

Automated training orchestration with model selection, hyperparameter optimization, checkpoints, early stopping, and Victor LLM hooks.

#### `AutoTrainer`

```python
from auto_trainer import AutoTrainer, TrainingConfig

trainer = AutoTrainer(checkpoint_dir="./checkpoints")

# Define a custom training function
def my_train_fn(batch, config):
    # batch: List[dict], config: TrainingConfig
    # return (train_loss, val_loss)
    loss = my_model.train_step(batch)
    return loss, val_loss

# Configure
config = TrainingConfig(
    epochs=10,
    batch_size=32,
    learning_rate=1e-4,
    model_type="auto",       # auto-detected from dataset
    early_stopping_patience=3,
    checkpoint_interval=2,
)

result = trainer.train(
    train_records=train_data,
    val_records=val_data,
    config=config,
    train_fn=my_train_fn,
    dataset_info={"task_type": "classification", "num_classes": 3},
)

print(result.summary())

# Hyperparameter search
best_config, all_results = trainer.hpo_search(
    train_records=train_data,
    val_records=val_data,
    n_trials=10,
    base_config=config,
    search_space={
        "learning_rate": [1e-5, 1e-4, 1e-3],
        "batch_size": [16, 32, 64],
    },
    train_fn=my_train_fn,
)
```

#### `TrainingConfig` Fields

| Field                     | Default  | Description                                |
|---------------------------|----------|--------------------------------------------|
| `model_type`              | `"auto"` | Model type or `"auto"` for detection       |
| `epochs`                  | `10`     | Maximum training epochs                    |
| `batch_size`              | `32`     | Records per batch                          |
| `learning_rate`           | `1e-3`   | Initial learning rate                      |
| `weight_decay`            | `1e-4`   | L2 regularization weight                   |
| `warmup_steps`            | `100`    | Learning rate warmup steps                 |
| `early_stopping_patience` | `5`      | Epochs without improvement before stopping |
| `checkpoint_interval`     | `5`      | Save checkpoint every N epochs             |
| `seed`                    | `42`     | Random seed for reproducibility            |
| `output_dir`              | `"./checkpoints"` | Checkpoint directory             |

#### Victor LLM Hook

The `VictorTrainingHook` automatically integrates with the Victor LLM training backend when `victor_core` is importable:

```python
from auto_trainer import VictorTrainingHook

hook = VictorTrainingHook()
print(f"Victor backend available: {hook.available}")
```

---

### AnalyticsDashboard

**File:** `analytics_dashboard.py`

Visual analytics and monitoring for datasets and training runs.

#### `AnalyticsDashboard`

```python
from analytics_dashboard import AnalyticsDashboard

dash = AnalyticsDashboard()

# Load dataset analytics
dash.update_dataset(
    field_stats=structured.field_stats,
    null_pcts=structured.metadata["null_percentages"],
    quality_score=structured.quality_score,
    record_count=len(records),
    anomaly_count=len(structured.anomalies),
    manifest=compiled.manifest,
)

# Load training history
dash.update_training([m.to_dict() for m in training_result.metrics_history])

# Terminal output
dash.print_summary()

# Save HTML report
path = dash.save_html("report.html")

# Start web server (non-blocking, runs in background thread)
server = dash.serve(host="127.0.0.1", port=8787)
# Open http://127.0.0.1:8787 in your browser

# Stop server
dash.stop_server()
```

---

### DataBlob Godmode Kit

**File:** `data_blob_godmode_kit.py`

Main orchestrator that integrates all components.

#### `DataBlobGodmodeKit`

```python
from data_blob_godmode_kit import DataBlobGodmodeKit, GodmodeConfig

config = GodmodeConfig(
    output_dir="./godmode_output",
    default_export_format="jsonl",
    dashboard_port=8787,
    seed=42,
)
kit = DataBlobGodmodeKit(config=config)
```

**Key properties:**

| Property              | Description                          |
|-----------------------|--------------------------------------|
| `kit.parser`          | `SmartParser` instance               |
| `kit.struct_engine`   | `StructEngine` instance              |
| `kit.compiler`        | `DatasetCompiler` instance           |
| `kit.trainer`         | `AutoTrainer` instance               |
| `kit.dashboard`       | `AnalyticsDashboard` instance        |
| `kit.records`         | All ingested records (read-only)     |
| `kit.structured_dataset` | Last `StructuredDataset`          |
| `kit.compiled_dataset`   | Last `CompiledDataset`            |
| `kit.last_training_result` | Last `TrainingResult`           |

**Ingestion methods:**

```python
kit.ingest_file("data.json")              # auto-detect format
kit.ingest_file("data.parquet", fmt=DataFormat.PARQUET)
kit.ingest_bytes(raw_bytes, hint="data.csv")
kit.ingest_records(my_list_of_dicts)
for record in kit.stream_file("huge.jsonl"):  # streaming
    process(record)
kit.clear_records()                        # reset pool
```

---

## CLI Interface

**File:** `cli_godmode.py`

```
usage: godmode [-h] [--verbose] {parse,structure,compile,train,pipeline,dashboard} ...
```

### `parse`

```bash
python cli_godmode.py parse data.json
python cli_godmode.py parse data.csv --show-records --limit 10
python cli_godmode.py parse data.xml --format json
```

### `structure`

```bash
python cli_godmode.py structure data.json
python cli_godmode.py structure data.csv --format json
```

### `compile`

```bash
python cli_godmode.py compile data.json extra.csv \
    --name my_dataset \
    --export-fmt jsonl \
    --label-field category \
    --balance oversample \
    --train-ratio 0.8 \
    --val-ratio 0.1 \
    --output-dir ./output
```

### `train`

```bash
python cli_godmode.py train data.json \
    --epochs 10 \
    --batch-size 64 \
    --lr 0.001 \
    --label-field label \
    --output-dir ./output \
    --report
```

### `pipeline`

```bash
python cli_godmode.py pipeline data.json \
    --name experiment_1 \
    --epochs 20 \
    --label-field category \
    --balance oversample \
    --export-fmt jsonl \
    --output-dir ./output
```

### `dashboard`

```bash
python cli_godmode.py dashboard data.json --port 8787
# Open http://127.0.0.1:8787 in your browser
```

---

## Integration with Victor LLM

The toolkit integrates with the Victor LLM training infrastructure through the `VictorTrainingHook`:

```python
from auto_trainer import AutoTrainer, VictorTrainingHook

hook = VictorTrainingHook(victor_core_path=None)  # auto-detects victor_core

trainer = AutoTrainer(
    checkpoint_dir="./checkpoints",
    victor_hook=hook,
)
```

When `victor_core` is available on the Python path, the hook calls into `victor_core.brain.AsiCoreBrain` at each epoch boundary and upon training completion.

**Custom metrics callback:**

```python
from auto_trainer import MetricsTracker, TrainingMetrics

def my_callback(metrics: TrainingMetrics) -> None:
    print(f"Epoch {metrics.epoch}: loss={metrics.train_loss:.4f}")

# Inject via MetricsTracker
tracker = MetricsTracker(output_dir="./logs", run_id="my-run")
tracker.add_callback(my_callback)
```

---

## Testing

Run the complete test suite:

```bash
python -m unittest test_godmode_toolkit -v
```

Expected output: **140 tests, 0 failures**.

The test suite covers:

- `TestFormatDetector` – format detection from bytes and extensions
- `TestJSONParser` – JSON parsing, repair, schema inference
- `TestJSONLParser` – JSONL multi-line parsing and streaming
- `TestXMLParser` – XML parsing and repair
- `TestCSVParser` – CSV/TSV auto-delimiter detection
- `TestTextParser` – plain text line parsing
- `TestSmartParser` – end-to-end file/bytes/stream parsing
- `TestTypeInferrer` – all type inference paths
- `TestNormalizer` – min-max, z-score, text, boolean normalization
- `TestAnomalyDetector` – outlier detection, duplicate detection, null analysis
- `TestQualityScorer` – quality score computation
- `TestStructEngine` – full structure/normalize/validate cycle
- `TestSplitter` – random and stratified splits
- `TestClassBalanceAnalyser` – balance analysis, over/undersampling
- `TestDatasetExporter` – all export formats
- `TestDatasetCompiler` – compile, fuse, export
- `TestTrainingConfig` – run ID generation
- `TestModelSelector` – all task type paths
- `TestHyperparamOptimizer` – random config, grid search
- `TestCheckpointManager` – save, load, best selection
- `TestAutoTrainer` – full training loop, custom function, early stopping, HPO
- `TestASCIIChart` – bar chart and histogram rendering
- `TestQualityHeatmap` – ASCII and HTML heatmaps
- `TestHTMLDashboard` – full HTML generation
- `TestAnalyticsDashboard` – update, render, save
- `TestDataBlobGodmodeKit` – full integration (ingest, structure, compile, export, train, pipeline)
- `TestCLI` – all CLI subcommands
- `TestEdgeCases` – empty data, Unicode, large CSV, single record

---

## Examples

### Example 1: Analyse a JSON dataset

```python
from data_blob_godmode_kit import DataBlobGodmodeKit

kit = DataBlobGodmodeKit("./output")
kit.ingest_file("products.json")
structured = kit.structure()
print(f"Quality: {structured.quality_score:.1f}/100")
print(f"Anomalies: {len(structured.anomalies)}")
kit.dashboard.print_summary()
```

### Example 2: Fuse heterogeneous sources

```python
from data_blob_godmode_kit import DataBlobGodmodeKit
from dataset_compiler import MergeStrategy

kit = DataBlobGodmodeKit("./output")
kit.ingest_file("users.csv")
kit.ingest_file("events.json")
kit.ingest_file("profiles.xml")

# All sources share 'user_id' -> fuse with union
compiled = kit.compile_dataset(
    name="user_events",
    merge_strategy=MergeStrategy.UNION,
    label_field="event_type",
    balance_strategy="undersample",
)

paths = kit.export_dataset(compiled, fmt="huggingface")
```

### Example 3: Custom training with HPO

```python
from data_blob_godmode_kit import DataBlobGodmodeKit
from auto_trainer import TrainingConfig
import torch  # your framework

kit = DataBlobGodmodeKit("./output")
kit.ingest_file("training_data.jsonl")
kit.structure()
compiled = kit.compile_dataset(label_field="label")

def train_step(batch, config):
    # Your actual training logic
    optimizer.zero_grad()
    loss = model(batch)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip)
    optimizer.step()
    return float(loss), float(val_loss)

best_cfg, results = kit.hpo_search(
    n_trials=10,
    base_config=TrainingConfig(epochs=5),
    search_space={"learning_rate": [1e-5, 5e-5, 1e-4, 5e-4]},
    train_fn=train_step,
)

final_result = kit.train(config=best_cfg, train_fn=train_step)
kit.save_report("final_report.html")
```

### Example 4: Live dashboard during training

```python
from data_blob_godmode_kit import DataBlobGodmodeKit
from auto_trainer import TrainingConfig

kit = DataBlobGodmodeKit("./output")
kit.ingest_file("data.json")
kit.structure()
compiled = kit.compile_dataset()

# Start dashboard server before training
kit.serve_dashboard(port=8787)

def train_fn(batch, config):
    loss = 0.5
    # After each step you can call kit.dashboard.update_training(...)
    return loss, loss

result = kit.train(compiled, TrainingConfig(epochs=10), train_fn)
print("Training complete. Dashboard still running at http://127.0.0.1:8787")
input("Press Enter to stop.")
```

---

## File Reference

| File                     | Purpose                                     |
|--------------------------|---------------------------------------------|
| `data_blob_godmode_kit.py` | Main toolkit orchestrator                 |
| `smart_parser.py`        | Multi-format parsing engine                 |
| `struct_engine.py`       | Intelligent data structuring               |
| `dataset_compiler.py`    | Dataset compilation and export              |
| `auto_trainer.py`        | Automated training pipeline                 |
| `analytics_dashboard.py` | Visual analytics and monitoring             |
| `cli_godmode.py`         | CLI interface                               |
| `test_godmode_toolkit.py`| Comprehensive test suite (140 tests)        |
| `GODMODE_TOOLKIT_GUIDE.md` | This documentation                        |
