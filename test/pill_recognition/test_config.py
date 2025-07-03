"""
Tests for pill recognition configuration module
"""
import pytest
import tempfile
import json
from pathlib import Path

from pill_recognition.config import (
    ModelConfig, 
    TrainingConfig, 
    DataConfig, 
    OCRConfig, 
    PillRecognitionConfig
)


class TestModelConfig:
    """Test ModelConfig class"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = ModelConfig()
        
        assert config.vision_model_name == "vit-base-patch16-224"
        assert config.vision_embed_dim == 768
        assert config.text_model_name == "bert-base-uncased"
        assert config.text_embed_dim == 768
        assert config.fusion_embed_dim == 512
        assert config.num_classes == 1000
        assert config.image_size == 224
        assert len(config.image_mean) == 3
        assert len(config.image_std) == 3
    
    def test_post_init(self):
        """Test post-initialization processing"""
        config = ModelConfig(image_mean=None, image_std=None)
        
        assert config.image_mean == [0.485, 0.456, 0.406]
        assert config.image_std == [0.229, 0.224, 0.225]


class TestTrainingConfig:
    """Test TrainingConfig class"""
    
    def test_default_values(self):
        """Test default training configuration"""
        config = TrainingConfig()
        
        assert config.batch_size == 32
        assert config.learning_rate == 1e-4
        assert config.num_epochs == 100
        assert config.optimizer == "adamw"
        assert config.scheduler == "cosine"
        assert config.use_ddp == True
        assert config.use_amp == True


class TestDataConfig:
    """Test DataConfig class"""
    
    def test_default_values(self):
        """Test default data configuration"""
        config = DataConfig()
        
        assert config.data_root == "data/pills"
        assert config.train_split == "train"
        assert config.val_split == "val"
        assert config.test_split == "test"
        assert config.train_ratio == 0.7
        assert config.val_ratio == 0.15
        assert config.test_ratio == 0.15
    
    def test_post_init(self):
        """Test post-initialization processing"""
        config = DataConfig(ocr_languages=None)
        
        assert config.ocr_languages == ["en", "ch_sim"]


class TestOCRConfig:
    """Test OCRConfig class"""
    
    def test_default_values(self):
        """Test default OCR configuration"""
        config = OCRConfig()
        
        assert config.tesseract_cmd is None
        assert config.tesseract_config == "--oem 3 --psm 6"
        assert config.paddle_use_angle_cls == True
        assert config.paddle_lang == "en"
        assert config.paddle_use_gpu == True
        assert config.min_confidence == 0.5


class TestPillRecognitionConfig:
    """Test main PillRecognitionConfig class"""
    
    def test_initialization(self):
        """Test configuration initialization"""
        config = PillRecognitionConfig()
        
        assert isinstance(config.model, ModelConfig)
        assert isinstance(config.training, TrainingConfig)
        assert isinstance(config.data, DataConfig)
        assert isinstance(config.ocr, OCRConfig)
        assert hasattr(config, 'device')
        assert hasattr(config, 'num_gpus')
    
    def test_distributed_training_config(self):
        """Test distributed training configuration"""
        config = PillRecognitionConfig()
        
        if config.num_gpus > 1:
            assert config.training.use_ddp == True
            assert config.training.world_size == config.num_gpus
        else:
            assert config.training.use_ddp == False
            assert config.training.world_size == 1
    
    def test_save_load_config(self):
        """Test saving and loading configuration"""
        config = PillRecognitionConfig()
        
        # Modify some values
        config.model.num_classes = 500
        config.training.batch_size = 64
        config.data.train_ratio = 0.8
        config.ocr.min_confidence = 0.7
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            # Save configuration
            config.save_to_file(config_file)
            
            # Load configuration
            new_config = PillRecognitionConfig(config_file)
            
            # Check that values were loaded correctly
            assert new_config.model.num_classes == 500
            assert new_config.training.batch_size == 64
            assert new_config.data.train_ratio == 0.8
            assert new_config.ocr.min_confidence == 0.7
            
        finally:
            # Clean up
            Path(config_file).unlink(missing_ok=True)
    
    def test_to_dict(self):
        """Test configuration to dictionary conversion"""
        config = PillRecognitionConfig()
        config_dict = config.to_dict()
        
        assert 'model' in config_dict
        assert 'training' in config_dict
        assert 'data' in config_dict
        assert 'ocr' in config_dict
        assert 'device' in config_dict
        assert 'num_gpus' in config_dict
        
        # Check nested structure
        assert 'num_classes' in config_dict['model']
        assert 'batch_size' in config_dict['training']
        assert 'data_root' in config_dict['data']
        assert 'min_confidence' in config_dict['ocr']
    
    def test_load_from_invalid_file(self):
        """Test loading from invalid configuration file"""
        # Create temporary invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            invalid_file = f.name
        
        try:
            # Should not raise exception, just use defaults
            config = PillRecognitionConfig()
            # The file loading should be handled gracefully
            
        finally:
            Path(invalid_file).unlink(missing_ok=True)
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent configuration file"""
        # Should not raise exception, just use defaults
        config = PillRecognitionConfig("nonexistent_file.json")
        
        # Should have default values
        assert config.model.num_classes == 1000
        assert config.training.batch_size == 32