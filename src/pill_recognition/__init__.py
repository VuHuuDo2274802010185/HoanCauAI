"""
Multimodal Transformer System for Pill Recognition

This package provides a complete multimodal transformer system that combines
image data with text imprint information for pill recognition tasks.

Key components:
- Vision transformer for image processing
- Text transformer for imprint processing
- Cross-modal attention mechanisms for feature fusion
- OCR extraction using Tesseract and PaddleOCR
- Distributed training capabilities for multi-GPU environments
"""

__version__ = "0.1.0"
__author__ = "HoanCau AI Team"

from .models import MultimodalPillTransformer
from .data import PillDataset, PillDataLoader
from .training import PillTrainer
from .inference import PillPredictor
from .ocr import OCRExtractor
from .config import PillRecognitionConfig

__all__ = [
    "MultimodalPillTransformer",
    "PillDataset", 
    "PillDataLoader",
    "PillTrainer",
    "PillPredictor",
    "OCRExtractor",
    "PillRecognitionConfig"
]