"""
Inference and prediction module for pill recognition
"""
import os
import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from PIL import Image
import cv2
from pathlib import Path
import logging

from .models import MultimodalPillTransformer
from .data import create_transforms
from .ocr import OCRExtractor
from .config import PillRecognitionConfig

logger = logging.getLogger(__name__)


class PillPredictor:
    """
    Inference class for pill recognition predictions
    """
    
    def __init__(self, model_path: str = None, config: PillRecognitionConfig = None, device: str = None):
        """
        Initialize pill predictor
        
        Args:
            model_path: Path to trained model checkpoint
            config: Configuration object
            device: Device to run inference on
        """
        self.config = config if config is not None else PillRecognitionConfig()
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize model
        self.model = None
        self.label_mapping = {}
        
        # Initialize OCR extractor
        self.ocr_extractor = OCRExtractor(self.config.ocr)
        
        # Initialize transforms
        self.transform = create_transforms(self.config.model, split="val")
        
        # Initialize tokenizer
        from transformers import AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model.text_model_name)
        
        # Load model if path provided
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            logger.warning("No model path provided or model not found. Model needs to be loaded before prediction.")
    
    def load_model(self, model_path: str):
        """
        Load trained model from checkpoint
        
        Args:
            model_path: Path to model checkpoint
        """
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            
            # Update config if saved in checkpoint
            if 'config' in checkpoint:
                saved_config = checkpoint['config']
                if 'model' in saved_config:
                    for key, value in saved_config['model'].items():
                        if hasattr(self.config.model, key):
                            setattr(self.config.model, key, value)
            
            # Initialize model
            self.model = MultimodalPillTransformer(self.config.model)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            # Load label mapping if available
            if 'label_mapping' in checkpoint:
                self.label_mapping = checkpoint['label_mapping']
            
            logger.info(f"Successfully loaded model from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            raise
    
    def preprocess_image(self, image: Union[str, np.ndarray, Image.Image]) -> torch.Tensor:
        """
        Preprocess image for model input
        
        Args:
            image: Input image (path, numpy array, or PIL Image)
            
        Returns:
            Preprocessed image tensor
        """
        # Load image if path provided
        if isinstance(image, str):
            image = cv2.imread(image)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif isinstance(image, Image.Image):
            image = np.array(image)
        
        # Apply transforms
        transformed = self.transform(image=image)
        image_tensor = transformed['image'].unsqueeze(0)  # Add batch dimension
        
        return image_tensor
    
    def preprocess_text(self, text: str) -> Dict[str, torch.Tensor]:
        """
        Preprocess text for model input
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with tokenized text tensors
        """
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.config.model.text_max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'],
            'attention_mask': encoding['attention_mask']
        }
    
    def extract_text_from_image(self, image: Union[str, np.ndarray, Image.Image]) -> str:
        """
        Extract text from pill image using OCR
        
        Args:
            image: Input image
            
        Returns:
            Extracted text string
        """
        try:
            ocr_result = self.ocr_extractor.extract_text(image)
            return ocr_result.get('text', '')
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return ""
    
    def predict_single(self, 
                      image: Union[str, np.ndarray, Image.Image],
                      text: Optional[str] = None,
                      extract_text: bool = True) -> Dict[str, any]:
        """
        Make prediction on a single pill image
        
        Args:
            image: Input pill image
            text: Optional text input (if None and extract_text=True, will use OCR)
            extract_text: Whether to extract text using OCR if text not provided
            
        Returns:
            Dictionary with prediction results
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        try:
            # Preprocess image
            image_tensor = self.preprocess_image(image).to(self.device)
            
            # Get text
            if text is None and extract_text:
                text = self.extract_text_from_image(image)
            elif text is None:
                text = ""
            
            # Preprocess text
            text_inputs = self.preprocess_text(text)
            input_ids = text_inputs['input_ids'].to(self.device)
            attention_mask = text_inputs['attention_mask'].to(self.device)
            
            # Make prediction
            with torch.no_grad():
                outputs = self.model(image_tensor, input_ids, attention_mask)
                logits = outputs['logits']
                probabilities = F.softmax(logits, dim=1)
                
                # Get top predictions
                top_probs, top_indices = torch.topk(probabilities, k=min(5, logits.size(1)), dim=1)
                
                top_probs = top_probs.cpu().numpy()[0]
                top_indices = top_indices.cpu().numpy()[0]
            
            # Format results
            predictions = []
            for i, (prob, idx) in enumerate(zip(top_probs, top_indices)):
                label = self.label_mapping.get(idx, f"Class_{idx}")
                predictions.append({
                    'rank': i + 1,
                    'class_id': int(idx),
                    'class_name': label,
                    'confidence': float(prob)
                })
            
            result = {
                'predictions': predictions,
                'extracted_text': text,
                'image_shape': image_tensor.shape[2:],  # (H, W)
                'status': 'success'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                'predictions': [],
                'extracted_text': text if 'text' in locals() else "",
                'error': str(e),
                'status': 'error'
            }
    
    def predict_batch(self, 
                     images: List[Union[str, np.ndarray, Image.Image]],
                     texts: Optional[List[str]] = None,
                     extract_text: bool = True,
                     batch_size: int = 8) -> List[Dict[str, any]]:
        """
        Make predictions on a batch of images
        
        Args:
            images: List of input images
            texts: Optional list of text inputs
            extract_text: Whether to extract text using OCR if texts not provided
            batch_size: Batch size for processing
            
        Returns:
            List of prediction results
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        results = []
        
        # Process in batches
        for i in range(0, len(images), batch_size):
            batch_images = images[i:i + batch_size]
            batch_texts = texts[i:i + batch_size] if texts else [None] * len(batch_images)
            
            batch_results = []
            
            for image, text in zip(batch_images, batch_texts):
                result = self.predict_single(image, text, extract_text)
                batch_results.append(result)
            
            results.extend(batch_results)
        
        return results
    
    def predict_from_directory(self, 
                              image_dir: str,
                              output_file: Optional[str] = None,
                              extract_text: bool = True) -> List[Dict[str, any]]:
        """
        Make predictions on all images in a directory
        
        Args:
            image_dir: Directory containing images
            output_file: Optional file to save results
            extract_text: Whether to extract text using OCR
            
        Returns:
            List of prediction results
        """
        image_dir = Path(image_dir)
        if not image_dir.exists():
            raise ValueError(f"Directory not found: {image_dir}")
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = [f for f in image_dir.iterdir() 
                      if f.suffix.lower() in image_extensions]
        
        if not image_files:
            logger.warning(f"No image files found in {image_dir}")
            return []
        
        logger.info(f"Found {len(image_files)} images in {image_dir}")
        
        # Make predictions
        results = []
        for image_file in image_files:
            try:
                result = self.predict_single(str(image_file), extract_text=extract_text)
                result['image_path'] = str(image_file)
                result['image_name'] = image_file.name
                results.append(result)
                
                if len(results) % 10 == 0:
                    logger.info(f"Processed {len(results)}/{len(image_files)} images")
                    
            except Exception as e:
                logger.error(f"Failed to process {image_file}: {e}")
                results.append({
                    'image_path': str(image_file),
                    'image_name': image_file.name,
                    'predictions': [],
                    'extracted_text': "",
                    'error': str(e),
                    'status': 'error'
                })
        
        # Save results if output file specified
        if output_file:
            self.save_results(results, output_file)
        
        return results
    
    def save_results(self, results: List[Dict[str, any]], output_file: str):
        """
        Save prediction results to file
        
        Args:
            results: List of prediction results
            output_file: Output file path
        """
        import json
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable format
        json_results = []
        for result in results:
            json_result = {
                'image_path': result.get('image_path', ''),
                'image_name': result.get('image_name', ''),
                'extracted_text': result.get('extracted_text', ''),
                'predictions': result.get('predictions', []),
                'status': result.get('status', 'unknown')
            }
            
            if 'error' in result:
                json_result['error'] = result['error']
            
            json_results.append(json_result)
        
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
    
    def evaluate_on_dataset(self, 
                           data_root: str,
                           split: str = "test",
                           save_results: bool = True) -> Dict[str, float]:
        """
        Evaluate model on a dataset
        
        Args:
            data_root: Root directory containing data
            split: Dataset split to evaluate on
            save_results: Whether to save detailed results
            
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        from .data import PillDataset
        
        # Create dataset
        dataset = PillDataset(
            data_root=data_root,
            split=split,
            config=self.config.data,
            transform=self.transform,
            tokenizer=self.tokenizer
        )
        
        if len(dataset) == 0:
            logger.warning(f"No samples found in {split} split")
            return {}
        
        # Make predictions
        all_predictions = []
        all_labels = []
        all_confidences = []
        
        logger.info(f"Evaluating on {len(dataset)} samples...")
        
        for i in range(len(dataset)):
            try:
                sample = dataset[i]
                
                # Prepare inputs
                image = sample['image'].unsqueeze(0).to(self.device)
                input_ids = sample['input_ids'].unsqueeze(0).to(self.device)
                attention_mask = sample['attention_mask'].unsqueeze(0).to(self.device)
                true_label = sample['label'].item()
                
                # Make prediction
                with torch.no_grad():
                    outputs = self.model(image, input_ids, attention_mask)
                    probabilities = F.softmax(outputs['logits'], dim=1)
                    pred_label = torch.argmax(probabilities, dim=1).item()
                    confidence = probabilities[0, pred_label].item()
                
                all_predictions.append(pred_label)
                all_labels.append(true_label)
                all_confidences.append(confidence)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Evaluated {i + 1}/{len(dataset)} samples")
                    
            except Exception as e:
                logger.error(f"Failed to evaluate sample {i}: {e}")
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
        
        accuracy = accuracy_score(all_labels, all_predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            all_labels, all_predictions, average='weighted', zero_division=0
        )
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'num_samples': len(all_labels),
            'avg_confidence': np.mean(all_confidences)
        }
        
        logger.info(f"Evaluation results: {metrics}")
        
        # Save detailed results if requested
        if save_results:
            detailed_results = {
                'metrics': metrics,
                'predictions': all_predictions,
                'labels': all_labels,
                'confidences': all_confidences,
                'classification_report': classification_report(
                    all_labels, all_predictions, target_names=list(dataset.idx_to_label.values())
                )
            }
            
            results_file = f"evaluation_results_{split}.json"
            with open(results_file, 'w') as f:
                import json
                json.dump(detailed_results, f, indent=2, default=str)
            
            logger.info(f"Detailed results saved to {results_file}")
        
        return metrics