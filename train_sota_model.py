"""
Train State-of-the-Art Victor Transformer Model

This script implements a complete training pipeline for the Victor Transformer model,
including data loading, training loop, checkpointing, and evaluation.
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import argparse
from tqdm import tqdm
import numpy as np

from models.transformer_model import VictorTransformerModel, load_model_from_config, count_parameters


class TextDataset(Dataset):
    """Simple text dataset for language modeling"""
    
    def __init__(self, text_file: str, tokenizer, max_length: int = 512, stride: int = 256):
        """
        Args:
            text_file: Path to text file
            tokenizer: Tokenizer to use for encoding
            max_length: Maximum sequence length
            stride: Stride for creating overlapping sequences
        """
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.stride = stride
        
        # Read and encode text
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Simple character-level tokenization (for demonstration)
        # In production, you'd use a proper tokenizer like BPE
        self.tokens = self._simple_tokenize(text)
        
        # Create sequences
        self.sequences = []
        for i in range(0, len(self.tokens) - max_length, stride):
            self.sequences.append(self.tokens[i:i + max_length])
        
        print(f"Created {len(self.sequences)} sequences from {len(self.tokens)} tokens")
    
    def _simple_tokenize(self, text: str) -> List[int]:
        """Simple character-level tokenization"""
        # Map characters to integers (0-255 for ASCII + special tokens)
        return [min(ord(c), 255) for c in text]
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        seq = torch.tensor(self.sequences[idx], dtype=torch.long)
        return {
            'input_ids': seq,
            'labels': seq  # For language modeling, labels are the same as inputs
        }


class SimpleTokenizer:
    """Simple character-level tokenizer"""
    
    def __init__(self, vocab_size: int = 256):
        self.vocab_size = vocab_size
    
    def encode(self, text: str) -> List[int]:
        return [min(ord(c), self.vocab_size - 1) for c in text]
    
    def decode(self, tokens: List[int]) -> str:
        return ''.join([chr(min(t, 255)) for t in tokens])


class Trainer:
    """Training orchestrator for Victor Transformer model"""
    
    def __init__(
        self,
        model: nn.Module,
        train_dataloader: DataLoader,
        val_dataloader: Optional[DataLoader] = None,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
        device: str = 'cpu',
        config: Optional[Dict[str, Any]] = None
    ):
        self.model = model
        self.train_dataloader = train_dataloader
        self.val_dataloader = val_dataloader
        self.device = device
        self.config = config or {}
        
        # Setup optimizer
        if optimizer is None:
            training_config = self.config.get('training_config', {})
            lr = training_config.get('learning_rate', 5e-5)
            weight_decay = training_config.get('weight_decay', 0.01)
            self.optimizer = AdamW(
                model.parameters(),
                lr=lr,
                weight_decay=weight_decay,
                betas=(training_config.get('beta1', 0.9), training_config.get('beta2', 0.999)),
                eps=training_config.get('epsilon', 1e-8)
            )
        else:
            self.optimizer = optimizer
        
        # Setup scheduler
        self.scheduler = scheduler
        
        # Training state
        self.global_step = 0
        self.epoch = 0
        self.best_val_loss = float('inf')
        
        # Gradient accumulation
        training_config = self.config.get('training_config', {})
        self.gradient_accumulation_steps = training_config.get('gradient_accumulation_steps', 1)
        self.max_grad_norm = training_config.get('max_grad_norm', 1.0)
        
    def train_epoch(self):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        num_batches = 0
        
        progress_bar = tqdm(self.train_dataloader, desc=f"Epoch {self.epoch + 1}")
        
        for batch_idx, batch in enumerate(progress_bar):
            input_ids = batch['input_ids'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            outputs = self.model(input_ids, labels=labels)
            loss = outputs['loss']
            
            # Normalize loss for gradient accumulation
            loss = loss / self.gradient_accumulation_steps
            
            # Backward pass
            loss.backward()
            
            # Gradient accumulation
            if (batch_idx + 1) % self.gradient_accumulation_steps == 0:
                # Clip gradients
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
                
                # Optimizer step
                self.optimizer.step()
                if self.scheduler is not None:
                    self.scheduler.step()
                self.optimizer.zero_grad()
                
                self.global_step += 1
            
            # Track loss
            total_loss += loss.item() * self.gradient_accumulation_steps
            num_batches += 1
            
            # Update progress bar
            current_lr = self.optimizer.param_groups[0]['lr']
            progress_bar.set_postfix({
                'loss': loss.item() * self.gradient_accumulation_steps,
                'lr': f'{current_lr:.2e}'
            })
        
        avg_loss = total_loss / num_batches
        return avg_loss
    
    def validate(self):
        """Run validation"""
        if self.val_dataloader is None:
            return None
        
        self.model.eval()
        total_loss = 0
        num_batches = 0
        
        with torch.no_grad():
            for batch in tqdm(self.val_dataloader, desc="Validation"):
                input_ids = batch['input_ids'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(input_ids, labels=labels)
                loss = outputs['loss']
                
                total_loss += loss.item()
                num_batches += 1
        
        avg_loss = total_loss / num_batches
        return avg_loss
    
    def train(self, num_epochs: int, checkpoint_dir: Optional[str] = None):
        """Main training loop"""
        print(f"\nStarting training for {num_epochs} epochs...")
        print(f"Total parameters: {count_parameters(self.model):,}")
        print(f"Device: {self.device}")
        print(f"Training batches: {len(self.train_dataloader)}")
        if self.val_dataloader:
            print(f"Validation batches: {len(self.val_dataloader)}")
        print("-" * 50)
        
        for epoch in range(num_epochs):
            self.epoch = epoch
            start_time = time.time()
            
            # Train
            train_loss = self.train_epoch()
            
            # Validate
            val_loss = self.validate()
            
            # Print stats
            epoch_time = time.time() - start_time
            print(f"\nEpoch {epoch + 1}/{num_epochs}")
            print(f"  Train Loss: {train_loss:.4f}")
            if val_loss is not None:
                print(f"  Val Loss: {val_loss:.4f}")
            print(f"  Time: {epoch_time:.2f}s")
            print(f"  LR: {self.optimizer.param_groups[0]['lr']:.2e}")
            
            # Save checkpoint
            if checkpoint_dir is not None:
                checkpoint_path = Path(checkpoint_dir)
                checkpoint_path.mkdir(parents=True, exist_ok=True)
                
                # Save latest
                self.save_checkpoint(checkpoint_path / "latest_checkpoint.pt")
                
                # Save best
                if val_loss is not None and val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    self.save_checkpoint(checkpoint_path / "best_checkpoint.pt")
                    print(f"  ✓ New best model saved!")
                elif val_loss is None and epoch == num_epochs - 1:
                    # Save final model if no validation
                    self.save_checkpoint(checkpoint_path / "final_checkpoint.pt")
        
        print("\n" + "=" * 50)
        print("Training completed!")
        print("=" * 50)
    
    def save_checkpoint(self, path: str):
        """Save model checkpoint"""
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict() if self.scheduler else None,
            'epoch': self.epoch,
            'global_step': self.global_step,
            'best_val_loss': self.best_val_loss,
            'config': self.config
        }
        torch.save(checkpoint, path)
    
    def load_checkpoint(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        if self.scheduler and checkpoint.get('scheduler_state_dict'):
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.epoch = checkpoint.get('epoch', 0)
        self.global_step = checkpoint.get('global_step', 0)
        self.best_val_loss = checkpoint.get('best_val_loss', float('inf'))
        print(f"Checkpoint loaded from {path}")


def create_sample_dataset(output_file: str = "sample_data.txt", num_samples: int = 1000):
    """Create a sample text dataset for demonstration"""
    print(f"Creating sample dataset: {output_file}")
    
    # Generate some sample text
    sample_texts = [
        "The Victor AGI system is a powerful framework for artificial intelligence.",
        "Language models learn patterns from text data to generate coherent responses.",
        "Training deep neural networks requires careful tuning of hyperparameters.",
        "The transformer architecture revolutionized natural language processing.",
        "Self-attention mechanisms allow models to focus on relevant context.",
        "Machine learning models improve with more training data and compute.",
        "The Victor Prime Synthesis Core enables advanced cognitive operations.",
        "Neural networks consist of layers of interconnected artificial neurons.",
        "Backpropagation is used to compute gradients for weight updates.",
        "State-of-the-art models achieve impressive performance on many tasks.",
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for _ in range(num_samples):
            text = np.random.choice(sample_texts)
            f.write(text + "\n")
    
    print(f"Sample dataset created with {num_samples} lines")


def main():
    parser = argparse.ArgumentParser(description="Train Victor Transformer Model")
    parser.add_argument('--config', type=str, default='models/blank_slate.json',
                        help='Path to model configuration file')
    parser.add_argument('--data', type=str, default='sample_data.txt',
                        help='Path to training data file')
    parser.add_argument('--epochs', type=int, default=3,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=8,
                        help='Training batch size')
    parser.add_argument('--max-length', type=int, default=128,
                        help='Maximum sequence length')
    parser.add_argument('--checkpoint-dir', type=str, default='checkpoints',
                        help='Directory to save checkpoints')
    parser.add_argument('--device', type=str, default='auto',
                        help='Device to use (cpu, cuda, or auto)')
    parser.add_argument('--create-sample-data', action='store_true',
                        help='Create sample dataset before training')
    
    args = parser.parse_args()
    
    # Determine device
    if args.device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = args.device
    
    print("=" * 50)
    print("VICTOR TRANSFORMER - SOTA MODEL TRAINING")
    print("=" * 50)
    
    # Create sample data if requested
    if args.create_sample_data or not Path(args.data).exists():
        create_sample_dataset(args.data)
    
    # Load config
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    # Override batch size if specified
    if 'training_config' in config:
        config['training_config']['batch_size'] = args.batch_size
    
    # Load model
    print(f"\nLoading model from {args.config}...")
    model = load_model_from_config(args.config, device=device)
    print(f"Model loaded successfully! Parameters: {count_parameters(model):,}")
    
    # Create tokenizer
    tokenizer = SimpleTokenizer(vocab_size=config['architecture']['vocab_size'])
    
    # Create datasets
    print(f"\nLoading training data from {args.data}...")
    train_dataset = TextDataset(args.data, tokenizer, max_length=args.max_length)
    
    # Create data loaders
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0
    )
    
    # Setup learning rate scheduler
    training_config = config.get('training_config', {})
    warmup_steps = training_config.get('warmup_steps', 100)
    total_steps = len(train_dataloader) * args.epochs
    
    # Create warmup + cosine annealing scheduler
    optimizer = AdamW(
        model.parameters(),
        lr=training_config.get('learning_rate', 5e-5),
        weight_decay=training_config.get('weight_decay', 0.01)
    )
    
    warmup_scheduler = LinearLR(
        optimizer,
        start_factor=0.1,
        end_factor=1.0,
        total_iters=warmup_steps
    )
    
    cosine_scheduler = CosineAnnealingLR(
        optimizer,
        T_max=total_steps - warmup_steps,
        eta_min=training_config.get('learning_rate', 5e-5) * 0.1
    )
    
    scheduler = SequentialLR(
        optimizer,
        schedulers=[warmup_scheduler, cosine_scheduler],
        milestones=[warmup_steps]
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        train_dataloader=train_dataloader,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        config=config
    )
    
    # Train
    trainer.train(num_epochs=args.epochs, checkpoint_dir=args.checkpoint_dir)
    
    print(f"\nCheckpoints saved to: {args.checkpoint_dir}")
    print("\nTo use the trained model:")
    print(f"  from models.transformer_model import VictorTransformerModel")
    print(f"  checkpoint = torch.load('{args.checkpoint_dir}/best_checkpoint.pt')")
    print(f"  model.load_state_dict(checkpoint['model_state_dict'])")


if __name__ == "__main__":
    main()
