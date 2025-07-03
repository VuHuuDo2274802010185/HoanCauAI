"""
Tests for multimodal transformer models
"""
import pytest
import torch
import torch.nn as nn
from transformers import AutoTokenizer

from pill_recognition.models import (
    VisionTransformer,
    TextTransformer, 
    CrossModalAttention,
    MultimodalPillTransformer
)


class TestVisionTransformer:
    """Test VisionTransformer class"""
    
    def test_initialization(self, config):
        """Test vision transformer initialization"""
        model = VisionTransformer(config.model)
        
        assert isinstance(model.backbone, nn.Module)
        assert isinstance(model.projection, nn.Linear)
        assert isinstance(model.layer_norm, nn.LayerNorm)
        assert isinstance(model.dropout, nn.Dropout)
        
        # Check dimensions
        assert model.projection.out_features == config.model.vision_embed_dim
    
    def test_forward_pass(self, config):
        """Test vision transformer forward pass"""
        model = VisionTransformer(config.model)
        
        # Create dummy input
        batch_size = 2
        channels = 3
        height = width = config.model.image_size
        
        images = torch.randn(batch_size, channels, height, width)
        
        # Forward pass
        features = model(images)
        
        # Check output shape
        assert features.dim() == 3  # [batch_size, num_patches, embed_dim]
        assert features.size(0) == batch_size
        assert features.size(2) == config.model.vision_embed_dim
    
    def test_feature_dimensions(self, config):
        """Test that feature dimensions are correct"""
        model = VisionTransformer(config.model)
        
        # Test with different batch sizes
        for batch_size in [1, 2, 4]:
            images = torch.randn(batch_size, 3, config.model.image_size, config.model.image_size)
            features = model(images)
            
            assert features.size(0) == batch_size
            assert features.size(2) == config.model.vision_embed_dim


class TestTextTransformer:
    """Test TextTransformer class"""
    
    def test_initialization(self, config):
        """Test text transformer initialization"""
        model = TextTransformer(config.model)
        
        assert hasattr(model, 'backbone')
        assert hasattr(model, 'tokenizer')
        assert isinstance(model.projection, nn.Linear)
        assert isinstance(model.layer_norm, nn.LayerNorm)
        assert isinstance(model.dropout, nn.Dropout)
        
        # Check dimensions
        assert model.projection.out_features == config.model.text_embed_dim
    
    def test_forward_pass(self, config):
        """Test text transformer forward pass"""
        model = TextTransformer(config.model)
        tokenizer = AutoTokenizer.from_pretrained(config.model.text_model_name)
        
        # Create dummy input
        texts = ["PILL123 10mg", "TABLET ABC 5mg"]
        encoding = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=config.model.text_max_length,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids']
        attention_mask = encoding['attention_mask']
        
        # Forward pass
        features = model(input_ids, attention_mask)
        
        # Check output shape
        assert features.dim() == 3  # [batch_size, seq_len, embed_dim]
        assert features.size(0) == len(texts)
        assert features.size(2) == config.model.text_embed_dim
    
    def test_different_sequence_lengths(self, config):
        """Test with different sequence lengths"""
        model = TextTransformer(config.model)
        tokenizer = AutoTokenizer.from_pretrained(config.model.text_model_name)
        
        # Test with different text lengths
        texts = [
            "PILL",
            "PILL123 10mg extra long description here",
            ""
        ]
        
        encoding = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=config.model.text_max_length,
            return_tensors='pt'
        )
        
        features = model(encoding['input_ids'], encoding['attention_mask'])
        
        assert features.size(0) == len(texts)
        assert features.size(2) == config.model.text_embed_dim


class TestCrossModalAttention:
    """Test CrossModalAttention class"""
    
    def test_initialization(self, config):
        """Test cross-modal attention initialization"""
        model = CrossModalAttention(config.model)
        
        assert isinstance(model.vision_to_text_attention, nn.MultiheadAttention)
        assert isinstance(model.text_to_vision_attention, nn.MultiheadAttention)
        assert isinstance(model.self_attention, nn.MultiheadAttention)
        assert isinstance(model.ffn, nn.Sequential)
        
        # Check dimensions
        assert model.embed_dim == config.model.fusion_embed_dim
        assert model.num_heads == config.model.fusion_num_heads
    
    def test_forward_pass(self, config):
        """Test cross-modal attention forward pass"""
        model = CrossModalAttention(config.model)
        
        batch_size = 2
        vision_seq_len = 10
        text_seq_len = 8
        embed_dim = config.model.fusion_embed_dim
        
        # Create dummy features
        vision_features = torch.randn(batch_size, vision_seq_len, embed_dim)
        text_features = torch.randn(batch_size, text_seq_len, embed_dim)
        
        # Forward pass
        fused_vision, fused_text = model(vision_features, text_features)
        
        # Check output shapes
        assert fused_vision.shape == vision_features.shape
        assert fused_text.shape == text_features.shape
    
    def test_forward_with_masks(self, config):
        """Test cross-modal attention with attention masks"""
        model = CrossModalAttention(config.model)
        
        batch_size = 2
        vision_seq_len = 10
        text_seq_len = 8
        embed_dim = config.model.fusion_embed_dim
        
        # Create dummy features and masks
        vision_features = torch.randn(batch_size, vision_seq_len, embed_dim)
        text_features = torch.randn(batch_size, text_seq_len, embed_dim)
        
        # Create attention masks (True for padding)
        vision_mask = torch.zeros(batch_size, vision_seq_len, dtype=torch.bool)
        text_mask = torch.zeros(batch_size, text_seq_len, dtype=torch.bool)
        text_mask[0, -2:] = True  # Mask last 2 tokens of first sample
        
        # Forward pass
        fused_vision, fused_text = model(
            vision_features, text_features,
            vision_mask=vision_mask, text_mask=text_mask
        )
        
        # Check output shapes
        assert fused_vision.shape == vision_features.shape
        assert fused_text.shape == text_features.shape


class TestMultimodalPillTransformer:
    """Test complete multimodal transformer"""
    
    def test_initialization(self, config):
        """Test multimodal transformer initialization"""
        model = MultimodalPillTransformer(config.model)
        
        assert isinstance(model.vision_transformer, VisionTransformer)
        assert isinstance(model.text_transformer, TextTransformer)
        assert isinstance(model.vision_projection, nn.Linear)
        assert isinstance(model.text_projection, nn.Linear)
        assert isinstance(model.fusion_layers, nn.ModuleList)
        assert isinstance(model.classifier, nn.Sequential)
        
        # Check number of fusion layers
        assert len(model.fusion_layers) == config.model.fusion_num_layers
    
    def test_forward_pass(self, config):
        """Test complete forward pass"""
        model = MultimodalPillTransformer(config.model)
        tokenizer = AutoTokenizer.from_pretrained(config.model.text_model_name)
        
        batch_size = 2
        
        # Create dummy inputs
        images = torch.randn(batch_size, 3, config.model.image_size, config.model.image_size)
        
        texts = ["PILL123 10mg", "TABLET ABC 5mg"]
        encoding = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=config.model.text_max_length,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids']
        attention_mask = encoding['attention_mask']
        
        # Forward pass
        outputs = model(images, input_ids, attention_mask)
        
        # Check outputs
        assert isinstance(outputs, dict)
        assert 'logits' in outputs
        assert 'vision_features' in outputs
        assert 'text_features' in outputs
        assert 'vision_pooled' in outputs
        assert 'text_pooled' in outputs
        
        # Check shapes
        logits = outputs['logits']
        assert logits.size(0) == batch_size
        assert logits.size(1) == config.model.num_classes
        
        vision_pooled = outputs['vision_pooled']
        assert vision_pooled.size(0) == batch_size
        assert vision_pooled.size(1) == config.model.fusion_embed_dim
        
        text_pooled = outputs['text_pooled']
        assert text_pooled.size(0) == batch_size
        assert text_pooled.size(1) == config.model.fusion_embed_dim
    
    def test_extract_features(self, config):
        """Test feature extraction without classification"""
        model = MultimodalPillTransformer(config.model)
        tokenizer = AutoTokenizer.from_pretrained(config.model.text_model_name)
        
        batch_size = 2
        
        # Create dummy inputs
        images = torch.randn(batch_size, 3, config.model.image_size, config.model.image_size)
        
        texts = ["PILL123 10mg", "TABLET ABC 5mg"]
        encoding = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=config.model.text_max_length,
            return_tensors='pt'
        )
        
        # Extract features
        features = model.extract_features(images, encoding['input_ids'], encoding['attention_mask'])
        
        # Check outputs
        assert isinstance(features, dict)
        assert 'vision_features' in features
        assert 'text_features' in features
        assert 'combined_features' in features
        
        # Check shapes
        vision_features = features['vision_features']
        assert vision_features.size(0) == batch_size
        assert vision_features.size(1) == config.model.fusion_embed_dim
        
        text_features = features['text_features']
        assert text_features.size(0) == batch_size
        assert text_features.size(1) == config.model.fusion_embed_dim
        
        combined_features = features['combined_features']
        assert combined_features.size(0) == batch_size
        assert combined_features.size(1) == config.model.fusion_embed_dim * 2
    
    def test_model_parameters(self, config):
        """Test that model has trainable parameters"""
        model = MultimodalPillTransformer(config.model)
        
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        assert total_params > 0
        assert trainable_params > 0
        assert trainable_params == total_params  # All parameters should be trainable
    
    def test_model_device_movement(self, config):
        """Test moving model to different devices"""
        model = MultimodalPillTransformer(config.model)
        
        # Test CPU
        model_cpu = model.cpu()
        assert next(model_cpu.parameters()).device.type == 'cpu'
        
        # Test CUDA if available
        if torch.cuda.is_available():
            model_cuda = model.cuda()
            assert next(model_cuda.parameters()).device.type == 'cuda'