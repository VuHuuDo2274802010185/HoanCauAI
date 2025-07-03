"""
Pill recognition integration module for existing MCP server
"""
import os
import io
import tempfile
import logging
from typing import Dict, List, Optional
from pathlib import Path
from fastapi import HTTPException
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class PillRecognitionIntegration:
    """
    Integration class for pill recognition system with existing MCP server
    """
    
    def __init__(self):
        self.predictor = None
        self._initialize_pill_recognition()
    
    def _initialize_pill_recognition(self):
        """Initialize pill recognition system if available"""
        try:
            from pill_recognition import PillPredictor, PillRecognitionConfig
            
            # Look for model checkpoint
            model_paths = [
                "models/pill_recognition.pth",
                "checkpoints/best_model.pth",
                "pill_recognition_model.pth"
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path:
                config = PillRecognitionConfig()
                self.predictor = PillPredictor(model_path=model_path, config=config)
                logger.info(f"Pill recognition system initialized with model: {model_path}")
            else:
                logger.warning("No pill recognition model found. Pill recognition features disabled.")
                
        except ImportError as e:
            logger.warning(f"Pill recognition modules not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize pill recognition: {e}")
    
    def is_available(self) -> bool:
        """Check if pill recognition is available"""
        return self.predictor is not None
    
    def predict_pill(self, image_data: bytes, text: Optional[str] = None) -> Dict:
        """
        Predict pill from image data
        
        Args:
            image_data: Image bytes
            text: Optional text input (if None, OCR will be used)
            
        Returns:
            Dictionary with prediction results
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Pill recognition system not available"
            )
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Make prediction
            result = self.predictor.predict_single(
                image=image,
                text=text,
                extract_text=(text is None)
            )
            
            return {
                "status": "success",
                "predictions": result.get("predictions", []),
                "extracted_text": result.get("extracted_text", ""),
                "confidence": result.get("predictions", [{}])[0].get("confidence", 0.0) if result.get("predictions") else 0.0
            }
            
        except Exception as e:
            logger.error(f"Pill prediction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "predictions": [],
                "extracted_text": "",
                "confidence": 0.0
            }
    
    def predict_pill_batch(self, image_files: List[bytes], texts: Optional[List[str]] = None) -> List[Dict]:
        """
        Predict pills from multiple images
        
        Args:
            image_files: List of image bytes
            texts: Optional list of text inputs
            
        Returns:
            List of prediction results
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Pill recognition system not available"
            )
        
        results = []
        
        for i, image_data in enumerate(image_files):
            text = texts[i] if texts and i < len(texts) else None
            result = self.predict_pill(image_data, text)
            result["image_index"] = i
            results.append(result)
        
        return results
    
    def extract_text_from_pill(self, image_data: bytes) -> Dict:
        """
        Extract text from pill image using OCR
        
        Args:
            image_data: Image bytes
            
        Returns:
            Dictionary with OCR results
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Pill recognition system not available"
            )
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Extract text using OCR
            ocr_result = self.predictor.extract_text_from_image(image)
            
            return {
                "status": "success",
                "text": ocr_result,
                "confidence": 1.0  # OCR confidence would need to be extracted separately
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "text": "",
                "confidence": 0.0
            }


# Global instance
pill_recognition = PillRecognitionIntegration()