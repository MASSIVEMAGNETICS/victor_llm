# Victor LLM – Datasets

This directory stores training datasets in the standard Victor layout.

## Directory Layout

```
datasets/
  <dataset_name>/
    train.jsonl      ← required
    valid.jsonl      ← optional (validation split)
    test.jsonl       ← optional (evaluation split)
    dataset.yaml     ← optional metadata / schema hints
```

## Record Format

Each line in a `.jsonl` file is a self-contained JSON object.
The minimum required field depends on your task:

| Task               | Required field(s)              |
|--------------------|--------------------------------|
| Language modelling | `text` (string)               |
| Classification     | `text` + `label`              |
| Instruction tuning | `instruction` + `response`    |
| Custom             | any fields – specify in YAML   |

### Language-model example
```json
{"text": "The quick brown fox jumps over the lazy dog."}
{"text": "Victor LLM is a modular AGI framework."}
```

### Classification example
```json
{"text": "This is great!", "label": "positive"}
{"text": "This is terrible.", "label": "negative"}
```

### Instruction-tuning example
```json
{"instruction": "Summarise the following.", "response": "A concise summary."}
```

## dataset.yaml (optional)

```yaml
name: my_dataset
task: classification        # language_model | classification | instruction
label_field: label          # field used as target (classification tasks)
text_field: text            # field used as input text
version: "1.0"
description: "Short description of the dataset."
```

## Adding a New Dataset

1. Create a sub-directory: `datasets/<your_dataset_name>/`
2. Add at least `train.jsonl` with valid JSON-Lines records.
3. Optionally add `valid.jsonl`, `test.jsonl`, and `dataset.yaml`.
4. Run:
   ```bash
   victor prepare --dataset datasets/<your_dataset_name>
   victor train   --dataset datasets/<your_dataset_name>
   ```

## Example Dataset

`datasets/example_dataset/` is a tiny built-in demo set (10 records each split)
useful for smoke tests and quick sanity checks.
