"""
Configuration module for pill recognition system
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import torch


@dataclass
class ModelConfig:
    """Configuration for multimodal transformer model"""
    # Vision transformer config
    vision_model_name: str = "vit-base-patch16-224"
    vision_embed_dim: int = 768
    vision_num_heads: int = 12
    vision_num_layers: int = 12
    
    # Text transformer config  
    text_model_name: str = "bert-base-uncased"
    text_embed_dim: int = 768
    text_max_length: int = 128
    
    # Cross-modal fusion config
    fusion_embed_dim: int = 512
    fusion_num_heads: int = 8
    fusion_num_layers: int = 4
    
    # Classification config
    num_classes: int = 1000  # Number of pill types
    dropout_rate: float = 0.1
    
    # Image preprocessing
    image_size: int = 224
    image_mean: List[float] = None
    image_std: List[float] = None
    
    def __post_init__(self):
        if self.image_mean is None:
            self.image_mean = [0.485, 0.456, 0.406]
        if self.image_std is None:
            self.image_std = [0.229, 0.224, 0.225]


@dataclass 
class TrainingConfig:
    """Configuration for training process"""
    # Basic training params
    batch_size: int = 32
    learning_rate: float = 1e-4
    num_epochs: int = 100
    warmup_steps: int = 1000
    weight_decay: float = 0.01
    
    # Distributed training
    use_ddp: bool = True
    world_size: int = 1
    rank: int = 0
    dist_backend: str = "nccl"
    dist_url: str = "env://"
    
    # Data loading
    num_workers: int = 4
    pin_memory: bool = True
    
    # Optimization
    optimizer: str = "adamw"
    scheduler: str = "cosine"
    clip_grad_norm: float = 1.0
    
    # Checkpointing
    save_every: int = 5
    eval_every: int = 1
    save_best_only: bool = True
    
    # Mixed precision training
    use_amp: bool = True
    
    # Augmentation
    use_augmentation: bool = True
    augmentation_strength: float = 0.5


@dataclass
class DataConfig:
    """Configuration for data handling"""
    # Paths
    data_root: str = "data/pills"
    train_split: str = "train"
    val_split: str = "val" 
    test_split: str = "test"
    
    # Data splits
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    
    # OCR config
    use_tesseract: bool = True
    use_paddle_ocr: bool = True
    ocr_languages: List[str] = None
    
    # Image processing
    min_image_size: int = 64
    max_image_size: int = 512
    
    def __post_init__(self):
        if self.ocr_languages is None:
            self.ocr_languages = ["en", "ch_sim"]


@dataclass
class OCRConfig:
    """Configuration for OCR extraction"""
    # Tesseract config
    tesseract_cmd: Optional[str] = None  # Auto-detect if None
    tesseract_config: str = "--oem 3 --psm 6"
    
    # PaddleOCR config
    paddle_use_angle_cls: bool = True
    paddle_lang: str = "en"
    paddle_use_gpu: bool = True
    paddle_show_log: bool = False
    
    # Text processing
    min_text_length: int = 1
    max_text_length: int = 128
    clean_text: bool = True
    
    # Confidence thresholds
    min_confidence: float = 0.5
    paddle_confidence_threshold: float = 0.5


class PillRecognitionConfig:
    """Main configuration class for pill recognition system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.model = ModelConfig()
        self.training = TrainingConfig()
        self.data = DataConfig() 
        self.ocr = OCRConfig()
        
        # Set device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_gpus = torch.cuda.device_count() if torch.cuda.is_available() else 0
        
        # Update distributed training config based on available GPUs
        if self.num_gpus > 1:
            self.training.use_ddp = True
            self.training.world_size = self.num_gpus
        else:
            self.training.use_ddp = False
            self.training.world_size = 1
            
        # Load from file if provided
        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)
    
    def load_from_file(self, config_path: str):
        """Load configuration from JSON/YAML file"""
        import json
        
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
            
        # Update configurations
        if 'model' in config_dict:
            for key, value in config_dict['model'].items():
                if hasattr(self.model, key):
                    setattr(self.model, key, value)
                    
        if 'training' in config_dict:
            for key, value in config_dict['training'].items():
                if hasattr(self.training, key):
                    setattr(self.training, key, value)
                    
        if 'data' in config_dict:
            for key, value in config_dict['data'].items():
                if hasattr(self.data, key):
                    setattr(self.data, key, value)
                    
        if 'ocr' in config_dict:
            for key, value in config_dict['ocr'].items():
                if hasattr(self.ocr, key):
                    setattr(self.ocr, key, value)
    
    def save_to_file(self, config_path: str):
        """Save configuration to JSON file"""
        import json
        from dataclasses import asdict
        
        config_dict = {
            'model': asdict(self.model),
            'training': asdict(self.training),
            'data': asdict(self.data),
            'ocr': asdict(self.ocr)
        }
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        from dataclasses import asdict
        return {
            'model': asdict(self.model),
            'training': asdict(self.training), 
            'data': asdict(self.data),
            'ocr': asdict(self.ocr),
            'device': str(self.device),
            'num_gpus': self.num_gpus
        }


# Default configuration instance
config = PillRecognitionConfig()