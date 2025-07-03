"""
OCR extraction module supporting both Tesseract and PaddleOCR
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class OCRExtractor:
    """
    OCR extractor that supports both Tesseract and PaddleOCR for text extraction
    from pill images.
    """
    
    def __init__(self, config=None):
        """
        Initialize OCR extractor with configuration
        
        Args:
            config: OCRConfig object with OCR settings
        """
        self.config = config
        self.tesseract_available = False
        self.paddle_available = False
        
        # Initialize OCR engines
        self._init_tesseract()
        self._init_paddle_ocr()
        
        if not (self.tesseract_available or self.paddle_available):
            logger.warning("No OCR engines available. Install pytesseract or paddleocr.")
    
    def _init_tesseract(self):
        """Initialize Tesseract OCR"""
        try:
            import pytesseract
            
            # Set tesseract command path if provided
            if self.config and self.config.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd
            
            # Test tesseract availability
            test_image = np.ones((50, 50, 3), dtype=np.uint8) * 255
            pytesseract.image_to_string(test_image)
            
            self.tesseract_available = True
            self.pytesseract = pytesseract
            logger.info("Tesseract OCR initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Tesseract: {e}")
            self.tesseract_available = False
    
    def _init_paddle_ocr(self):
        """Initialize PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            
            # Configure PaddleOCR
            ocr_kwargs = {
                'use_angle_cls': True,
                'lang': 'en',
                'use_gpu': True,
                'show_log': False
            }
            
            if self.config:
                ocr_kwargs.update({
                    'use_angle_cls': self.config.paddle_use_angle_cls,
                    'lang': self.config.paddle_lang,
                    'use_gpu': self.config.paddle_use_gpu,
                    'show_log': self.config.paddle_show_log
                })
            
            self.paddle_ocr = PaddleOCR(**ocr_kwargs)
            self.paddle_available = True
            logger.info("PaddleOCR initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize PaddleOCR: {e}")
            self.paddle_available = False
    
    def preprocess_image(self, image: Union[np.ndarray, Image.Image, str]) -> np.ndarray:
        """
        Preprocess image for better OCR results
        
        Args:
            image: Input image (numpy array, PIL Image, or file path)
            
        Returns:
            Preprocessed image as numpy array
        """
        # Load image if path provided
        if isinstance(image, str):
            image = cv2.imread(image)
        elif isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply image enhancement techniques
        # 1. Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 2. Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # 3. Morphological operations to clean up text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
        
        # 4. Thresholding for better text extraction
        _, thresh = cv2.threshold(cleaned, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def extract_with_tesseract(self, image: np.ndarray) -> Dict[str, any]:
        """
        Extract text using Tesseract OCR
        
        Args:
            image: Preprocessed image array
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.tesseract_available:
            return {"text": "", "confidence": 0.0, "words": []}
        
        try:
            # Configure tesseract
            config = "--oem 3 --psm 6"
            if self.config and hasattr(self.config, 'tesseract_config'):
                config = self.config.tesseract_config
            
            # Extract text with confidence
            data = self.pytesseract.image_to_data(image, config=config, output_type=self.pytesseract.Output.DICT)
            
            # Filter out low confidence detections
            min_conf = 50
            if self.config and hasattr(self.config, 'min_confidence'):
                min_conf = self.config.min_confidence * 100
            
            words = []
            confidences = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > min_conf:
                    text = data['text'][i].strip()
                    if text:
                        words.append({
                            'text': text,
                            'confidence': float(data['conf'][i]) / 100.0,
                            'bbox': [data['left'][i], data['top'][i], 
                                   data['width'][i], data['height'][i]]
                        })
                        confidences.append(float(data['conf'][i]) / 100.0)
            
            # Combine all text
            full_text = ' '.join([w['text'] for w in words])
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "words": words,
                "engine": "tesseract"
            }
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return {"text": "", "confidence": 0.0, "words": []}
    
    def extract_with_paddle(self, image: np.ndarray) -> Dict[str, any]:
        """
        Extract text using PaddleOCR
        
        Args:
            image: Preprocessed image array
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.paddle_available:
            return {"text": "", "confidence": 0.0, "words": []}
        
        try:
            # Run PaddleOCR
            results = self.paddle_ocr.ocr(image, cls=True)
            
            if not results or not results[0]:
                return {"text": "", "confidence": 0.0, "words": []}
            
            # Parse results
            words = []
            confidences = []
            
            min_conf = 0.5
            if self.config and hasattr(self.config, 'paddle_confidence_threshold'):
                min_conf = self.config.paddle_confidence_threshold
            
            for line in results[0]:
                if line:
                    bbox, (text, confidence) = line
                    if confidence > min_conf:
                        words.append({
                            'text': text,
                            'confidence': confidence,
                            'bbox': bbox
                        })
                        confidences.append(confidence)
            
            # Combine all text
            full_text = ' '.join([w['text'] for w in words])
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "words": words,
                "engine": "paddle"
            }
            
        except Exception as e:
            logger.error(f"PaddleOCR failed: {e}")
            return {"text": "", "confidence": 0.0, "words": []}
    
    def clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing unwanted characters and formatting
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove non-alphanumeric characters except common pill markings
        text = re.sub(r'[^\w\s\-\.\+\/]', '', text)
        
        # Handle common OCR mistakes for pill text
        replacements = {
            '0': 'O',  # Zero to letter O
            'l': '1',  # lowercase L to number 1
            'I': '1',  # uppercase I to number 1
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    def extract_text(self, image: Union[np.ndarray, Image.Image, str]) -> Dict[str, any]:
        """
        Extract text from image using both OCR engines and return best result
        
        Args:
            image: Input image (numpy array, PIL Image, or file path)
            
        Returns:
            Dictionary with extracted text and metadata
        """
        # Preprocess image
        processed_image = self.preprocess_image(image)
        
        results = []
        
        # Try Tesseract
        if self.tesseract_available:
            tesseract_result = self.extract_with_tesseract(processed_image)
            if tesseract_result['text']:
                results.append(tesseract_result)
        
        # Try PaddleOCR
        if self.paddle_available:
            paddle_result = self.extract_with_paddle(processed_image)
            if paddle_result['text']:
                results.append(paddle_result)
        
        if not results:
            return {"text": "", "confidence": 0.0, "words": [], "engine": "none"}
        
        # Return result with highest confidence
        best_result = max(results, key=lambda x: x['confidence'])
        
        # Clean text if enabled
        if self.config and getattr(self.config, 'clean_text', True):
            best_result['text'] = self.clean_text(best_result['text'])
        
        return best_result
    
    def extract_multiple_images(self, image_paths: List[str]) -> List[Dict[str, any]]:
        """
        Extract text from multiple images
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of OCR results for each image
        """
        results = []
        for image_path in image_paths:
            try:
                result = self.extract_text(image_path)
                result['image_path'] = image_path
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                results.append({
                    "text": "",
                    "confidence": 0.0,
                    "words": [],
                    "engine": "error",
                    "image_path": image_path,
                    "error": str(e)
                })
        
        return results