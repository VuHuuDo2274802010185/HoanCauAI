#!/usr/bin/env python3
"""
Data preparation script for pill recognition dataset
"""
import os
import sys
import argparse
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import random

# Add src directory to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pill_recognition.ocr import OCRExtractor
from pill_recognition.config import PillRecognitionConfig

logger = logging.getLogger(__name__)


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/data_preparation.log')
        ]
    )


def create_train_val_test_splits(data_root: str, train_ratio: float = 0.7, 
                                val_ratio: float = 0.15, test_ratio: float = 0.15,
                                random_seed: int = 42):
    """
    Create train/validation/test splits from organized data
    
    Args:
        data_root: Root directory containing class subdirectories
        train_ratio: Fraction of data for training
        val_ratio: Fraction of data for validation
        test_ratio: Fraction of data for testing
        random_seed: Random seed for reproducibility
    """
    random.seed(random_seed)
    
    data_root = Path(data_root)
    
    # Find all class directories
    class_dirs = [d for d in data_root.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not class_dirs:
        logger.error(f"No class directories found in {data_root}")
        return
    
    logger.info(f"Found {len(class_dirs)} classes")
    
    # Create split directories
    for split in ['train', 'val', 'test']:
        split_dir = data_root / split
        split_dir.mkdir(exist_ok=True)
        
        for class_dir in class_dirs:
            (split_dir / class_dir.name).mkdir(exist_ok=True)
    
    # Split data for each class
    total_moved = {'train': 0, 'val': 0, 'test': 0}
    
    for class_dir in class_dirs:
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = [f for f in class_dir.iterdir() 
                      if f.suffix.lower() in image_extensions]
        
        if not image_files:
            logger.warning(f"No images found in {class_dir}")
            continue
        
        # Shuffle files
        random.shuffle(image_files)
        
        # Calculate split sizes
        num_images = len(image_files)
        num_train = int(num_images * train_ratio)
        num_val = int(num_images * val_ratio)
        num_test = num_images - num_train - num_val
        
        # Split files
        train_files = image_files[:num_train]
        val_files = image_files[num_train:num_train + num_val]
        test_files = image_files[num_train + num_val:]
        
        logger.info(f"Class {class_dir.name}: {num_train} train, {num_val} val, {num_test} test")
        
        # Move files to split directories
        for split, files in [('train', train_files), ('val', val_files), ('test', test_files)]:
            split_class_dir = data_root / split / class_dir.name
            
            for file in files:
                # Move image file
                dest_image = split_class_dir / file.name
                shutil.copy2(file, dest_image)
                
                # Move corresponding text file if exists
                text_file = file.with_suffix('.txt')
                if text_file.exists():
                    dest_text = split_class_dir / text_file.name
                    shutil.copy2(text_file, dest_text)
            
            total_moved[split] += len(files)
    
    logger.info(f"Total files moved: {total_moved}")


def extract_text_from_images(data_root: str, output_format: str = "individual"):
    """
    Extract text from images using OCR and save as text files
    
    Args:
        data_root: Root directory containing images
        output_format: "individual" for separate .txt files, "json" for consolidated JSON
    """
    config = PillRecognitionConfig()
    ocr_extractor = OCRExtractor(config.ocr)
    
    data_root = Path(data_root)
    
    # Find all image files recursively
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(data_root.rglob(f"*{ext}"))
        image_files.extend(data_root.rglob(f"*{ext.upper()}"))
    
    if not image_files:
        logger.error(f"No image files found in {data_root}")
        return
    
    logger.info(f"Found {len(image_files)} images for text extraction")
    
    all_results = []
    successful = 0
    failed = 0
    
    for i, image_file in enumerate(image_files):
        try:
            # Extract text
            result = ocr_extractor.extract_text(str(image_file))
            extracted_text = result.get('text', '').strip()
            confidence = result.get('confidence', 0.0)
            
            if output_format == "individual":
                # Save as individual text file
                text_file = image_file.with_suffix('.txt')
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
            
            # Collect for JSON output
            all_results.append({
                'image_path': str(image_file.relative_to(data_root)),
                'text': extracted_text,
                'confidence': confidence,
                'engine': result.get('engine', 'unknown')
            })
            
            successful += 1
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(image_files)} images")
        
        except Exception as e:
            logger.error(f"Failed to extract text from {image_file}: {e}")
            failed += 1
    
    # Save JSON results
    if output_format == "json" or output_format == "both":
        json_file = data_root / "ocr_results.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        logger.info(f"OCR results saved to {json_file}")
    
    logger.info(f"OCR extraction completed: {successful} successful, {failed} failed")


def create_annotations_file(data_root: str, split: str):
    """
    Create annotations file for a dataset split
    
    Args:
        data_root: Root directory containing data
        split: Dataset split ('train', 'val', 'test')
    """
    data_root = Path(data_root)
    split_dir = data_root / split
    
    if not split_dir.exists():
        logger.error(f"Split directory not found: {split_dir}")
        return
    
    annotations = []
    
    # Find all class directories in split
    class_dirs = [d for d in split_dir.iterdir() if d.is_dir()]
    
    for class_dir in class_dirs:
        class_name = class_dir.name
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = [f for f in class_dir.iterdir() 
                      if f.suffix.lower() in image_extensions]
        
        for image_file in image_files:
            # Get relative path from data root
            relative_path = image_file.relative_to(data_root)
            
            # Load text if exists
            text_file = image_file.with_suffix('.txt')
            text = ""
            if text_file.exists():
                try:
                    with open(text_file, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                except Exception as e:
                    logger.warning(f"Failed to read text file {text_file}: {e}")
            
            # Create annotation
            annotation = {
                'image_path': str(relative_path),
                'text': text,
                'label': class_name,
                'pill_id': image_file.stem,
                'metadata': {
                    'split': split,
                    'class_dir': class_name
                }
            }
            
            annotations.append(annotation)
    
    # Save annotations file
    annotations_file = data_root / f"{split}_annotations.json"
    with open(annotations_file, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created annotations file with {len(annotations)} samples: {annotations_file}")


def validate_dataset(data_root: str):
    """
    Validate dataset structure and content
    
    Args:
        data_root: Root directory containing dataset
    """
    data_root = Path(data_root)
    
    logger.info(f"Validating dataset: {data_root}")
    
    issues = []
    stats = {
        'total_images': 0,
        'total_classes': 0,
        'images_with_text': 0,
        'split_counts': {}
    }
    
    # Check for split directories
    for split in ['train', 'val', 'test']:
        split_dir = data_root / split
        if split_dir.exists():
            class_dirs = [d for d in split_dir.iterdir() if d.is_dir()]
            stats['split_counts'][split] = 0
            
            for class_dir in class_dirs:
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
                image_files = [f for f in class_dir.iterdir() 
                              if f.suffix.lower() in image_extensions]
                
                stats['split_counts'][split] += len(image_files)
                stats['total_images'] += len(image_files)
                
                # Check for text files
                for image_file in image_files:
                    text_file = image_file.with_suffix('.txt')
                    if text_file.exists():
                        stats['images_with_text'] += 1
            
            if class_dirs:
                stats['total_classes'] = len(class_dirs)
        else:
            issues.append(f"Split directory missing: {split}")
    
    # Check class balance
    if stats['total_classes'] > 0:
        avg_images_per_class = stats['total_images'] / stats['total_classes']
        logger.info(f"Average images per class: {avg_images_per_class:.1f}")
    
    # Report statistics
    logger.info(f"Dataset statistics:")
    logger.info(f"  Total images: {stats['total_images']}")
    logger.info(f"  Total classes: {stats['total_classes']}")
    logger.info(f"  Images with text: {stats['images_with_text']}")
    logger.info(f"  Split counts: {stats['split_counts']}")
    
    # Report issues
    if issues:
        logger.warning("Dataset issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("Dataset validation passed!")
    
    return stats, issues


def main():
    """Main data preparation function"""
    parser = argparse.ArgumentParser(description="Prepare data for pill recognition training")
    
    parser.add_argument('--data-root', type=str, required=True,
                       help='Root directory containing data')
    
    # Action arguments
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--create-splits', action='store_true',
                             help='Create train/val/test splits from class directories')
    action_group.add_argument('--extract-text', action='store_true',
                             help='Extract text from images using OCR')
    action_group.add_argument('--create-annotations', action='store_true',
                             help='Create annotation files for all splits')
    action_group.add_argument('--validate', action='store_true',
                             help='Validate dataset structure')
    
    # Split creation options
    parser.add_argument('--train-ratio', type=float, default=0.7,
                       help='Fraction of data for training')
    parser.add_argument('--val-ratio', type=float, default=0.15,
                       help='Fraction of data for validation')
    parser.add_argument('--test-ratio', type=float, default=0.15,
                       help='Fraction of data for testing')
    parser.add_argument('--random-seed', type=int, default=42,
                       help='Random seed for reproducible splits')
    
    # OCR options
    parser.add_argument('--output-format', type=str, default='individual',
                       choices=['individual', 'json', 'both'],
                       help='Output format for extracted text')
    
    args = parser.parse_args()
    
    # Setup logging
    os.makedirs('logs', exist_ok=True)
    setup_logging()
    
    # Check data root
    if not os.path.exists(args.data_root):
        logger.error(f"Data root directory not found: {args.data_root}")
        return 1
    
    try:
        if args.create_splits:
            logger.info("Creating train/val/test splits...")
            create_train_val_test_splits(
                data_root=args.data_root,
                train_ratio=args.train_ratio,
                val_ratio=args.val_ratio,
                test_ratio=args.test_ratio,
                random_seed=args.random_seed
            )
        
        elif args.extract_text:
            logger.info("Extracting text from images...")
            extract_text_from_images(
                data_root=args.data_root,
                output_format=args.output_format
            )
        
        elif args.create_annotations:
            logger.info("Creating annotation files...")
            for split in ['train', 'val', 'test']:
                create_annotations_file(args.data_root, split)
        
        elif args.validate:
            logger.info("Validating dataset...")
            validate_dataset(args.data_root)
    
    except Exception as e:
        logger.error(f"Data preparation failed: {e}")
        return 1
    
    logger.info("Data preparation completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())