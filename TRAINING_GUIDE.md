# Training a State-of-the-Art Victor Transformer Model

This guide explains how to train the Victor Transformer Model using the provided training infrastructure.

## Overview

The Victor Transformer is a GPT-style causal language model with 125M parameters based on the blank_slate.json configuration. It features:

- **12-layer transformer architecture** with 768 hidden dimensions
- **12 attention heads** for multi-head self-attention
- **Position embeddings** for sequence understanding  
- **Causal masking** for autoregressive generation
- **Modern optimization** with AdamW, warmup, and cosine annealing

## Quick Start

### 1. Install Dependencies

```bash
pip install torch tqdm numpy
```

### 2. Train the Model

```bash
# Train on sample data (creates automatically)
python train_sota_model.py --create-sample-data --epochs 3

# Train on your own dataset
python train_sota_model.py --data your_text_file.txt --epochs 10
```

### 3. Command-Line Options

```bash
python train_sota_model.py \
    --config models/blank_slate.json \
    --data your_data.txt \
    --epochs 3 \
    --batch-size 8 \
    --max-length 128 \
    --checkpoint-dir checkpoints \
    --device auto  # or 'cpu' or 'cuda'
```

## Training Process

The training script implements a complete pipeline:

1. **Data Loading**: Loads text data and creates sequences with stride for efficiency
2. **Model Initialization**: Creates transformer model from configuration
3. **Optimization**: Uses AdamW optimizer with:
   - Learning rate warmup (first 100 steps)
   - Cosine annealing decay
   - Gradient clipping (max norm = 1.0)
   - Gradient accumulation support
4. **Checkpointing**: Saves latest and best models based on loss

### Training Output

```
==================================================
VICTOR TRANSFORMER - SOTA MODEL TRAINING
==================================================
Creating sample dataset: sample_data.txt
Sample dataset created with 1000 lines

Loading model from models/blank_slate.json...
Model loaded successfully! Parameters: 125,226,240

Loading training data from sample_data.txt...
Created 280 sequences from 71633 tokens

Starting training for 1 epochs...
Total parameters: 125,226,240
Device: cpu
Training batches: 140
--------------------------------------------------
Epoch 1: 100%|████████| 140/140 [02:00<00:00,  1.16it/s, loss=7.44, lr=6.57e-06]

Epoch 1/1
  Train Loss: 8.5902
  Time: 120.48s
  LR: 6.57e-06

==================================================
Training completed!
==================================================

Checkpoints saved to: checkpoints
```

## Using the Trained Model

### Load and Inference

```python
import torch
from models.transformer_model import VictorTransformerModel, load_model_from_config

# Load model architecture
model = load_model_from_config('models/blank_slate.json')

# Load trained weights
checkpoint = torch.load('checkpoints/best_checkpoint.pt')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Generate text
input_ids = torch.tensor([[1, 2, 3, 4, 5]])  # Your token IDs
generated = model.generate(
    input_ids,
    max_new_tokens=50,
    temperature=0.7,
    top_p=0.9,
    top_k=50
)
print(generated)
```

### Model Architecture Details

The model uses modern transformer architecture with:

```python
VictorTransformerModel(
    vocab_size=50257,           # Token vocabulary
    hidden_size=768,             # Model dimension
    num_layers=12,               # Transformer blocks
    num_heads=12,                # Attention heads
    intermediate_size=3072,      # FFN dimension
    max_position_embeddings=2048 # Max sequence length
)
```

## Advanced Configuration

### Custom Model Configuration

Edit `models/blank_slate.json` to customize architecture:

```json
{
  "architecture": {
    "num_layers": 12,          // More layers = more capacity
    "hidden_size": 768,         // Larger = more parameters
    "num_attention_heads": 12,  // Must divide hidden_size
    "max_position_embeddings": 2048
  },
  "training_config": {
    "learning_rate": 5e-05,
    "batch_size": 8,
    "num_train_epochs": 3,
    "gradient_accumulation_steps": 4
  }
}
```

### Data Preparation

For best results:
- Use large text corpora (>1M tokens)
- Clean and normalize text
- Consider domain-specific data for specialized models

Example data format (plain text):
```
The Victor AGI system is powerful.
Training deep neural networks requires care.
Language models learn from text patterns.
```

## Performance Tips

### Training Faster

1. **Use GPU**: `--device cuda` (requires CUDA-capable GPU)
2. **Increase batch size**: `--batch-size 16` (if memory allows)
3. **Reduce sequence length**: `--max-length 64` (for faster iterations)

### Better Results

1. **More epochs**: `--epochs 10` or more
2. **Larger dataset**: Use real-world text corpora
3. **Learning rate tuning**: Adjust in `blank_slate.json`
4. **Longer sequences**: `--max-length 512` for better context

## Model Files

After training, you'll have:

```
checkpoints/
├── latest_checkpoint.pt      # Most recent model
├── best_checkpoint.pt        # Best validation loss
└── final_checkpoint.pt       # End of training
```

Each checkpoint contains:
- `model_state_dict`: Trained model weights
- `optimizer_state_dict`: Optimizer state for resuming
- `scheduler_state_dict`: Learning rate scheduler state
- `epoch`: Training epoch number
- `config`: Model configuration

## Troubleshooting

### Out of Memory

- Reduce `--batch-size` (try 4 or 2)
- Reduce `--max-length` (try 64 or 32)
- Use gradient accumulation (edit `gradient_accumulation_steps` in config)

### Slow Training

- Use GPU if available: `--device cuda`
- Reduce model size (edit `num_layers` or `hidden_size` in config)
- Use fewer training epochs initially

### Loss Not Decreasing

- Check learning rate (default 5e-5 is usually good)
- Ensure data is properly formatted
- Try training longer (more epochs)
- Check data quality and diversity

## Integration with Victor Core

The trained model can be integrated into the Victor AGI framework:

```python
from models.transformer_model import VictorTransformerModel
from victor_core.main import VictorBrain

# Load trained model
model = VictorTransformerModel.load_checkpoint('checkpoints/best_checkpoint.pt')

# Integrate with Victor
brain = VictorBrain()
brain.set_language_model(model)
```

## Citation

If you use this training pipeline in your research:

```bibtex
@software{victor_transformer_2025,
  title={Victor Transformer - State-of-the-Art Language Model},
  author={Victor AGI Team},
  year={2025},
  organization={Massive Magnetics / Ethica AI}
}
```

## Additional Resources

- Model configuration: `models/blank_slate.json`
- Model architecture: `models/transformer_model.py`
- Training script: `train_sota_model.py`
- Victor core framework: `victor_core/`

## License

Proprietary - Massive Magnetics / Ethica AI / BHeard Network
