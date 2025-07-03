"""
Tests for OCR extraction module
"""
import pytest
import numpy as np
import cv2
from PIL import Image
import tempfile
from pathlib import Path

from pill_recognition.ocr import OCRExtractor
from pill_recognition.config import OCRConfig


class TestOCRExtractor:
    """Test OCRExtractor class"""
    
    def test_initialization_default(self):
        """Test OCR extractor initialization with default config"""
        extractor = OCRExtractor()
        
        # Should have config attribute
        assert hasattr(extractor, 'config')
        assert hasattr(extractor, 'tesseract_available')
        assert hasattr(extractor, 'paddle_available')
    
    def test_initialization_with_config(self):
        """Test OCR extractor initialization with custom config"""
        config = OCRConfig()
        config.min_confidence = 0.8
        config.clean_text = True
        
        extractor = OCRExtractor(config)
        
        assert extractor.config == config
        assert extractor.config.min_confidence == 0.8
        assert extractor.config.clean_text == True
    
    def test_preprocess_image_numpy(self):
        """Test image preprocessing with numpy array input"""
        extractor = OCRExtractor()
        
        # Create test image
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        processed = extractor.preprocess_image(image)
        
        assert isinstance(processed, np.ndarray)
        assert len(processed.shape) == 2  # Should be grayscale
        assert processed.dtype == np.uint8
    
    def test_preprocess_image_pil(self):
        """Test image preprocessing with PIL Image input"""
        extractor = OCRExtractor()
        
        # Create test image
        image_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        image = Image.fromarray(image_array)
        
        processed = extractor.preprocess_image(image)
        
        assert isinstance(processed, np.ndarray)
        assert len(processed.shape) == 2  # Should be grayscale
    
    def test_preprocess_image_file_path(self):
        """Test image preprocessing with file path input"""
        extractor = OCRExtractor()
        
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            image_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            image = Image.fromarray(image_array)
            image.save(f.name)
            temp_file = f.name
        
        try:
            processed = extractor.preprocess_image(temp_file)
            
            assert isinstance(processed, np.ndarray)
            assert len(processed.shape) == 2  # Should be grayscale
            
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        extractor = OCRExtractor()
        
        # Test cases for text cleaning
        test_cases = [
            ("", ""),
            ("  extra   spaces  ", "extra spaces"),
            ("PILL123", "PILL123"),
            ("P!LL@123#", "PLL123"),
            ("0ne Tw0", "One TwO"),  # 0 -> O conversion
            ("l1l", "111"),  # l -> 1 conversion
            ("I1I", "111"),  # I -> 1 conversion
        ]
        
        for input_text, expected in test_cases:
            cleaned = extractor.clean_text(input_text)
            assert cleaned == expected, f"Failed for input: '{input_text}'"
    
    @pytest.mark.skip(reason="Requires Tesseract installation")
    def test_extract_with_tesseract(self):
        """Test text extraction with Tesseract OCR"""
        extractor = OCRExtractor()
        
        if not extractor.tesseract_available:
            pytest.skip("Tesseract not available")
        
        # Create simple text image
        image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        processed = extractor.preprocess_image(image)
        
        result = extractor.extract_with_tesseract(processed)
        
        assert isinstance(result, dict)
        assert 'text' in result
        assert 'confidence' in result
        assert 'words' in result
        assert 'engine' in result
        assert result['engine'] == 'tesseract'
    
    @pytest.mark.skip(reason="Requires PaddleOCR installation")
    def test_extract_with_paddle(self):
        """Test text extraction with PaddleOCR"""
        extractor = OCRExtractor()
        
        if not extractor.paddle_available:
            pytest.skip("PaddleOCR not available")
        
        # Create simple text image
        image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        processed = extractor.preprocess_image(image)
        
        result = extractor.extract_with_paddle(processed)
        
        assert isinstance(result, dict)
        assert 'text' in result
        assert 'confidence' in result
        assert 'words' in result
        assert 'engine' in result
        assert result['engine'] == 'paddle'
    
    def test_extract_text_no_engines(self):
        """Test text extraction when no OCR engines are available"""
        extractor = OCRExtractor()
        
        # Force disable both engines
        extractor.tesseract_available = False
        extractor.paddle_available = False
        
        # Create test image
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        
        result = extractor.extract_text(image)
        
        assert isinstance(result, dict)
        assert result['text'] == ""
        assert result['confidence'] == 0.0
        assert result['engine'] == 'none'
    
    def test_extract_multiple_images(self):
        """Test extraction from multiple images"""
        extractor = OCRExtractor()
        
        # Create temporary image files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                image_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
                image = Image.fromarray(image_array)
                image.save(f.name)
                temp_files.append(f.name)
        
        try:
            results = extractor.extract_multiple_images(temp_files)
            
            assert len(results) == 3
            
            for i, result in enumerate(results):
                assert isinstance(result, dict)
                assert 'text' in result
                assert 'confidence' in result
                assert 'image_path' in result
                assert result['image_path'] == temp_files[i]
        
        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink(missing_ok=True)
    
    def test_extract_multiple_images_with_errors(self):
        """Test extraction from multiple images with some errors"""
        extractor = OCRExtractor()
        
        # Mix of valid and invalid file paths
        image_paths = [
            "nonexistent_file1.jpg",
            "nonexistent_file2.jpg"
        ]
        
        results = extractor.extract_multiple_images(image_paths)
        
        assert len(results) == 2
        
        for result in results:
            assert result['engine'] == 'error'
            assert 'error' in result
            assert result['text'] == ""
            assert result['confidence'] == 0.0


class TestOCRConfig:
    """Test OCRConfig class"""
    
    def test_default_config(self):
        """Test default OCR configuration"""
        config = OCRConfig()
        
        assert config.tesseract_cmd is None
        assert config.tesseract_config == "--oem 3 --psm 6"
        assert config.paddle_use_angle_cls == True
        assert config.paddle_lang == "en"
        assert config.paddle_use_gpu == True
        assert config.paddle_show_log == False
        assert config.min_text_length == 1
        assert config.max_text_length == 128
        assert config.clean_text == True
        assert config.min_confidence == 0.5
        assert config.paddle_confidence_threshold == 0.5
    
    def test_custom_config(self):
        """Test custom OCR configuration"""
        config = OCRConfig(
            tesseract_cmd="/usr/bin/tesseract",
            tesseract_config="--oem 1 --psm 8",
            paddle_lang="ch_sim",
            min_confidence=0.8,
            clean_text=False
        )
        
        assert config.tesseract_cmd == "/usr/bin/tesseract"
        assert config.tesseract_config == "--oem 1 --psm 8"
        assert config.paddle_lang == "ch_sim"
        assert config.min_confidence == 0.8
        assert config.clean_text == False