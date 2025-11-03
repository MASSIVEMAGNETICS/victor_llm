#!/usr/bin/env python3
"""
Example usage of Victor LLM models - blank slate and pretrained GGUF.

This script demonstrates how to load and use the blank slate configuration
and pretrained GGUF models in the Victor LLM system.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from models
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    load_blank_slate,
    load_gguf_model,
    list_available_models,
    MODELS_DIR
)


def example_blank_slate():
    """Example: Load and inspect the blank slate configuration."""
    print("=" * 70)
    print("EXAMPLE 1: Loading Blank Slate Configuration")
    print("=" * 70)
    
    try:
        config = load_blank_slate()
        print(f"\n✓ Successfully loaded blank slate configuration")
        print(f"  Model name: {config['model_name']}")
        print(f"  Version: {config['version']}")
        print(f"  Architecture type: {config['architecture']['type']}")
        print(f"  Number of layers: {config['architecture']['num_layers']}")
        print(f"  Hidden size: {config['architecture']['hidden_size']}")
        print(f"  Vocabulary size: {config['architecture']['vocab_size']}")
        print(f"  Max sequence length: {config['architecture']['max_position_embeddings']}")
        
        print(f"\n  Training config:")
        print(f"    - Learning rate: {config['training_config']['learning_rate']}")
        print(f"    - Batch size: {config['training_config']['batch_size']}")
        print(f"    - Epochs: {config['training_config']['num_train_epochs']}")
        
        print(f"\n  This configuration can be used to:")
        print(f"    - Initialize a new model from scratch")
        print(f"    - Start training with the BandoDatasetTrainer")
        print(f"    - Configure Victor's neural architecture")
        
    except Exception as e:
        print(f"\n✗ Error loading blank slate: {e}")
    
    print()


def example_gguf_model():
    """Example: Load and use a pretrained GGUF model."""
    print("=" * 70)
    print("EXAMPLE 2: Loading Pretrained GGUF Model")
    print("=" * 70)
    
    try:
        # This will raise an error if the model doesn't exist
        print("\nAttempting to load GGUF model...")
        model = load_gguf_model()
        
        print(f"✓ Successfully loaded GGUF model")
        print(f"  Model path: {MODELS_DIR / 'victor_pretrained.gguf'}")
        
        # Try a simple generation
        prompt = "Hello, Victor! What can you do?"
        print(f"\n  Testing with prompt: '{prompt}'")
        
        response = model(prompt, max_tokens=100, temperature=0.7)
        generated_text = response['choices'][0]['text']
        
        print(f"\n  Generated response:")
        print(f"  {generated_text}")
        
    except FileNotFoundError as e:
        print(f"\n✗ GGUF model not found")
        print(f"  {e}")
        print(f"\n  To use GGUF models:")
        print(f"    1. Download a pretrained model (see models/PRETRAINED_GGUF_DOWNLOAD.txt)")
        print(f"    2. Place it in: {MODELS_DIR}/victor_pretrained.gguf")
        print(f"    3. Install llama-cpp-python: pip install llama-cpp-python")
        
    except ImportError as e:
        print(f"\n✗ Required library not installed")
        print(f"  {e}")
        
    except Exception as e:
        print(f"\n✗ Error loading GGUF model: {e}")
    
    print()


def example_list_models():
    """Example: List all available models."""
    print("=" * 70)
    print("EXAMPLE 3: Listing Available Models")
    print("=" * 70)
    
    models = list_available_models()
    
    print(f"\nModels directory: {MODELS_DIR}")
    print(f"\nAvailable models:")
    
    for model_name, exists in models.items():
        status = "✓ Available" if exists else "✗ Not found"
        print(f"  {model_name:<30} {status}")
    
    print(f"\nTotal models found: {sum(models.values())}/{len(models)}")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("VICTOR LLM MODELS - EXAMPLE USAGE")
    print("=" * 70)
    print()
    
    # Example 1: Blank slate configuration
    example_blank_slate()
    
    # Example 2: GGUF model loading
    example_gguf_model()
    
    # Example 3: List available models
    example_list_models()
    
    print("=" * 70)
    print("For more information, see:")
    print(f"  - {MODELS_DIR}/README.md")
    print(f"  - {MODELS_DIR}/PRETRAINED_GGUF_DOWNLOAD.txt")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
