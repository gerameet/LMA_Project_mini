#!/usr/bin/env python3
"""
Comprehensive Dataset Testing Script
Tests all datasets configured in download_data.py by downloading samples and checking language detection.
"""

import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter

# External libraries
import datasets
from datasets import load_dataset
from tqdm import tqdm
import tiktoken
from transformers import AutoTokenizer
from huggingface_hub import whoami

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dataset_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LanguageDetector:
    """Enhanced language detection with detailed analysis."""
    
    def __init__(self):
        self.language_patterns = {
            'english': re.compile(r'^[a-zA-Z\s\.,!?;:\-\'"()]+$'),
            'hindi': re.compile(r'^[\u0900-\u097F\sa-zA-Z\.,!?;:\-\'"()]+$'),
            'sanskrit': re.compile(r'^[\u0900-\u097F\sa-zA-Z\.,!?;:\-\'"()]+$')
        }
    
    def analyze_text_script(self, text: str) -> Dict:
        """Detailed script analysis of text."""
        if not text:
            return {'script': 'empty', 'confidence': 0, 'details': {}}
        
        # Character analysis
        total_chars = len(text)
        alpha_chars = sum(1 for c in text if c.isalpha())
        
        if alpha_chars == 0:
            return {'script': 'no_alpha', 'confidence': 0, 'details': {'total_chars': total_chars}}
        
        # Count different scripts
        devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        latin_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
        other_chars = alpha_chars - devanagari_chars - latin_chars
        
        # Calculate ratios
        devanagari_ratio = devanagari_chars / alpha_chars
        latin_ratio = latin_chars / alpha_chars
        other_ratio = other_chars / alpha_chars
        
        details = {
            'total_chars': total_chars,
            'alpha_chars': alpha_chars,
            'devanagari_chars': devanagari_chars,
            'latin_chars': latin_chars,
            'other_chars': other_chars,
            'devanagari_ratio': devanagari_ratio,
            'latin_ratio': latin_ratio,
            'other_ratio': other_ratio
        }
        
        # Determine script and confidence
        if devanagari_ratio > 0.7:
            script = 'devanagari'
            confidence = devanagari_ratio
        elif latin_ratio > 0.8:
            script = 'latin'
            confidence = latin_ratio
        elif devanagari_ratio > 0.3:
            script = 'mixed_devanagari'
            confidence = devanagari_ratio
        elif latin_ratio > 0.3:
            script = 'mixed_latin'
            confidence = latin_ratio
        else:
            script = 'mixed_other'
            confidence = max(devanagari_ratio, latin_ratio)
        
        return {
            'script': script,
            'confidence': confidence,
            'details': details
        }
    
    def detect_language(self, text: str, expected_language: str) -> Dict:
        """Detect language and provide detailed analysis."""
        script_analysis = self.analyze_text_script(text)
        
        # Language prediction based on script
        script = script_analysis['script']
        confidence = script_analysis['confidence']
        
        if script in ['devanagari', 'mixed_devanagari']:
            if expected_language == 'hindi':
                predicted_language = 'hindi'
                match_score = confidence
            elif expected_language == 'sanskrit':
                predicted_language = 'sanskrit'
                match_score = confidence
            else:
                predicted_language = 'hindi_or_sanskrit'
                match_score = confidence * 0.8  # Penalty for unexpected
        elif script in ['latin', 'mixed_latin']:
            if expected_language == 'english':
                predicted_language = 'english'
                match_score = confidence
            else:
                predicted_language = 'english'
                match_score = confidence * 0.5  # Penalty for unexpected
        else:
            predicted_language = 'unknown'
            match_score = 0
        
        # Check if language matches expectation
        language_match = (
            (expected_language == 'english' and predicted_language == 'english') or
            (expected_language in ['hindi', 'sanskrit'] and predicted_language in ['hindi', 'sanskrit', 'hindi_or_sanskrit'])
        )
        
        return {
            'expected_language': expected_language,
            'predicted_language': predicted_language,
            'language_match': language_match,
            'match_score': match_score,
            'script_analysis': script_analysis,
            'text_preview': text[:100] + '...' if len(text) > 100 else text
        }

class DatasetTester:
    """Tests all datasets from download_data.py configuration."""
    
    def __init__(self, sample_size: int = 10):
        self.sample_size = sample_size
        self.language_detector = LanguageDetector()
        self.results = defaultdict(list)
        
        # Load dataset configuration from download_data.py
        self.datasets_config = self._load_datasets_config()
    
    def _load_datasets_config(self) -> Dict:
        """Load dataset configuration from download_data.py."""
        # Import the DatasetConfig class from download_data.py
        sys.path.append(str(Path(__file__).parent))
        try:
            from download_data import DatasetConfig
            return DatasetConfig.DATASETS
        except ImportError as e:
            logger.error(f"Could not import DatasetConfig: {e}")
            # Fallback configuration
            return {
                'english': [],
                'hindi': [],
                'sanskrit': []
            }
    
    def check_authentication(self) -> bool:
        """Check if user is authenticated with Hugging Face."""
        try:
            user_info = whoami()
            logger.info(f"✅ Authenticated as: {user_info['name']}")
            return True
        except Exception as e:
            logger.warning("⚠️  Hugging Face authentication not found")
            return False
    
    def test_dataset(self, dataset_info: Dict, expected_language: str) -> Dict:
        """Test a single dataset and return results."""
        dataset_name = dataset_info['name']
        config = dataset_info.get('config')
        text_column = dataset_info.get('text_column', 'text')
        split = dataset_info.get('split', 'train')
        
        logger.info(f"Testing {dataset_name} (config: {config}, split: {split}) for {expected_language}")
        
        result = {
            'dataset_name': dataset_name,
            'config': config,
            'split': split,
            'expected_language': expected_language,
            'text_column': text_column,
            'status': 'unknown',
            'samples': [],
            'language_stats': defaultdict(int),
            'error': None
        }
        
        try:
            # Load dataset
            dataset = load_dataset(
                dataset_name,
                config,
                streaming=True,
                split=split
            )
            
            # Sample texts
            samples_collected = 0
            samples = []
            
            for example in dataset:
                if samples_collected >= self.sample_size:
                    break
                
                text = example.get(text_column, '')
                if not text or len(text.strip()) < 10:
                    continue
                
                # Analyze language
                analysis = self.language_detector.detect_language(text, expected_language)
                samples.append(analysis)
                
                # Update stats
                result['language_stats'][analysis['predicted_language']] += 1
                if analysis['language_match']:
                    result['language_stats']['correct_matches'] += 1
                
                samples_collected += 1
            
            result['samples'] = samples
            result['status'] = 'success'
            result['samples_collected'] = samples_collected
            
            # Calculate accuracy
            if samples_collected > 0:
                accuracy = result['language_stats']['correct_matches'] / samples_collected
                result['accuracy'] = accuracy
            else:
                result['accuracy'] = 0
            
            logger.info(f"✅ {dataset_name}: {samples_collected} samples, {result['accuracy']:.2f} accuracy")
            
        except Exception as e:
            error_msg = str(e)
            result['status'] = 'error'
            result['error'] = error_msg
            logger.error(f"❌ {dataset_name}: {error_msg}")
        
        return result
    
    def test_all_datasets(self) -> Dict:
        """Test all datasets for all languages."""
        logger.info("Starting comprehensive dataset testing...")
        
        # Check authentication
        auth_ok = self.check_authentication()
        
        all_results = {
            'authentication': auth_ok,
            'test_config': {
                'sample_size': self.sample_size
            },
            'results_by_language': {},
            'summary': {}
        }
        
        # Test each language
        for language, datasets in self.datasets_config.items():
            logger.info(f"\n--- Testing {language.upper()} datasets ---")
            
            language_results = []
            successful_datasets = 0
            total_accuracy = 0
            
            for dataset_info in datasets:
                result = self.test_dataset(dataset_info, language)
                language_results.append(result)
                
                if result['status'] == 'success':
                    successful_datasets += 1
                    total_accuracy += result['accuracy']
            
            # Calculate language summary
            avg_accuracy = total_accuracy / successful_datasets if successful_datasets > 0 else 0
            
            all_results['results_by_language'][language] = {
                'datasets': language_results,
                'total_datasets': len(datasets),
                'successful_datasets': successful_datasets,
                'failed_datasets': len(datasets) - successful_datasets,
                'average_accuracy': avg_accuracy
            }
            
            logger.info(f"{language} summary: {successful_datasets}/{len(datasets)} datasets successful, {avg_accuracy:.2f} avg accuracy")
        
        # Overall summary
        total_datasets = sum(len(datasets) for datasets in self.datasets_config.values())
        total_successful = sum(lang_result['successful_datasets'] for lang_result in all_results['results_by_language'].values())
        overall_accuracy = sum(
            lang_result['average_accuracy'] * lang_result['successful_datasets'] 
            for lang_result in all_results['results_by_language'].values()
        ) / total_successful if total_successful > 0 else 0
        
        all_results['summary'] = {
            'total_datasets': total_datasets,
            'successful_datasets': total_successful,
            'failed_datasets': total_datasets - total_successful,
            'overall_success_rate': total_successful / total_datasets if total_datasets > 0 else 0,
            'overall_accuracy': overall_accuracy
        }
        
        return all_results
    
    def print_detailed_report(self, results: Dict):
        """Print a detailed report of all test results."""
        print("\n" + "="*80)
        print("COMPREHENSIVE DATASET TESTING REPORT")
        print("="*80)
        
        # Authentication status
        auth_status = "✅ Authenticated" if results['authentication'] else "⚠️  Not authenticated"
        print(f"Authentication: {auth_status}")
        print(f"Sample size per dataset: {results['test_config']['sample_size']}")
        
        # Overall summary
        summary = results['summary']
        print(f"\nOVERALL SUMMARY:")
        print(f"  Total datasets tested: {summary['total_datasets']}")
        print(f"  Successful: {summary['successful_datasets']} ({summary['overall_success_rate']:.1%})")
        print(f"  Failed: {summary['failed_datasets']}")
        print(f"  Overall language accuracy: {summary['overall_accuracy']:.1%}")
        
        # Per-language results
        for language, lang_results in results['results_by_language'].items():
            print(f"\n{language.upper()} DATASETS:")
            print(f"  Success rate: {lang_results['successful_datasets']}/{lang_results['total_datasets']} ({lang_results['successful_datasets']/lang_results['total_datasets']:.1%})")
            print(f"  Average accuracy: {lang_results['average_accuracy']:.1%}")
            
            for dataset_result in lang_results['datasets']:
                status_icon = "✅" if dataset_result['status'] == 'success' else "❌"
                dataset_name = dataset_result['dataset_name']
                config = dataset_result['config'] or 'default'
                
                if dataset_result['status'] == 'success':
                    accuracy = dataset_result['accuracy']
                    samples = dataset_result['samples_collected']
                    split = dataset_result['split']
                    print(f"    {status_icon} {dataset_name} ({config}, split: {split}): {accuracy:.1%} accuracy, {samples} samples")
                    
                    # Show language distribution
                    lang_stats = dataset_result['language_stats']
                    stats_str = ", ".join([f"{lang}: {count}" for lang, count in lang_stats.items() if lang != 'correct_matches'])
                    print(f"        Language distribution: {stats_str}")
                else:
                    error = dataset_result['error']
                    split = dataset_result['split']
                    print(f"    {status_icon} {dataset_name} ({config}, split: {split}): FAILED - {error}")
        
        # Problematic datasets
        failed_datasets = []
        low_accuracy_datasets = []
        
        for language, lang_results in results['results_by_language'].items():
            for dataset_result in lang_results['datasets']:
                if dataset_result['status'] == 'error':
                    failed_datasets.append((language, dataset_result['dataset_name'], dataset_result['error']))
                elif dataset_result['status'] == 'success' and dataset_result['accuracy'] < 0.5:
                    low_accuracy_datasets.append((language, dataset_result['dataset_name'], dataset_result['accuracy']))
        
        if failed_datasets:
            print(f"\n⚠️  FAILED DATASETS:")
            for language, dataset_name, error in failed_datasets:
                print(f"  - {language}/{dataset_name}: {error}")
        
        if low_accuracy_datasets:
            print(f"\n⚠️  LOW ACCURACY DATASETS (< 50%):")
            for language, dataset_name, accuracy in low_accuracy_datasets:
                print(f"  - {language}/{dataset_name}: {accuracy:.1%}")
        
        print("="*80)
    
    def save_results(self, results: Dict, filename: str = "dataset_test_results.json"):
        """Save results to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {filename}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test all datasets from download_data.py")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of samples to test per dataset")
    parser.add_argument("--output", default="dataset_test_results.json", help="Output file for results")
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = DatasetTester(sample_size=args.sample_size)
    
    # Run tests
    results = tester.test_all_datasets()
    
    # Print report
    tester.print_detailed_report(results)
    
    # Save results
    tester.save_results(results, args.output)
    
    logger.info("Dataset testing completed!")

if __name__ == "__main__":
    main()
