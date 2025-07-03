#!/usr/bin/env python3
"""
Training script for multimodal pill recognition with distributed training support
"""
import os
import sys
import argparse
import logging
import torch
import torch.multiprocessing as mp
from pathlib import Path

# Add src directory to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pill_recognition.config import PillRecognitionConfig
from pill_recognition.training import PillTrainer, setup_distributed_training, cleanup_distributed
from pill_recognition.data import PillDataLoader

logger = logging.getLogger(__name__)


def setup_logging(rank: int = 0):
    """Setup logging configuration"""
    level = logging.INFO if rank == 0 else logging.WARNING
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'logs/training_rank_{rank}.log')
        ]
    )


def train_worker(rank: int, world_size: int, args):
    """
    Training worker function for distributed training
    
    Args:
        rank: Process rank
        world_size: Total number of processes
        args: Command line arguments
    """
    try:
        # Setup distributed training
        if world_size > 1:
            setup_distributed_training(rank, world_size)
        
        # Setup logging
        setup_logging(rank)
        
        # Load configuration
        config = PillRecognitionConfig(args.config)
        config.training.rank = rank
        config.training.world_size = world_size
        config.training.use_ddp = world_size > 1
        
        # Override config with command line arguments
        if args.batch_size:
            config.training.batch_size = args.batch_size
        if args.learning_rate:
            config.training.learning_rate = args.learning_rate
        if args.num_epochs:
            config.training.num_epochs = args.num_epochs
        if args.num_classes:
            config.model.num_classes = args.num_classes
        
        # Log configuration
        if rank == 0:
            logger.info(f"Training configuration: {config.to_dict()}")
            logger.info(f"Using device: {config.device}")
            logger.info(f"Number of GPUs: {config.num_gpus}")
            logger.info(f"Distributed training: {config.training.use_ddp}")
        
        # Create trainer
        trainer = PillTrainer(config)
        
        # Load checkpoint if specified
        if args.resume:
            if os.path.exists(args.resume):
                trainer.load_checkpoint(args.resume)
                if rank == 0:
                    logger.info(f"Resumed training from {args.resume}")
            else:
                if rank == 0:
                    logger.warning(f"Checkpoint not found: {args.resume}")
        
        # Start training
        trainer.train(args.data_root, args.output_dir)
        
        # Clean up
        if world_size > 1:
            cleanup_distributed()
            
    except Exception as e:
        logger.error(f"Training failed on rank {rank}: {e}")
        raise


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description="Train multimodal pill recognition model")
    
    # Data arguments
    parser.add_argument('--data-root', type=str, required=True,
                       help='Root directory containing training data')
    parser.add_argument('--output-dir', type=str, default='checkpoints',
                       help='Directory to save checkpoints')
    
    # Model arguments
    parser.add_argument('--config', type=str, default=None,
                       help='Path to configuration file')
    parser.add_argument('--num-classes', type=int, default=None,
                       help='Number of pill classes')
    
    # Training arguments
    parser.add_argument('--batch-size', type=int, default=None,
                       help='Batch size for training')
    parser.add_argument('--learning-rate', type=float, default=None,
                       help='Learning rate')
    parser.add_argument('--num-epochs', type=int, default=None,
                       help='Number of training epochs')
    parser.add_argument('--resume', type=str, default=None,
                       help='Path to checkpoint to resume from')
    
    # Distributed training arguments
    parser.add_argument('--world-size', type=int, default=None,
                       help='Number of processes for distributed training')
    parser.add_argument('--single-gpu', action='store_true',
                       help='Force single GPU training')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Determine world size
    if args.single_gpu:
        world_size = 1
    elif args.world_size:
        world_size = args.world_size
    else:
        world_size = torch.cuda.device_count() if torch.cuda.is_available() else 1
    
    print(f"Starting training with {world_size} processes...")
    
    if world_size > 1:
        # Multi-GPU distributed training
        mp.spawn(
            train_worker,
            args=(world_size, args),
            nprocs=world_size,
            join=True
        )
    else:
        # Single GPU or CPU training
        train_worker(0, 1, args)
    
    print("Training completed!")


if __name__ == '__main__':
    main()