# Victor LLM Benchmarks

This directory contains benchmarking infrastructure for Victor LLM.

## Structure

```
benchmarks/
  harness.py         ← standalone benchmarking harness (latency, throughput, memory)
  results/           ← JSON results from past benchmark runs (auto-created)
  README.md          ← this file
```

## Quick Start

```bash
# Run inference benchmark (no checkpoint needed)
python benchmarks/harness.py

# Run with a trained checkpoint
python benchmarks/harness.py --checkpoint runs/<run_id>

# Use the victor CLI
victor benchmark --prompts 20 --max-tokens 128
```

## Metrics Captured

| Metric | Description |
|--------|-------------|
| `latency_mean_s` | Mean per-prompt inference time (seconds) |
| `latency_median_s` | Median per-prompt inference time |
| `latency_min_s` / `latency_max_s` | Min / max latency |
| `latency_stdev_s` | Standard deviation of latency |
| `throughput_tokens_per_s` | Total tokens generated ÷ total time |
| `memory_before_mb` | RSS before benchmark (MB) |
| `memory_after_mb` | RSS after benchmark (MB) |
| `memory_delta_mb` | Memory growth during benchmark |

## Comparing Runs

Results are stored as timestamped JSON files in `benchmarks/results/`.
Use the compare helper:

```bash
python benchmarks/harness.py --compare benchmarks/results/
```

## Adding a Training Benchmark

```bash
python benchmarks/harness.py --mode training --dataset datasets/example_dataset --epochs 1
```
