"""
Multimodal transformer models for pill recognition
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple
import math
from transformers import AutoModel, AutoTokenizer
import timm
import logging

logger = logging.getLogger(__name__)


class VisionTransformer(nn.Module):
    """
    Vision Transformer for processing pill images
    """
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # Load pre-trained vision transformer
        self.backbone = timm.create_model(
            config.vision_model_name,
            pretrained=True,
            num_classes=0,  # Remove classification head
            global_pool=''  # Remove global pooling
        )
        
        # Get feature dimensions from backbone
        self.feature_dim = self.backbone.num_features
        
        # Projection layer to match embedding dimension
        self.projection = nn.Linear(self.feature_dim, config.vision_embed_dim)
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(config.vision_embed_dim)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for vision transformer
        
        Args:
            images: Batch of images [batch_size, channels, height, width]
            
        Returns:
            Vision features [batch_size, num_patches, embed_dim]
        """
        # Extract features using backbone
        features = self.backbone.forward_features(images)
        
        # features shape: [batch_size, num_patches, feature_dim]
        batch_size, num_patches, _ = features.shape
        
        # Project to embedding dimension
        features = self.projection(features)
        features = self.layer_norm(features)
        features = self.dropout(features)
        
        return features


class TextTransformer(nn.Module):
    """
    Text Transformer for processing pill imprint text
    """
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # Load pre-trained text model
        self.backbone = AutoModel.from_pretrained(config.text_model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(config.text_model_name)
        
        # Get feature dimensions
        self.feature_dim = self.backbone.config.hidden_size
        
        # Projection layer to match embedding dimension
        self.projection = nn.Linear(self.feature_dim, config.text_embed_dim)
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(config.text_embed_dim)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for text transformer
        
        Args:
            input_ids: Token IDs [batch_size, sequence_length]
            attention_mask: Attention mask [batch_size, sequence_length]
            
        Returns:
            Text features [batch_size, sequence_length, embed_dim]
        """
        # Get text features
        outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        features = outputs.last_hidden_state
        
        # Project to embedding dimension
        features = self.projection(features)
        features = self.layer_norm(features)
        features = self.dropout(features)
        
        return features


class CrossModalAttention(nn.Module):
    """
    Cross-modal attention mechanism for fusing vision and text features
    """
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.embed_dim = config.fusion_embed_dim
        self.num_heads = config.fusion_num_heads
        self.head_dim = self.embed_dim // self.num_heads
        
        assert self.embed_dim % self.num_heads == 0, "embed_dim must be divisible by num_heads"
        
        # Vision-to-text attention
        self.vision_to_text_attention = nn.MultiheadAttention(
            embed_dim=self.embed_dim,
            num_heads=self.num_heads,
            dropout=config.dropout_rate,
            batch_first=True
        )
        
        # Text-to-vision attention
        self.text_to_vision_attention = nn.MultiheadAttention(
            embed_dim=self.embed_dim,
            num_heads=self.num_heads,
            dropout=config.dropout_rate,
            batch_first=True
        )
        
        # Self-attention for fusion
        self.self_attention = nn.MultiheadAttention(
            embed_dim=self.embed_dim,
            num_heads=self.num_heads,
            dropout=config.dropout_rate,
            batch_first=True
        )
        
        # Feed-forward networks
        self.ffn = nn.Sequential(
            nn.Linear(self.embed_dim, self.embed_dim * 4),
            nn.GELU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(self.embed_dim * 4, self.embed_dim),
            nn.Dropout(config.dropout_rate)
        )
        
        # Layer normalizations
        self.layer_norm1 = nn.LayerNorm(self.embed_dim)
        self.layer_norm2 = nn.LayerNorm(self.embed_dim)
        self.layer_norm3 = nn.LayerNorm(self.embed_dim)
        
    def forward(self, vision_features: torch.Tensor, text_features: torch.Tensor,
                vision_mask: Optional[torch.Tensor] = None,
                text_mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Cross-modal attention fusion
        
        Args:
            vision_features: [batch_size, num_patches, embed_dim]
            text_features: [batch_size, sequence_length, embed_dim]
            vision_mask: Optional mask for vision features
            text_mask: Optional mask for text features
            
        Returns:
            Tuple of (fused_vision_features, fused_text_features)
        """
        # Vision-to-text attention
        v2t_output, _ = self.vision_to_text_attention(
            query=text_features,
            key=vision_features,
            value=vision_features,
            key_padding_mask=vision_mask
        )
        text_features = self.layer_norm1(text_features + v2t_output)
        
        # Text-to-vision attention
        t2v_output, _ = self.text_to_vision_attention(
            query=vision_features,
            key=text_features,
            value=text_features,
            key_padding_mask=text_mask
        )
        vision_features = self.layer_norm2(vision_features + t2v_output)
        
        # Concatenate and apply self-attention
        combined_features = torch.cat([vision_features, text_features], dim=1)
        
        # Create combined mask
        combined_mask = None
        if vision_mask is not None or text_mask is not None:
            batch_size = combined_features.size(0)
            vision_len = vision_features.size(1)
            text_len = text_features.size(1)
            
            if vision_mask is None:
                vision_mask = torch.zeros(batch_size, vision_len, device=vision_features.device, dtype=torch.bool)
            if text_mask is None:
                text_mask = torch.zeros(batch_size, text_len, device=text_features.device, dtype=torch.bool)
            
            combined_mask = torch.cat([vision_mask, text_mask], dim=1)
        
        # Self-attention on combined features
        attn_output, _ = self.self_attention(
            query=combined_features,
            key=combined_features,
            value=combined_features,
            key_padding_mask=combined_mask
        )
        combined_features = self.layer_norm3(combined_features + attn_output)
        
        # Feed-forward network
        ffn_output = self.ffn(combined_features)
        combined_features = combined_features + ffn_output
        
        # Split back to vision and text features
        vision_out = combined_features[:, :vision_features.size(1), :]
        text_out = combined_features[:, vision_features.size(1):, :]
        
        return vision_out, text_out


class MultimodalPillTransformer(nn.Module):
    """
    Complete multimodal transformer for pill recognition combining vision and text
    """
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # Vision and text transformers
        self.vision_transformer = VisionTransformer(config)
        self.text_transformer = TextTransformer(config)
        
        # Project to fusion dimension
        self.vision_projection = nn.Linear(config.vision_embed_dim, config.fusion_embed_dim)
        self.text_projection = nn.Linear(config.text_embed_dim, config.fusion_embed_dim)
        
        # Cross-modal attention layers
        self.fusion_layers = nn.ModuleList([
            CrossModalAttention(config) for _ in range(config.fusion_num_layers)
        ])
        
        # Global pooling for classification
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(config.fusion_embed_dim * 2, config.fusion_embed_dim),
            nn.GELU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(config.fusion_embed_dim, config.num_classes)
        )
        
        # Initialize weights
        self.apply(self._init_weights)
        
    def _init_weights(self, module):
        """Initialize model weights"""
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.zeros_(module.bias)
            torch.nn.init.ones_(module.weight)
    
    def forward(self, images: torch.Tensor, input_ids: torch.Tensor,
                attention_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass for multimodal pill recognition
        
        Args:
            images: Batch of pill images [batch_size, channels, height, width]
            input_ids: Token IDs for text [batch_size, sequence_length]
            attention_mask: Attention mask for text [batch_size, sequence_length]
            
        Returns:
            Dictionary containing:
            - logits: Classification logits [batch_size, num_classes]
            - vision_features: Vision features after fusion
            - text_features: Text features after fusion
        """
        # Extract initial features
        vision_features = self.vision_transformer(images)
        text_features = self.text_transformer(input_ids, attention_mask)
        
        # Project to fusion dimension
        vision_features = self.vision_projection(vision_features)
        text_features = self.text_projection(text_features)
        
        # Create masks (invert attention_mask for padding)
        text_mask = ~attention_mask.bool() if attention_mask is not None else None
        
        # Apply cross-modal fusion layers
        for fusion_layer in self.fusion_layers:
            vision_features, text_features = fusion_layer(
                vision_features, text_features, text_mask=text_mask
            )
        
        # Global pooling
        # Vision: [batch_size, num_patches, embed_dim] -> [batch_size, embed_dim]
        vision_pooled = self.global_pool(vision_features.transpose(1, 2)).squeeze(-1)
        
        # Text: Use [CLS] token or mean pooling with attention mask
        if attention_mask is not None:
            # Mean pooling with attention mask
            mask_expanded = attention_mask.unsqueeze(-1).expand(text_features.size()).float()
            sum_embeddings = torch.sum(text_features * mask_expanded, dim=1)
            sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
            text_pooled = sum_embeddings / sum_mask
        else:
            text_pooled = text_features.mean(dim=1)
        
        # Concatenate features for classification
        combined_features = torch.cat([vision_pooled, text_pooled], dim=-1)
        
        # Classification
        logits = self.classifier(combined_features)
        
        return {
            'logits': logits,
            'vision_features': vision_features,
            'text_features': text_features,
            'vision_pooled': vision_pooled,
            'text_pooled': text_pooled
        }
    
    def extract_features(self, images: torch.Tensor, input_ids: torch.Tensor,
                        attention_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Extract features without classification for analysis or retrieval
        
        Args:
            images: Batch of pill images
            input_ids: Token IDs for text
            attention_mask: Attention mask for text
            
        Returns:
            Dictionary of extracted features
        """
        with torch.no_grad():
            outputs = self.forward(images, input_ids, attention_mask)
            return {
                'vision_features': outputs['vision_pooled'],
                'text_features': outputs['text_pooled'],
                'combined_features': torch.cat([
                    outputs['vision_pooled'], 
                    outputs['text_pooled']
                ], dim=-1)
            }