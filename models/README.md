# Victor LLM Models Directory

This directory contains model files for the Victor LLM system.

## Model Files

### Blank Slate Model

The **blank slate model** (`blank_slate.json`) is a minimal, untrained model configuration that serves as a starting point for training or fine-tuning. It contains:
- Model architecture configuration
- Initial random weights/parameters
- Tokenizer configuration
- Default hyperparameters

**Usage:**
```python
from models import load_blank_slate

# Load the blank slate model
model = load_blank_slate('models/blank_slate.json')
```

### Pretrained GGUF Model

**GGUF** (GPT-Generated Unified Format) is a file format for storing quantized language models, commonly used with llama.cpp and similar inference engines.

The pretrained GGUF file should be placed in this directory with the name `victor_pretrained.gguf`.

**Obtaining Pretrained Models:**

Due to the large size of GGUF model files (typically several GB), they are not stored in the repository. You can:

1. **Download from Hugging Face:**
   ```bash
   # Example: Download a compatible GGUF model
   wget https://huggingface.co/TheBloke/[model-name]/resolve/main/[model-file].gguf -O models/victor_pretrained.gguf
   ```

2. **Convert your own model to GGUF:**
   ```bash
   # Using llama.cpp conversion tools
   python convert.py /path/to/your/model --outfile models/victor_pretrained.gguf
   ```

3. **Train and export your own:**
   Use the BandoDatasetTrainer to train a model, then export to GGUF format.

**Usage:**
```python
from models import load_gguf_model

# Load the pretrained GGUF model
model = load_gguf_model('models/victor_pretrained.gguf')
```

## Model Storage Guidelines

- **Large files:** GGUF files are typically excluded from git (see `.gitignore`)
- **Recommended location:** Keep models in this directory for consistency
- **Naming convention:** Use descriptive names like `victor_pretrained_7b_q4.gguf` to indicate model size and quantization

## Supported Model Formats

- `.json` - Model configuration files
- `.gguf` - Quantized model weights (GGUF format)
- `.pt` / `.pth` - PyTorch model checkpoints
- `.safetensors` - SafeTensors format

## Model Requirements

For optimal performance with Victor:
- Minimum 4GB RAM for small models (up to 3B parameters)
- 8GB+ RAM recommended for 7B models
- 16GB+ RAM for 13B+ models

## See Also

- `docs/perf_tuning.md` - Performance optimization guide
- `bando_dataset_trainer_gui_v1.0.0-BANDO-GODCORE.py` - Model training interface
- `BandoSuperFractalLanguageModel.py` - Advanced model architecture
