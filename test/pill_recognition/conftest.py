"""
Test configuration for pill recognition module
"""
import pytest
import torch
import numpy as np
from PIL import Image
import tempfile
import os
from pathlib import Path


@pytest.fixture
def config():
    """Fixture for test configuration"""
    from pill_recognition.config import PillRecognitionConfig
    config = PillRecognitionConfig()
    
    # Override for testing
    config.model.num_classes = 10
    config.model.vision_embed_dim = 32
    config.model.text_embed_dim = 32
    config.model.fusion_embed_dim = 32
    config.model.fusion_num_layers = 1
    config.model.image_size = 64
    config.training.batch_size = 2
    config.training.num_epochs = 2
    config.training.use_ddp = False
    config.training.use_amp = False
    config.training.num_workers = 0
    
    return config


@pytest.fixture
def sample_image():
    """Fixture for sample image"""
    # Create a dummy image
    image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    return Image.fromarray(image)


@pytest.fixture
def sample_text():
    """Fixture for sample text"""
    return "PILL123 10mg"


@pytest.fixture
def temp_dataset_dir():
    """Fixture for temporary dataset directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create dataset structure
        temp_path = Path(temp_dir)
        
        # Create train/val/test splits
        for split in ['train', 'val', 'test']:
            split_dir = temp_path / split
            split_dir.mkdir(exist_ok=True)
            
            # Create class directories
            for class_name in ['class_0', 'class_1']:
                class_dir = split_dir / class_name
                class_dir.mkdir(exist_ok=True)
                
                # Create sample images and text files
                for i in range(3):
                    # Create image
                    image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
                    image_pil = Image.fromarray(image)
                    image_path = class_dir / f"image_{i}.jpg"
                    image_pil.save(image_path)
                    
                    # Create text file
                    text_path = class_dir / f"image_{i}.txt"
                    with open(text_path, 'w') as f:
                        f.write(f"Sample text for {class_name} image {i}")
        
        yield temp_path


@pytest.fixture
def mock_model_checkpoint(config):
    """Fixture for mock model checkpoint"""
    from pill_recognition.models import MultimodalPillTransformer
    
    model = MultimodalPillTransformer(config.model)
    
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'config': config.to_dict(),
        'label_mapping': {i: f"class_{i}" for i in range(config.model.num_classes)},
        'epoch': 10,
        'best_val_acc': 0.85
    }
    
    return checkpoint


# Skip tests if PyTorch not available - remove CUDA requirement for basic testing
pytestmark = pytest.mark.skipif(
    False,  # Always run tests - remove CUDA requirement
    reason="PyTorch CUDA not available"
)