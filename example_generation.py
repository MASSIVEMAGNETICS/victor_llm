"""
Example: Using the Trained Victor Transformer Model

This script demonstrates how to load and use a trained Victor Transformer model
for text generation.
"""

import torch
from models.transformer_model import VictorTransformerModel, load_model_from_config
from pathlib import Path


def load_trained_model(config_path: str = 'models/blank_slate.json', 
                       checkpoint_path: str = 'checkpoints/best_checkpoint.pt',
                       device: str = 'auto'):
    """
    Load a trained Victor Transformer model
    
    Args:
        config_path: Path to model configuration JSON
        checkpoint_path: Path to trained checkpoint
        device: Device to load model on ('cpu', 'cuda', or 'auto')
    
    Returns:
        Loaded model ready for inference
    """
    # Determine device
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"Loading model on device: {device}")
    
    # Load model architecture
    model = load_model_from_config(config_path, device=device)
    
    # Load trained weights if checkpoint exists
    checkpoint_path = Path(checkpoint_path)
    if checkpoint_path.exists():
        print(f"Loading checkpoint from: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        
        # Print training info
        if 'epoch' in checkpoint:
            print(f"Model trained for {checkpoint['epoch']} epochs")
        if 'best_val_loss' in checkpoint and checkpoint['best_val_loss'] != float('inf'):
            print(f"Best validation loss: {checkpoint['best_val_loss']:.4f}")
    else:
        print(f"Warning: Checkpoint not found at {checkpoint_path}")
        print("Using untrained model!")
    
    # Set to evaluation mode
    model.eval()
    
    return model


def simple_tokenize(text: str, max_length: int = 128):
    """
    Simple character-level tokenization
    In production, use a proper tokenizer like BPE or SentencePiece
    """
    token_ids = [min(ord(c), 255) for c in text[:max_length]]
    return torch.tensor([token_ids], dtype=torch.long)


def simple_detokenize(token_ids):
    """Decode token IDs back to text"""
    return ''.join([chr(min(int(t), 255)) for t in token_ids[0]])


def generate_text(model, prompt: str, max_new_tokens: int = 50, 
                  temperature: float = 0.7, top_p: float = 0.9, top_k: int = 50):
    """
    Generate text from a prompt
    
    Args:
        model: Trained model
        prompt: Starting text
        max_new_tokens: Number of tokens to generate
        temperature: Sampling temperature (higher = more random)
        top_p: Nucleus sampling threshold
        top_k: Top-k sampling threshold
    
    Returns:
        Generated text
    """
    # Tokenize prompt
    input_ids = simple_tokenize(prompt)
    device = next(model.parameters()).device
    input_ids = input_ids.to(device)
    
    print(f"\nPrompt: '{prompt}'")
    print(f"Generating {max_new_tokens} tokens...")
    
    # Generate
    with torch.no_grad():
        generated_ids = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k
        )
    
    # Decode
    generated_text = simple_detokenize(generated_ids)
    
    return generated_text


def main():
    """Main demonstration"""
    print("=" * 60)
    print("VICTOR TRANSFORMER MODEL - GENERATION DEMO")
    print("=" * 60)
    
    # Load model
    model = load_trained_model()
    
    # Example prompts
    prompts = [
        "The Victor AGI system",
        "Machine learning is",
        "The future of AI"
    ]
    
    print("\n" + "-" * 60)
    print("TEXT GENERATION EXAMPLES")
    print("-" * 60)
    
    for prompt in prompts:
        try:
            generated = generate_text(
                model, 
                prompt, 
                max_new_tokens=30,
                temperature=0.8,
                top_p=0.9
            )
            print(f"\nGenerated: '{generated}'")
            print("-" * 60)
        except Exception as e:
            print(f"Error generating for prompt '{prompt}': {e}")
    
    # Show model statistics
    print("\nMODEL STATISTICS")
    print("-" * 60)
    print(f"Architecture: {model.num_layers}-layer Transformer")
    print(f"Hidden size: {model.hidden_size}")
    print(f"Attention heads: {model.num_heads}")
    print(f"Vocabulary size: {model.vocab_size}")
    print(f"Max sequence length: {model.max_position_embeddings}")
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
