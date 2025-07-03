#!/usr/bin/env python3
"""
Inference script for multimodal pill recognition
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# Add src directory to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pill_recognition.inference import PillPredictor
from pill_recognition.config import PillRecognitionConfig

logger = logging.getLogger(__name__)


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/inference.log')
        ]
    )


def main():
    """Main inference function"""
    parser = argparse.ArgumentParser(description="Run inference with multimodal pill recognition model")
    
    # Model arguments
    parser.add_argument('--model-path', type=str, required=True,
                       help='Path to trained model checkpoint')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to configuration file')
    
    # Input arguments (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--image', type=str,
                           help='Single image to process')
    input_group.add_argument('--image-dir', type=str,
                           help='Directory containing images to process')
    input_group.add_argument('--dataset', type=str,
                           help='Dataset directory for evaluation')
    
    # Processing options
    parser.add_argument('--text', type=str, default=None,
                       help='Text to use instead of OCR extraction')
    parser.add_argument('--no-ocr', action='store_true',
                       help='Disable OCR text extraction')
    parser.add_argument('--batch-size', type=int, default=8,
                       help='Batch size for processing multiple images')
    
    # Output arguments
    parser.add_argument('--output', type=str, default=None,
                       help='Output file to save results')
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of top predictions to show')
    
    # Dataset evaluation options
    parser.add_argument('--split', type=str, default='test',
                       choices=['train', 'val', 'test'],
                       help='Dataset split to evaluate (when using --dataset)')
    
    args = parser.parse_args()
    
    # Setup logging
    os.makedirs('logs', exist_ok=True)
    setup_logging()
    
    # Load configuration
    config = PillRecognitionConfig(args.config)
    
    # Check model path
    if not os.path.exists(args.model_path):
        logger.error(f"Model not found: {args.model_path}")
        return 1
    
    # Initialize predictor
    logger.info("Loading model...")
    predictor = PillPredictor(
        model_path=args.model_path,
        config=config
    )
    
    try:
        if args.image:
            # Single image prediction
            logger.info(f"Processing single image: {args.image}")
            
            if not os.path.exists(args.image):
                logger.error(f"Image not found: {args.image}")
                return 1
            
            result = predictor.predict_single(
                image=args.image,
                text=args.text,
                extract_text=not args.no_ocr
            )
            
            # Print results
            print(f"\nResults for {args.image}:")
            print(f"Extracted text: '{result.get('extracted_text', '')}'")
            print(f"Status: {result.get('status', 'unknown')}")
            
            if result.get('status') == 'error':
                print(f"Error: {result.get('error', 'Unknown error')}")
            else:
                print("\nTop predictions:")
                for pred in result.get('predictions', [])[:args.top_k]:
                    print(f"  {pred['rank']}. {pred['class_name']} ({pred['confidence']:.4f})")
            
            # Save results if output specified
            if args.output:
                predictor.save_results([result], args.output)
                logger.info(f"Results saved to {args.output}")
        
        elif args.image_dir:
            # Directory of images
            logger.info(f"Processing images in directory: {args.image_dir}")
            
            if not os.path.exists(args.image_dir):
                logger.error(f"Directory not found: {args.image_dir}")
                return 1
            
            results = predictor.predict_from_directory(
                image_dir=args.image_dir,
                output_file=args.output,
                extract_text=not args.no_ocr
            )
            
            # Print summary
            total_images = len(results)
            successful = sum(1 for r in results if r.get('status') == 'success')
            failed = total_images - successful
            
            print(f"\nProcessed {total_images} images:")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            
            # Show some examples
            print(f"\nSample results (top {min(5, len(results))}):")
            for i, result in enumerate(results[:5]):
                status = result.get('status', 'unknown')
                image_name = result.get('image_name', 'unknown')
                
                if status == 'success':
                    top_pred = result.get('predictions', [{}])[0]
                    class_name = top_pred.get('class_name', 'unknown')
                    confidence = top_pred.get('confidence', 0.0)
                    print(f"  {i+1}. {image_name}: {class_name} ({confidence:.4f})")
                else:
                    error = result.get('error', 'unknown error')
                    print(f"  {i+1}. {image_name}: ERROR - {error}")
        
        elif args.dataset:
            # Dataset evaluation
            logger.info(f"Evaluating on dataset: {args.dataset} ({args.split} split)")
            
            if not os.path.exists(args.dataset):
                logger.error(f"Dataset directory not found: {args.dataset}")
                return 1
            
            metrics = predictor.evaluate_on_dataset(
                data_root=args.dataset,
                split=args.split,
                save_results=True
            )
            
            # Print evaluation results
            print(f"\nEvaluation Results on {args.split} split:")
            print(f"  Accuracy: {metrics.get('accuracy', 0.0):.4f}")
            print(f"  Precision: {metrics.get('precision', 0.0):.4f}")
            print(f"  Recall: {metrics.get('recall', 0.0):.4f}")
            print(f"  F1-Score: {metrics.get('f1', 0.0):.4f}")
            print(f"  Number of samples: {metrics.get('num_samples', 0)}")
            print(f"  Average confidence: {metrics.get('avg_confidence', 0.0):.4f}")
            
            logger.info("Detailed evaluation results saved to evaluation_results_*.json")
    
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        return 1
    
    logger.info("Inference completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())