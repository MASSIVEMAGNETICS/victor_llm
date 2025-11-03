"""
Victor LLM Models Module

This module provides utilities for loading and managing Victor LLM models,
including blank slate configurations and pretrained GGUF models.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Get the models directory path
MODELS_DIR = Path(__file__).parent

def load_blank_slate(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the blank slate model configuration.
    
    Args:
        config_path: Optional path to blank slate config. If None, uses default.
        
    Returns:
        Dictionary containing the blank slate configuration.
        
    Example:
        >>> config = load_blank_slate()
        >>> print(config['model_name'])
        'Victor Blank Slate'
    """
    if config_path is None:
        config_path = MODELS_DIR / "blank_slate.json"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Blank slate config not found at: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config


def get_gguf_model_path(model_name: str = "victor_pretrained.gguf") -> Path:
    """
    Get the path to a GGUF model file.
    
    Args:
        model_name: Name of the GGUF model file.
        
    Returns:
        Path object pointing to the model file.
        
    Raises:
        FileNotFoundError: If the model file doesn't exist.
        
    Example:
        >>> model_path = get_gguf_model_path()
        >>> print(model_path)
        /path/to/victor_llm/models/victor_pretrained.gguf
    """
    model_path = MODELS_DIR / model_name
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"GGUF model not found at: {model_path}\n"
            f"Please download a pretrained model. See models/PRETRAINED_GGUF_DOWNLOAD.txt for instructions."
        )
    
    return model_path


def load_gguf_model(model_path: Optional[str] = None, **kwargs):
    """
    Load a GGUF model using llama-cpp-python.
    
    Args:
        model_path: Path to the GGUF model file. If None, uses default.
        **kwargs: Additional arguments to pass to Llama constructor.
        
    Returns:
        Loaded Llama model instance.
        
    Raises:
        ImportError: If llama-cpp-python is not installed.
        FileNotFoundError: If the model file doesn't exist.
        
    Example:
        >>> model = load_gguf_model()
        >>> output = model("Hello, Victor!", max_tokens=50)
        >>> print(output['choices'][0]['text'])
    """
    try:
        from llama_cpp import Llama
    except ImportError:
        raise ImportError(
            "llama-cpp-python is required to load GGUF models.\n"
            "Install it with: pip install llama-cpp-python\n"
            "For GPU support, see models/PRETRAINED_GGUF_DOWNLOAD.txt"
        )
    
    if model_path is None:
        model_path = get_gguf_model_path()
    else:
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Default kwargs for Victor models
    default_kwargs = {
        'n_ctx': 2048,  # Context window
        'n_threads': None,  # Auto-detect
        'n_gpu_layers': 0,  # CPU-only by default (change if GPU available)
        'verbose': False,
    }
    
    # Merge user kwargs with defaults
    final_kwargs = {**default_kwargs, **kwargs}
    
    # Load and return the model
    model = Llama(model_path=str(model_path), **final_kwargs)
    
    return model


def list_available_models() -> Dict[str, bool]:
    """
    List all models in the models directory and their availability.
    
    Returns:
        Dictionary mapping model names to their existence status.
        
    Example:
        >>> models = list_available_models()
        >>> print(models)
        {'blank_slate.json': True, 'victor_pretrained.gguf': False}
    """
    models = {
        'blank_slate.json': (MODELS_DIR / 'blank_slate.json').exists(),
        'victor_pretrained.gguf': (MODELS_DIR / 'victor_pretrained.gguf').exists(),
    }
    
    # Also list any other .gguf files found
    for gguf_file in MODELS_DIR.glob('*.gguf'):
        models[gguf_file.name] = True
    
    return models


__all__ = [
    'load_blank_slate',
    'get_gguf_model_path',
    'load_gguf_model',
    'list_available_models',
    'MODELS_DIR',
]
