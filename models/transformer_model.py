"""
Victor Transformer Model - SOTA Architecture Implementation
Based on the blank_slate.json configuration
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import json
from pathlib import Path
from typing import Optional, Dict, Any


class MultiHeadAttention(nn.Module):
    """Multi-head self-attention mechanism"""
    
    def __init__(self, hidden_size: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        assert hidden_size % num_heads == 0, "hidden_size must be divisible by num_heads"
        
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.scaling = self.head_dim ** -0.5
        
        self.q_proj = nn.Linear(hidden_size, hidden_size)
        self.k_proj = nn.Linear(hidden_size, hidden_size)
        self.v_proj = nn.Linear(hidden_size, hidden_size)
        self.out_proj = nn.Linear(hidden_size, hidden_size)
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
        batch_size, seq_length, _ = hidden_states.size()
        
        # Project and reshape to (batch, num_heads, seq_len, head_dim)
        q = self.q_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Compute attention scores
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) * self.scaling
        
        if attention_mask is not None:
            attn_weights = attn_weights + attention_mask
        
        attn_weights = F.softmax(attn_weights, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        attn_output = torch.matmul(attn_weights, v)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_length, self.hidden_size)
        
        return self.out_proj(attn_output)


class FeedForward(nn.Module):
    """Position-wise feed-forward network"""
    
    def __init__(self, hidden_size: int, intermediate_size: int, dropout: float = 0.1, activation: str = "gelu"):
        super().__init__()
        self.fc1 = nn.Linear(hidden_size, intermediate_size)
        self.fc2 = nn.Linear(intermediate_size, hidden_size)
        self.dropout = nn.Dropout(dropout)
        
        if activation == "gelu":
            self.activation = F.gelu
        elif activation == "relu":
            self.activation = F.relu
        else:
            self.activation = F.gelu
    
    def forward(self, x: torch.Tensor):
        x = self.fc1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class TransformerBlock(nn.Module):
    """Single transformer block with self-attention and feed-forward"""
    
    def __init__(self, hidden_size: int, num_heads: int, intermediate_size: int, 
                 dropout: float = 0.1, attention_dropout: float = 0.1, 
                 layer_norm_epsilon: float = 1e-5, activation: str = "gelu"):
        super().__init__()
        
        self.attention = MultiHeadAttention(hidden_size, num_heads, attention_dropout)
        self.feed_forward = FeedForward(hidden_size, intermediate_size, dropout, activation)
        
        self.ln1 = nn.LayerNorm(hidden_size, eps=layer_norm_epsilon)
        self.ln2 = nn.LayerNorm(hidden_size, eps=layer_norm_epsilon)
        
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
    
    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
        # Self-attention with residual connection
        residual = hidden_states
        hidden_states = self.ln1(hidden_states)
        hidden_states = self.attention(hidden_states, attention_mask)
        hidden_states = self.dropout1(hidden_states)
        hidden_states = residual + hidden_states
        
        # Feed-forward with residual connection
        residual = hidden_states
        hidden_states = self.ln2(hidden_states)
        hidden_states = self.feed_forward(hidden_states)
        hidden_states = self.dropout2(hidden_states)
        hidden_states = residual + hidden_states
        
        return hidden_states


class VictorTransformerModel(nn.Module):
    """
    Victor Transformer Model - State-of-the-Art Language Model
    
    A GPT-style causal language model with modern transformer architecture.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        arch = config.get('architecture', {})
        self.vocab_size = arch.get('vocab_size', 50257)
        self.hidden_size = arch.get('hidden_size', 768)
        self.num_layers = arch.get('num_layers', 12)
        self.num_heads = arch.get('num_attention_heads', 12)
        self.intermediate_size = arch.get('intermediate_size', 3072)
        self.max_position_embeddings = arch.get('max_position_embeddings', 2048)
        self.dropout = arch.get('dropout_rate', 0.1)
        self.attention_dropout = arch.get('attention_dropout', 0.1)
        self.layer_norm_epsilon = arch.get('layer_norm_epsilon', 1e-5)
        self.activation = arch.get('activation_function', 'gelu')
        
        # Embeddings
        self.token_embedding = nn.Embedding(self.vocab_size, self.hidden_size)
        self.position_embedding = nn.Embedding(self.max_position_embeddings, self.hidden_size)
        self.dropout_layer = nn.Dropout(self.dropout)
        
        # Transformer blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(
                self.hidden_size,
                self.num_heads,
                self.intermediate_size,
                self.dropout,
                self.attention_dropout,
                self.layer_norm_epsilon,
                self.activation
            ) for _ in range(self.num_layers)
        ])
        
        # Final layer norm
        self.ln_f = nn.LayerNorm(self.hidden_size, eps=self.layer_norm_epsilon)
        
        # Language model head
        self.lm_head = nn.Linear(self.hidden_size, self.vocab_size, bias=False)
        
        # Weight tying (share weights between token embedding and output layer)
        # This reduces parameters and improves performance by ensuring
        # input and output embeddings are consistent
        self.lm_head.weight = self.token_embedding.weight
        
        # Initialize weights
        self.apply(self._init_weights)
        
    def _init_weights(self, module):
        """Initialize weights using normal distribution"""
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.ones_(module.weight)
            torch.nn.init.zeros_(module.bias)
    
    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None, 
                labels: Optional[torch.Tensor] = None):
        """
        Forward pass through the model
        
        Args:
            input_ids: Token indices (batch_size, seq_length)
            attention_mask: Attention mask (batch_size, seq_length)
            labels: Target token indices for loss computation (batch_size, seq_length)
            
        Returns:
            Dictionary with logits and optional loss
        """
        batch_size, seq_length = input_ids.size()
        device = input_ids.device
        
        # Create position indices
        position_ids = torch.arange(0, seq_length, dtype=torch.long, device=device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
        
        # Get embeddings
        token_embeds = self.token_embedding(input_ids)
        position_embeds = self.position_embedding(position_ids)
        hidden_states = token_embeds + position_embeds
        hidden_states = self.dropout_layer(hidden_states)
        
        # Create causal mask (prevent attending to future tokens)
        causal_mask = torch.triu(torch.full((seq_length, seq_length), float('-inf'), device=device), diagonal=1)
        causal_mask = causal_mask.unsqueeze(0).unsqueeze(0)  # (1, 1, seq_len, seq_len)
        
        # Apply attention mask if provided
        if attention_mask is not None:
            # Convert attention mask to the right format (0 for masked, 1 for not masked)
            extended_mask = attention_mask.unsqueeze(1).unsqueeze(2)  # (batch, 1, 1, seq_len)
            extended_mask = (1.0 - extended_mask) * -10000.0
            causal_mask = causal_mask + extended_mask
        
        # Pass through transformer blocks
        for block in self.blocks:
            hidden_states = block(hidden_states, causal_mask)
        
        # Final layer norm
        hidden_states = self.ln_f(hidden_states)
        
        # Project to vocabulary
        logits = self.lm_head(hidden_states)
        
        loss = None
        if labels is not None:
            # Shift so that tokens < n predict n
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            # Flatten the tokens
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(shift_logits.view(-1, self.vocab_size), shift_labels.view(-1))
        
        return {
            'logits': logits,
            'loss': loss
        }
    
    def generate(self, input_ids: torch.Tensor, max_new_tokens: int = 50, 
                 temperature: float = 0.7, top_p: float = 0.9, top_k: int = 50):
        """
        Generate text using the model
        
        Args:
            input_ids: Starting token indices (batch_size, seq_length)
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling threshold
            
        Returns:
            Generated token indices
        """
        self.eval()
        generated = input_ids
        
        with torch.no_grad():
            for _ in range(max_new_tokens):
                # Get predictions for the last token
                outputs = self.forward(generated)
                logits = outputs['logits'][:, -1, :]  # (batch_size, vocab_size)
                
                # Apply temperature
                logits = logits / temperature
                
                # Top-k filtering
                if top_k > 0:
                    indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
                    logits[indices_to_remove] = float('-inf')
                
                # Top-p (nucleus) filtering
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    # Remove tokens with cumulative probability above the threshold
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    
                    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                    logits[indices_to_remove] = float('-inf')
                
                # Sample from the distribution
                probs = F.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
                
                # Append to generated sequence
                generated = torch.cat([generated, next_token], dim=1)
                
                # Stop if we exceed max position embeddings
                if generated.size(1) >= self.max_position_embeddings:
                    break
        
        return generated


def load_model_from_config(config_path: str, device: str = 'cpu'):
    """
    Load a Victor Transformer model from a configuration file
    
    Args:
        config_path: Path to the JSON configuration file
        device: Device to load the model on ('cpu' or 'cuda')
        
    Returns:
        Initialized VictorTransformerModel
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    model = VictorTransformerModel(config)
    model.to(device)
    
    return model


def count_parameters(model: nn.Module):
    """Count the number of trainable parameters in the model"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Test the model
    print("Testing Victor Transformer Model...")
    
    # Load blank slate config
    config_path = Path(__file__).parent / "blank_slate.json"
    if config_path.exists():
        model = load_model_from_config(str(config_path))
        print(f"Model loaded successfully!")
        print(f"Total parameters: {count_parameters(model):,}")
        
        # Test forward pass
        batch_size = 2
        seq_length = 128
        input_ids = torch.randint(0, model.vocab_size, (batch_size, seq_length))
        
        outputs = model(input_ids)
        print(f"Output logits shape: {outputs['logits'].shape}")
        print(f"Expected shape: ({batch_size}, {seq_length}, {model.vocab_size})")
        
        # Test with labels
        labels = torch.randint(0, model.vocab_size, (batch_size, seq_length))
        outputs = model(input_ids, labels=labels)
        print(f"Loss: {outputs['loss'].item():.4f}")
        
        print("\nModel architecture test passed! ✓")
    else:
        print(f"Config file not found at {config_path}")
