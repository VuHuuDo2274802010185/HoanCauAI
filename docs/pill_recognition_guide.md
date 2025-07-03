# Multimodal Pill Recognition System

A comprehensive multimodal transformer system for pill recognition that combines image data with text imprint information using state-of-the-art deep learning techniques.

## Features

### Core Capabilities
- **Multimodal Architecture**: Combines visual features from pill images with textual information from imprints
- **Transformer-Based Models**: Uses Vision Transformer (ViT) for images and BERT for text processing
- **Cross-Modal Attention**: Advanced fusion mechanism for combining visual and textual features
- **OCR Integration**: Supports both Tesseract and PaddleOCR for text extraction from pill images
- **Distributed Training**: Multi-GPU training with Distributed Data Parallel (DDP)
- **Comprehensive Testing**: Full test suite for all components

### Technical Implementation
- **Framework**: PyTorch with HuggingFace Transformers
- **Vision Processing**: timm models with configurable architectures
- **Text Processing**: Pre-trained BERT models with custom tokenization
- **Data Augmentation**: Advanced image augmentations using Albumentations
- **Mixed Precision**: Automatic Mixed Precision (AMP) for efficient training
- **Configuration Management**: Flexible JSON-based configuration system

## Architecture Overview

The system consists of several key components:

```
┌─────────────────┐    ┌─────────────────┐
│   Pill Image    │    │  Text Imprint   │
│      Input      │    │     Input       │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│     Vision      │    │      Text       │
│  Transformer    │    │  Transformer    │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│    Vision       │    │     Text        │
│  Projection     │    │  Projection     │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     ▼
          ┌─────────────────┐
          │  Cross-Modal    │
          │   Attention     │
          │    Fusion       │
          └─────────┬───────┘
                    ▼
          ┌─────────────────┐
          │ Classification  │
          │     Head        │
          └─────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- CUDA-capable GPU (recommended)
- Git

### Step 1: Clone Repository
```bash
git clone https://github.com/VuHuuDo2274802010185/HoanCauAI.git
cd HoanCauAI
```

### Step 2: Install Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

### Step 3: Install OCR Dependencies

#### Tesseract OCR
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

#### PaddleOCR (Optional)
```bash
pip install paddlepaddle-gpu  # For GPU
# or
pip install paddlepaddle      # For CPU only
```

## Quick Start

### 1. Data Preparation

Organize your pill dataset in the following structure:
```
data/pills/
├── class_1/
│   ├── image_1.jpg
│   ├── image_1.txt  # Optional text file
│   ├── image_2.jpg
│   └── ...
├── class_2/
│   ├── image_1.jpg
│   ├── image_2.jpg
│   └── ...
└── ...
```

Create train/validation/test splits:
```bash
python scripts/pill_recognition/prepare_data.py \
    --data-root data/pills \
    --create-splits \
    --train-ratio 0.7 \
    --val-ratio 0.15 \
    --test-ratio 0.15
```

Extract text from images using OCR:
```bash
python scripts/pill_recognition/prepare_data.py \
    --data-root data/pills \
    --extract-text \
    --output-format both
```

### 2. Training

#### Single GPU Training
```bash
python scripts/pill_recognition/train.py \
    --data-root data/pills \
    --output-dir checkpoints \
    --config configs/pill_recognition_default.json \
    --batch-size 32 \
    --num-epochs 50 \
    --single-gpu
```

#### Multi-GPU Distributed Training
```bash
python scripts/pill_recognition/train.py \
    --data-root data/pills \
    --output-dir checkpoints \
    --config configs/pill_recognition_default.json \
    --batch-size 32 \
    --num-epochs 50
```

#### Resume Training from Checkpoint
```bash
python scripts/pill_recognition/train.py \
    --data-root data/pills \
    --output-dir checkpoints \
    --resume checkpoints/best_model.pth
```

### 3. Inference

#### Single Image Prediction
```bash
python scripts/pill_recognition/inference.py \
    --model-path checkpoints/best_model.pth \
    --image path/to/pill_image.jpg \
    --output results.json
```

#### Batch Processing
```bash
python scripts/pill_recognition/inference.py \
    --model-path checkpoints/best_model.pth \
    --image-dir path/to/images/ \
    --output batch_results.json \
    --batch-size 16
```

#### Dataset Evaluation
```bash
python scripts/pill_recognition/inference.py \
    --model-path checkpoints/best_model.pth \
    --dataset data/pills \
    --split test
```

## Configuration

The system uses JSON configuration files for flexible parameter management. Key configuration sections:

### Model Configuration
```json
{
  "model": {
    "vision_model_name": "vit-base-patch16-224",
    "text_model_name": "bert-base-uncased", 
    "fusion_embed_dim": 512,
    "num_classes": 1000,
    "image_size": 224
  }
}
```

### Training Configuration
```json
{
  "training": {
    "batch_size": 32,
    "learning_rate": 1e-4,
    "num_epochs": 100,
    "use_ddp": true,
    "use_amp": true,
    "optimizer": "adamw",
    "scheduler": "cosine"
  }
}
```

### OCR Configuration
```json
{
  "ocr": {
    "use_tesseract": true,
    "use_paddle_ocr": true,
    "min_confidence": 0.5,
    "clean_text": true
  }
}
```

## API Usage

### Python API

```python
from pill_recognition import (
    PillRecognitionConfig,
    MultimodalPillTransformer,
    PillPredictor,
    OCRExtractor
)

# Load configuration
config = PillRecognitionConfig("configs/pill_recognition_default.json")

# Initialize predictor
predictor = PillPredictor(
    model_path="checkpoints/best_model.pth",
    config=config
)

# Make prediction
result = predictor.predict_single(
    image="path/to/pill.jpg",
    extract_text=True
)

print(f"Top prediction: {result['predictions'][0]}")
```

### OCR Usage

```python
from pill_recognition import OCRExtractor, OCRConfig

# Initialize OCR
config = OCRConfig()
ocr = OCRExtractor(config)

# Extract text from image
result = ocr.extract_text("path/to/pill.jpg")
print(f"Extracted text: {result['text']}")
print(f"Confidence: {result['confidence']}")
```

## Training Your Own Model

### 1. Prepare Your Dataset

Ensure your dataset follows the required structure:
- Images in class-based folders
- Optional text files with same name as images
- Balanced distribution across classes

### 2. Configure Model Architecture

Create a custom configuration file:
```json
{
  "model": {
    "num_classes": 500,  # Your number of pill types
    "vision_model_name": "vit-large-patch16-224",
    "fusion_embed_dim": 768
  },
  "training": {
    "batch_size": 16,
    "learning_rate": 5e-5,
    "num_epochs": 200
  }
}
```

### 3. Monitor Training

Training logs and metrics are saved to:
- TensorBoard logs: `logs/pill_recognition_*/`
- Checkpoints: `checkpoints/`
- Training logs: `logs/training_rank_*.log`

View training progress:
```bash
tensorboard --logdir logs/
```

## Performance Optimization

### Multi-GPU Training
- Automatic detection of available GPUs
- Distributed Data Parallel (DDP) for efficient scaling
- Gradient synchronization across devices

### Memory Optimization
- Mixed precision training (AMP)
- Gradient checkpointing for large models
- Efficient data loading with multiple workers

### Inference Optimization
- Batch processing for multiple images
- GPU acceleration when available
- Optimized preprocessing pipelines

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest test/pill_recognition/ -v

# Run specific test modules
python -m pytest test/pill_recognition/test_models.py -v
python -m pytest test/pill_recognition/test_ocr.py -v

# Run with coverage
python -m pytest test/pill_recognition/ --cov=pill_recognition --cov-report=html
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   - Reduce batch size in configuration
   - Enable gradient checkpointing
   - Use mixed precision training

2. **OCR Installation Issues**
   - Install Tesseract system package
   - Check PaddleOCR GPU compatibility
   - Verify language packages are installed

3. **Model Loading Errors**
   - Check checkpoint file integrity
   - Verify configuration matches saved model
   - Ensure all dependencies are installed

4. **Distributed Training Issues**
   - Check NCCL backend availability
   - Verify GPU visibility (CUDA_VISIBLE_DEVICES)
   - Ensure consistent PyTorch versions across nodes

### Performance Tips

1. **Data Loading**
   - Increase `num_workers` for faster data loading
   - Use SSD storage for datasets
   - Enable `pin_memory` for GPU training

2. **Training Speed**
   - Use larger batch sizes when possible
   - Enable mixed precision training
   - Consider gradient accumulation for large models

3. **Memory Usage**
   - Monitor GPU memory usage
   - Use DataLoader with appropriate batch sizes
   - Clear unused variables in training loops

## Integration with Existing System

The pill recognition system is designed to integrate seamlessly with the existing CV processing system:

### Adding to Existing Modules
```python
# In your existing module
from pill_recognition import PillPredictor, PillRecognitionConfig

class EnhancedCVProcessor(CVProcessor):
    def __init__(self):
        super().__init__()
        # Initialize pill recognition
        config = PillRecognitionConfig()
        self.pill_predictor = PillPredictor(
            model_path="models/pill_recognition.pth",
            config=config
        )
    
    def process_pill_image(self, image_path):
        return self.pill_predictor.predict_single(image_path)
```

### API Integration
The system can be easily integrated into the existing FastAPI endpoints for real-time pill recognition.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- HuggingFace Transformers for model implementations
- PyTorch team for the deep learning framework
- timm library for vision model architectures
- Albumentations for image augmentation
- Tesseract and PaddleOCR teams for OCR capabilities