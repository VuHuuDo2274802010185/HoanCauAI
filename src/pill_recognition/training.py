"""
Training module for multimodal pill recognition with distributed training support
"""
import os
import time
import logging
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from torch.nn.parallel import DistributedDataParallel as DDP
import torch.distributed as dist
from torch.utils.tensorboard import SummaryWriter
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from .models import MultimodalPillTransformer
from .data import PillDataLoader

logger = logging.getLogger(__name__)


class PillTrainer:
    """
    Trainer class for multimodal pill recognition with distributed training support
    """
    
    def __init__(self, config, model=None, data_loader=None):
        """
        Initialize trainer
        
        Args:
            config: Configuration object
            model: Optional pre-initialized model
            data_loader: Optional pre-initialized data loader
        """
        self.config = config
        self.device = config.device
        self.rank = config.training.rank
        self.world_size = config.training.world_size
        self.use_ddp = config.training.use_ddp
        
        # Initialize distributed training
        if self.use_ddp:
            self._init_distributed()
        
        # Initialize model
        self.model = model if model is not None else MultimodalPillTransformer(config.model)
        self.model.to(self.device)
        
        # Wrap model with DDP if using distributed training
        if self.use_ddp:
            self.model = DDP(self.model, device_ids=[self.rank])
        
        # Initialize data loader
        self.data_loader = data_loader if data_loader is not None else PillDataLoader(config)
        
        # Initialize optimizer and scheduler
        self._init_optimizer()
        self._init_scheduler()
        
        # Initialize loss function
        self.criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
        
        # Initialize mixed precision training
        self.scaler = GradScaler() if config.training.use_amp else None
        
        # Training state
        self.current_epoch = 0
        self.best_val_acc = 0.0
        self.train_losses = []
        self.val_losses = []
        self.val_accuracies = []
        
        # Logging
        if self.rank == 0:  # Only log on main process
            self.writer = SummaryWriter(log_dir=f"logs/pill_recognition_{int(time.time())}")
        else:
            self.writer = None
    
    def _init_distributed(self):
        """Initialize distributed training"""
        if not dist.is_initialized():
            dist.init_process_group(
                backend=self.config.training.dist_backend,
                init_method=self.config.training.dist_url,
                world_size=self.world_size,
                rank=self.rank
            )
        
        # Set device for current process
        torch.cuda.set_device(self.rank)
        self.device = torch.device(f"cuda:{self.rank}")
        
        logger.info(f"Initialized distributed training: rank {self.rank}/{self.world_size}")
    
    def _init_optimizer(self):
        """Initialize optimizer"""
        # Get model parameters
        model = self.model.module if self.use_ddp else self.model
        
        # Separate parameters for different learning rates
        vision_params = []
        text_params = []
        fusion_params = []
        classifier_params = []
        
        for name, param in model.named_parameters():
            if 'vision_transformer' in name:
                vision_params.append(param)
            elif 'text_transformer' in name:
                text_params.append(param)
            elif 'fusion' in name or 'projection' in name:
                fusion_params.append(param)
            else:
                classifier_params.append(param)
        
        # Create parameter groups with different learning rates
        param_groups = [
            {'params': vision_params, 'lr': self.config.training.learning_rate * 0.1},  # Lower LR for pre-trained
            {'params': text_params, 'lr': self.config.training.learning_rate * 0.1},   # Lower LR for pre-trained
            {'params': fusion_params, 'lr': self.config.training.learning_rate},
            {'params': classifier_params, 'lr': self.config.training.learning_rate}
        ]
        
        if self.config.training.optimizer.lower() == 'adamw':
            self.optimizer = optim.AdamW(
                param_groups,
                lr=self.config.training.learning_rate,
                weight_decay=self.config.training.weight_decay,
                betas=(0.9, 0.999),
                eps=1e-8
            )
        elif self.config.training.optimizer.lower() == 'adam':
            self.optimizer = optim.Adam(
                param_groups,
                lr=self.config.training.learning_rate,
                weight_decay=self.config.training.weight_decay
            )
        else:
            self.optimizer = optim.SGD(
                param_groups,
                lr=self.config.training.learning_rate,
                momentum=0.9,
                weight_decay=self.config.training.weight_decay
            )
    
    def _init_scheduler(self):
        """Initialize learning rate scheduler"""
        if self.config.training.scheduler.lower() == 'cosine':
            self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=self.config.training.num_epochs,
                eta_min=self.config.training.learning_rate * 0.01
            )
        elif self.config.training.scheduler.lower() == 'step':
            self.scheduler = optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=self.config.training.num_epochs // 3,
                gamma=0.1
            )
        elif self.config.training.scheduler.lower() == 'warmup_cosine':
            # Custom warmup + cosine scheduler
            self.scheduler = self._get_warmup_cosine_scheduler()
        else:
            self.scheduler = None
    
    def _get_warmup_cosine_scheduler(self):
        """Create warmup + cosine annealing scheduler"""
        def lr_lambda(step):
            if step < self.config.training.warmup_steps:
                return step / self.config.training.warmup_steps
            else:
                progress = (step - self.config.training.warmup_steps) / (
                    self.config.training.num_epochs * len(self.train_loader) - self.config.training.warmup_steps
                )
                return 0.5 * (1 + np.cos(np.pi * progress))
        
        return optim.lr_scheduler.LambdaLR(self.optimizer, lr_lambda)
    
    def train_epoch(self, train_loader, epoch: int) -> Dict[str, float]:
        """
        Train for one epoch
        
        Args:
            train_loader: Training data loader
            epoch: Current epoch number
            
        Returns:
            Dictionary with training metrics
        """
        self.model.train()
        total_loss = 0.0
        total_samples = 0
        step = 0
        
        # Set sampler epoch for distributed training
        if self.use_ddp and hasattr(train_loader.sampler, 'set_epoch'):
            train_loader.sampler.set_epoch(epoch)
        
        for batch_idx, batch in enumerate(train_loader):
            # Move batch to device
            images = batch['image'].to(self.device, non_blocking=True)
            input_ids = batch['input_ids'].to(self.device, non_blocking=True)
            attention_mask = batch['attention_mask'].to(self.device, non_blocking=True)
            labels = batch['label'].to(self.device, non_blocking=True)
            
            batch_size = images.size(0)
            
            # Zero gradients
            self.optimizer.zero_grad()
            
            # Forward pass with mixed precision
            if self.scaler is not None:
                with autocast():
                    outputs = self.model(images, input_ids, attention_mask)
                    loss = self.criterion(outputs['logits'], labels)
                
                # Backward pass with gradient scaling
                self.scaler.scale(loss).backward()
                
                # Gradient clipping
                if self.config.training.clip_grad_norm > 0:
                    self.scaler.unscale_(self.optimizer)
                    nn.utils.clip_grad_norm_(
                        self.model.parameters(), 
                        self.config.training.clip_grad_norm
                    )
                
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(images, input_ids, attention_mask)
                loss = self.criterion(outputs['logits'], labels)
                
                # Backward pass
                loss.backward()
                
                # Gradient clipping
                if self.config.training.clip_grad_norm > 0:
                    nn.utils.clip_grad_norm_(
                        self.model.parameters(), 
                        self.config.training.clip_grad_norm
                    )
                
                self.optimizer.step()
            
            # Update scheduler if step-based
            if self.scheduler is not None and self.config.training.scheduler.lower() == 'warmup_cosine':
                self.scheduler.step()
            
            # Accumulate metrics
            total_loss += loss.item() * batch_size
            total_samples += batch_size
            step += 1
            
            # Log progress
            if self.rank == 0 and batch_idx % 100 == 0:
                logger.info(
                    f"Epoch {epoch} [{batch_idx}/{len(train_loader)}] "
                    f"Loss: {loss.item():.4f} "
                    f"LR: {self.optimizer.param_groups[0]['lr']:.2e}"
                )
                
                if self.writer:
                    global_step = epoch * len(train_loader) + batch_idx
                    self.writer.add_scalar('Train/Loss_Step', loss.item(), global_step)
                    self.writer.add_scalar('Train/LR', self.optimizer.param_groups[0]['lr'], global_step)
        
        # Calculate average loss
        avg_loss = total_loss / total_samples
        
        # Aggregate loss across all processes for distributed training
        if self.use_ddp:
            avg_loss_tensor = torch.tensor(avg_loss, device=self.device)
            dist.all_reduce(avg_loss_tensor, op=dist.ReduceOp.SUM)
            avg_loss = avg_loss_tensor.item() / self.world_size
        
        return {'loss': avg_loss}
    
    def validate(self, val_loader, epoch: int) -> Dict[str, float]:
        """
        Validate model
        
        Args:
            val_loader: Validation data loader
            epoch: Current epoch number
            
        Returns:
            Dictionary with validation metrics
        """
        self.model.eval()
        total_loss = 0.0
        total_samples = 0
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for batch in val_loader:
                # Move batch to device
                images = batch['image'].to(self.device, non_blocking=True)
                input_ids = batch['input_ids'].to(self.device, non_blocking=True)
                attention_mask = batch['attention_mask'].to(self.device, non_blocking=True)
                labels = batch['label'].to(self.device, non_blocking=True)
                
                batch_size = images.size(0)
                
                # Forward pass
                if self.scaler is not None:
                    with autocast():
                        outputs = self.model(images, input_ids, attention_mask)
                        loss = self.criterion(outputs['logits'], labels)
                else:
                    outputs = self.model(images, input_ids, attention_mask)
                    loss = self.criterion(outputs['logits'], labels)
                
                # Get predictions
                predictions = torch.argmax(outputs['logits'], dim=1)
                
                # Accumulate metrics
                total_loss += loss.item() * batch_size
                total_samples += batch_size
                
                # Collect predictions and labels
                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        # Calculate metrics
        avg_loss = total_loss / total_samples
        accuracy = accuracy_score(all_labels, all_predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            all_labels, all_predictions, average='weighted', zero_division=0
        )
        
        # Aggregate metrics across all processes for distributed training
        if self.use_ddp:
            metrics_tensor = torch.tensor([avg_loss, accuracy, precision, recall, f1], device=self.device)
            dist.all_reduce(metrics_tensor, op=dist.ReduceOp.SUM)
            avg_loss, accuracy, precision, recall, f1 = (metrics_tensor / self.world_size).cpu().numpy()
        
        metrics = {
            'loss': avg_loss,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
        return metrics
    
    def train(self, data_root: str, output_dir: str = "checkpoints"):
        """
        Main training loop
        
        Args:
            data_root: Root directory containing training data
            output_dir: Directory to save checkpoints
        """
        if self.rank == 0:
            logger.info("Starting training...")
            os.makedirs(output_dir, exist_ok=True)
        
        # Create data loaders
        train_loader, val_loader, _ = self.data_loader.create_dataloaders(data_root)
        self.train_loader = train_loader  # Store for scheduler
        
        # Training loop
        for epoch in range(self.current_epoch, self.config.training.num_epochs):
            self.current_epoch = epoch
            
            # Train epoch
            train_metrics = self.train_epoch(train_loader, epoch)
            self.train_losses.append(train_metrics['loss'])
            
            # Update scheduler if epoch-based
            if self.scheduler is not None and self.config.training.scheduler.lower() != 'warmup_cosine':
                self.scheduler.step()
            
            # Validate
            if epoch % self.config.training.eval_every == 0:
                val_metrics = self.validate(val_loader, epoch)
                self.val_losses.append(val_metrics['loss'])
                self.val_accuracies.append(val_metrics['accuracy'])
                
                # Check if best model
                is_best = val_metrics['accuracy'] > self.best_val_acc
                if is_best:
                    self.best_val_acc = val_metrics['accuracy']
                
                # Log metrics
                if self.rank == 0:
                    logger.info(
                        f"Epoch {epoch}: "
                        f"Train Loss: {train_metrics['loss']:.4f}, "
                        f"Val Loss: {val_metrics['loss']:.4f}, "
                        f"Val Acc: {val_metrics['accuracy']:.4f}, "
                        f"Best Acc: {self.best_val_acc:.4f}"
                    )
                    
                    if self.writer:
                        self.writer.add_scalar('Train/Loss_Epoch', train_metrics['loss'], epoch)
                        self.writer.add_scalar('Val/Loss', val_metrics['loss'], epoch)
                        self.writer.add_scalar('Val/Accuracy', val_metrics['accuracy'], epoch)
                        self.writer.add_scalar('Val/Precision', val_metrics['precision'], epoch)
                        self.writer.add_scalar('Val/Recall', val_metrics['recall'], epoch)
                        self.writer.add_scalar('Val/F1', val_metrics['f1'], epoch)
                
                # Save checkpoint
                if self.rank == 0 and (epoch % self.config.training.save_every == 0 or is_best):
                    self.save_checkpoint(
                        output_dir, 
                        epoch, 
                        val_metrics, 
                        is_best=is_best
                    )
        
        # Training complete
        if self.rank == 0:
            logger.info("Training completed!")
            if self.writer:
                self.writer.close()
        
        # Clean up distributed training
        if self.use_ddp:
            dist.destroy_process_group()
    
    def save_checkpoint(self, output_dir: str, epoch: int, metrics: Dict[str, float], is_best: bool = False):
        """Save model checkpoint"""
        model = self.model.module if self.use_ddp else self.model
        
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict() if self.scheduler else None,
            'best_val_acc': self.best_val_acc,
            'metrics': metrics,
            'config': self.config.to_dict(),
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'val_accuracies': self.val_accuracies
        }
        
        # Save regular checkpoint
        checkpoint_path = os.path.join(output_dir, f"checkpoint_epoch_{epoch}.pth")
        torch.save(checkpoint, checkpoint_path)
        
        # Save best model
        if is_best:
            best_path = os.path.join(output_dir, "best_model.pth")
            torch.save(checkpoint, best_path)
            logger.info(f"Saved best model with accuracy: {self.best_val_acc:.4f}")
    
    def load_checkpoint(self, checkpoint_path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        model = self.model.module if self.use_ddp else self.model
        model.load_state_dict(checkpoint['model_state_dict'])
        
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        if self.scheduler and checkpoint['scheduler_state_dict']:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        self.current_epoch = checkpoint['epoch'] + 1
        self.best_val_acc = checkpoint['best_val_acc']
        self.train_losses = checkpoint.get('train_losses', [])
        self.val_losses = checkpoint.get('val_losses', [])
        self.val_accuracies = checkpoint.get('val_accuracies', [])
        
        logger.info(f"Loaded checkpoint from epoch {checkpoint['epoch']}")


def setup_distributed_training(rank: int, world_size: int):
    """
    Setup function for distributed training
    
    Args:
        rank: Process rank
        world_size: Total number of processes
    """
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12355'
    
    # Initialize distributed training
    dist.init_process_group(
        backend='nccl',
        init_method='env://',
        world_size=world_size,
        rank=rank
    )
    
    # Set device for current process
    torch.cuda.set_device(rank)


def cleanup_distributed():
    """Clean up distributed training"""
    dist.destroy_process_group()