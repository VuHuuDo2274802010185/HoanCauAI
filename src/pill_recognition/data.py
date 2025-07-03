"""
Dataset and data loading utilities for pill recognition
"""
import os
import json
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader, DistributedSampler
from PIL import Image
import albumentations as A
from albumentations.pytorch import ToTensorV2
from transformers import AutoTokenizer
import logging

logger = logging.getLogger(__name__)


class PillDataset(Dataset):
    """
    Dataset class for pill recognition with images and text imprints
    """
    
    def __init__(self, 
                 data_root: str,
                 split: str = "train",
                 config=None,
                 transform=None,
                 tokenizer=None):
        """
        Initialize pill dataset
        
        Args:
            data_root: Root directory containing pill data
            split: Data split ('train', 'val', 'test')
            config: Configuration object
            transform: Image transformations
            tokenizer: Text tokenizer
        """
        self.data_root = Path(data_root)
        self.split = split
        self.config = config
        self.transform = transform
        self.tokenizer = tokenizer
        
        # Load data
        self.samples = self._load_samples()
        
        # Create label mapping
        self.label_to_idx, self.idx_to_label = self._create_label_mapping()
        
        logger.info(f"Loaded {len(self.samples)} samples for {split} split")
        logger.info(f"Found {len(self.label_to_idx)} unique pill classes")
    
    def _load_samples(self) -> List[Dict]:
        """Load dataset samples from directory structure or annotation file"""
        samples = []
        
        # Look for annotation file first
        annotation_file = self.data_root / f"{self.split}_annotations.json"
        if annotation_file.exists():
            samples = self._load_from_annotations(annotation_file)
        else:
            # Fall back to directory structure
            samples = self._load_from_directory()
        
        return samples
    
    def _load_from_annotations(self, annotation_file: Path) -> List[Dict]:
        """Load samples from JSON annotation file"""
        with open(annotation_file, 'r') as f:
            annotations = json.load(f)
        
        samples = []
        for ann in annotations:
            sample = {
                'image_path': self.data_root / ann['image_path'],
                'text': ann.get('text', ''),
                'label': ann['label'],
                'pill_id': ann.get('pill_id', ''),
                'metadata': ann.get('metadata', {})
            }
            
            # Check if image exists
            if sample['image_path'].exists():
                samples.append(sample)
            else:
                logger.warning(f"Image not found: {sample['image_path']}")
        
        return samples
    
    def _load_from_directory(self) -> List[Dict]:
        """Load samples from directory structure: data_root/split/class/images"""
        samples = []
        split_dir = self.data_root / self.split
        
        if not split_dir.exists():
            logger.error(f"Split directory not found: {split_dir}")
            return samples
        
        # Iterate through class directories
        for class_dir in split_dir.iterdir():
            if not class_dir.is_dir():
                continue
            
            class_name = class_dir.name
            
            # Find all images in class directory
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            image_files = [f for f in class_dir.iterdir() 
                          if f.suffix.lower() in image_extensions]
            
            for image_file in image_files:
                # Look for corresponding text file
                text_file = image_file.with_suffix('.txt')
                text = ""
                if text_file.exists():
                    try:
                        with open(text_file, 'r') as f:
                            text = f.read().strip()
                    except Exception as e:
                        logger.warning(f"Failed to read text file {text_file}: {e}")
                
                sample = {
                    'image_path': image_file,
                    'text': text,
                    'label': class_name,
                    'pill_id': image_file.stem,
                    'metadata': {}
                }
                samples.append(sample)
        
        return samples
    
    def _create_label_mapping(self) -> Tuple[Dict[str, int], Dict[int, str]]:
        """Create mapping between labels and indices"""
        unique_labels = sorted(set(sample['label'] for sample in self.samples))
        label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
        idx_to_label = {idx: label for label, idx in label_to_idx.items()}
        return label_to_idx, idx_to_label
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict[str, Union[torch.Tensor, str, int]]:
        """Get a single sample"""
        sample = self.samples[idx]
        
        # Load and process image
        image = self._load_image(sample['image_path'])
        if self.transform:
            image = self.transform(image=image)['image']
        
        # Process text
        text = sample['text']
        if self.tokenizer:
            text_encoding = self._tokenize_text(text)
        else:
            text_encoding = {'input_ids': torch.tensor([]), 'attention_mask': torch.tensor([])}
        
        # Get label index
        label_idx = self.label_to_idx[sample['label']]
        
        return {
            'image': image,
            'input_ids': text_encoding['input_ids'],
            'attention_mask': text_encoding['attention_mask'],
            'label': torch.tensor(label_idx, dtype=torch.long),
            'text': text,
            'pill_id': sample['pill_id'],
            'image_path': str(sample['image_path'])
        }
    
    def _load_image(self, image_path: Path) -> np.ndarray:
        """Load and preprocess image"""
        try:
            # Load image using OpenCV
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Basic preprocessing
            if self.config:
                min_size = getattr(self.config, 'min_image_size', 64)
                max_size = getattr(self.config, 'max_image_size', 512)
                
                h, w = image.shape[:2]
                if min(h, w) < min_size:
                    # Resize if too small
                    scale = min_size / min(h, w)
                    new_h, new_w = int(h * scale), int(w * scale)
                    image = cv2.resize(image, (new_w, new_h))
                elif max(h, w) > max_size:
                    # Resize if too large
                    scale = max_size / max(h, w)
                    new_h, new_w = int(h * scale), int(w * scale)
                    image = cv2.resize(image, (new_w, new_h))
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            # Return a blank image as fallback
            if self.config:
                size = getattr(self.config, 'image_size', 224)
                return np.zeros((size, size, 3), dtype=np.uint8)
            return np.zeros((224, 224, 3), dtype=np.uint8)
    
    def _tokenize_text(self, text: str) -> Dict[str, torch.Tensor]:
        """Tokenize text using the tokenizer"""
        if not self.tokenizer:
            return {'input_ids': torch.tensor([]), 'attention_mask': torch.tensor([])}
        
        max_length = 128
        if self.config:
            max_length = getattr(self.config, 'text_max_length', 128)
        
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0)
        }


def create_transforms(config, split: str = "train") -> A.Compose:
    """
    Create image augmentation transforms
    
    Args:
        config: Configuration object
        split: Data split ('train', 'val', 'test')
        
    Returns:
        Albumentations transform pipeline
    """
    image_size = getattr(config, 'image_size', 224)
    
    if split == "train" and getattr(config, 'use_augmentation', True):
        # Training transforms with augmentation
        transform = A.Compose([
            A.Resize(image_size, image_size),
            A.RandomRotate90(p=0.5),
            A.Flip(p=0.5),
            A.RandomBrightnessContrast(
                brightness_limit=0.2,
                contrast_limit=0.2,
                p=0.5
            ),
            A.HueSaturationValue(
                hue_shift_limit=20,
                sat_shift_limit=30,
                val_shift_limit=20,
                p=0.5
            ),
            A.GaussianBlur(blur_limit=(3, 7), p=0.3),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            A.CoarseDropout(
                max_holes=8,
                max_height=8,
                max_width=8,
                min_holes=1,
                min_height=4,
                min_width=4,
                fill_value=0,
                p=0.3
            ),
            A.Normalize(
                mean=config.image_mean,
                std=config.image_std
            ),
            ToTensorV2()
        ])
    else:
        # Validation/test transforms without augmentation
        transform = A.Compose([
            A.Resize(image_size, image_size),
            A.Normalize(
                mean=config.image_mean,
                std=config.image_std
            ),
            ToTensorV2()
        ])
    
    return transform


class PillDataLoader:
    """
    Data loader factory for pill recognition dataset
    """
    
    def __init__(self, config):
        self.config = config
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(config.text_model_name)
    
    def create_dataloaders(self, data_root: str) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        Create train, validation, and test data loaders
        
        Args:
            data_root: Root directory containing data
            
        Returns:
            Tuple of (train_loader, val_loader, test_loader)
        """
        # Create transforms
        train_transform = create_transforms(self.config.model, "train")
        val_transform = create_transforms(self.config.model, "val")
        
        # Create datasets
        train_dataset = PillDataset(
            data_root=data_root,
            split=self.config.data.train_split,
            config=self.config.data,
            transform=train_transform,
            tokenizer=self.tokenizer
        )
        
        val_dataset = PillDataset(
            data_root=data_root,
            split=self.config.data.val_split,
            config=self.config.data,
            transform=val_transform,
            tokenizer=self.tokenizer
        )
        
        test_dataset = PillDataset(
            data_root=data_root,
            split=self.config.data.test_split,
            config=self.config.data,
            transform=val_transform,
            tokenizer=self.tokenizer
        )
        
        # Create samplers for distributed training
        train_sampler = None
        val_sampler = None
        test_sampler = None
        
        if self.config.training.use_ddp:
            train_sampler = DistributedSampler(train_dataset)
            val_sampler = DistributedSampler(val_dataset, shuffle=False)
            test_sampler = DistributedSampler(test_dataset, shuffle=False)
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.training.batch_size,
            shuffle=(train_sampler is None),
            sampler=train_sampler,
            num_workers=self.config.training.num_workers,
            pin_memory=self.config.training.pin_memory,
            drop_last=True
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.training.batch_size,
            shuffle=False,
            sampler=val_sampler,
            num_workers=self.config.training.num_workers,
            pin_memory=self.config.training.pin_memory,
            drop_last=False
        )
        
        test_loader = DataLoader(
            test_dataset,
            batch_size=self.config.training.batch_size,
            shuffle=False,
            sampler=test_sampler,
            num_workers=self.config.training.num_workers,
            pin_memory=self.config.training.pin_memory,
            drop_last=False
        )
        
        return train_loader, val_loader, test_loader
    
    def create_single_dataloader(self, data_root: str, split: str = "train") -> DataLoader:
        """
        Create a single data loader for specified split
        
        Args:
            data_root: Root directory containing data
            split: Data split to load
            
        Returns:
            DataLoader for the specified split
        """
        # Create transform based on split
        if split == "train":
            transform = create_transforms(self.config.model, "train")
            shuffle = True
        else:
            transform = create_transforms(self.config.model, "val")
            shuffle = False
        
        # Create dataset
        dataset = PillDataset(
            data_root=data_root,
            split=split,
            config=self.config.data,
            transform=transform,
            tokenizer=self.tokenizer
        )
        
        # Create sampler for distributed training
        sampler = None
        if self.config.training.use_ddp:
            sampler = DistributedSampler(dataset, shuffle=shuffle)
            shuffle = False  # Don't shuffle when using sampler
        
        # Create data loader
        loader = DataLoader(
            dataset,
            batch_size=self.config.training.batch_size,
            shuffle=shuffle,
            sampler=sampler,
            num_workers=self.config.training.num_workers,
            pin_memory=self.config.training.pin_memory,
            drop_last=(split == "train")
        )
        
        return loader