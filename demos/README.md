# Victor LLM Demos

This directory contains runnable examples for Victor LLM.

| Demo | File | Description |
|------|------|-------------|
| Minimal inference | `demo_inference.py` | Load a tokenizer and generate text from a prompt. |
| Fine-tuning | `demo_finetune.py` | Train on `datasets/example_dataset` for 2 epochs. |
| End-to-end | `demo_e2e.py` | Runs prepare → train → eval → predict in one script. |

## Running demos

Install dependencies first (from repo root):

```bash
pip install -r requirements.txt
pip install pyyaml           # optional – for dataset.yaml support
```

### 1 – Minimal inference

```bash
python demos/demo_inference.py
```

### 2 – Fine-tuning demo

```bash
python demos/demo_finetune.py
```

### 3 – End-to-end demo (prepare → train → eval → predict)

```bash
python demos/demo_e2e.py
```

Or use the `victor` CLI directly (after installing with `pip install -e .`):

```bash
victor prepare  --dataset datasets/example_dataset
victor train    --dataset datasets/example_dataset --epochs 2 --output-dir /tmp/victor_demo
victor eval     --dataset datasets/example_dataset --checkpoint /tmp/victor_demo --split test
victor predict  --prompt "Hello, Victor!"
victor benchmark --prompts 5
```
