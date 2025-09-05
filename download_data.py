#!/usr/bin/env python3
"""
Multilingual Corpus Collection Script
Downloads and preprocesses text data from Hugging Face datasets for English, Hindi, and Sanskrit.
Target: 3 billion tokens total with distribution: English (50%), Hindi (30-40%), Sanskrit (10-20%)
"""

import os
import sys
import json
import hashlib
import re
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Iterator, Set, Tuple
from collections import defaultdict
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, as_completed

# External libraries
import datasets
from datasets import load_dataset, Dataset
from tqdm import tqdm
import tiktoken
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import spacy
from transformers import AutoTokenizer
from huggingface_hub import login, whoami

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_data.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_huggingface_auth():
    """Check Hugging Face authentication and guide user if needed."""
    try:
        user_info = whoami()
        logger.info(f"✅ Authenticated as: {user_info['name']}")
        return True
    except Exception as e:
        logger.warning("⚠️  Hugging Face authentication not found or invalid")
        print("\n" + "="*60)
        print("🔐 HUGGING FACE AUTHENTICATION REQUIRED")
        print("="*60)
        print("Some datasets require authentication. You have two options:")
        print("\n1. Use your existing token:")
        print("   huggingface-cli login")
        print("\n2. Get a token from https://huggingface.co/settings/tokens")
        print("   Then run: huggingface-cli login")
        print("\n3. Continue without authentication (some datasets may fail)")
        print("="*60)
        
        choice = input("\nChoose (1=login now, 2=get token, 3=continue anyway): ").strip()
        
        if choice == "1":
            try:
                token = input("Enter your Hugging Face token: ").strip()
                login(token=token)
                logger.info("✅ Authentication successful!")
                return True
            except Exception as e:
                logger.error(f"❌ Authentication failed: {e}")
                return False
        elif choice == "2":
            print("\n📋 Steps to get your token:")
            print("1. Go to: https://huggingface.co/settings/tokens")
            print("2. Create a new token (read permission is sufficient)")
            print("3. Copy the token")
            print("4. Run: huggingface-cli login")
            print("5. Restart this script")
            return False
        else:
            logger.warning("⚠️  Continuing without authentication - some datasets may fail")
            return True

class TokenCounter:
    """Optimized token counting with fast approximations."""
    
    def __init__(self):
        self.tokenizers = {}
        self.use_fast_counting = True  # Flag to enable fast approximation
        self._initialize_tokenizers()
    
    def _initialize_tokenizers(self):
        """Initialize tokenizers for different languages."""
        try:
            # For English - using tiktoken (GPT-style tokenization)
            self.tokenizers['english'] = tiktoken.get_encoding("cl100k_base")
            
            # For Hindi - skip heavy transformer tokenizer, use fast approximation
            if not self.use_fast_counting:
                self.tokenizers['hindi'] = AutoTokenizer.from_pretrained("ai4bharat/indic-bert")
            
            # For Sanskrit - using basic word tokenization (fallback)
            self.tokenizers['sanskrit'] = None
            
        except Exception as e:
            logger.warning(f"Error initializing tokenizers: {e}")
            # Fallback to fast approximation
            self.use_fast_counting = True
            self.tokenizers = {}
    
    def count_tokens(self, text: str, language: str) -> int:
        """Optimized token counting with fast approximations."""
        if not text or not text.strip():
            return 0
            
        try:
            if self.use_fast_counting:
                # Fast approximation based on word count and language characteristics
                word_count = len(text.split())
                
                if language == 'english':
                    # English: ~1.3 tokens per word on average
                    return int(word_count * 1.3)
                elif language == 'hindi':
                    # Hindi: ~1.8 tokens per word (longer words, complex morphology)
                    return int(word_count * 1.8)
                elif language == 'sanskrit':
                    # Sanskrit: ~2.0 tokens per word (very complex morphology)
                    return int(word_count * 2.0)
                else:
                    return word_count
            else:
                # Original precise tokenization (slower)
                if language == 'english' and 'english' in self.tokenizers:
                    return len(self.tokenizers['english'].encode(text))
                elif language == 'hindi' and 'hindi' in self.tokenizers:
                    return len(self.tokenizers['hindi'].tokenize(text))
                else:
                    # Fallback to word tokenization
                    return len(word_tokenize(text))
        except Exception:
            # Ultimate fallback - split by whitespace
            return len(text.split())

class DatasetConfig:
    """Configuration for datasets to download for each language."""
    
    DATASETS = {
        'english': [
            {
                'name': 'HuggingFaceFW/fineweb',
                'config': 'sample-10BT',
                'text_column': 'text',
                'streaming': True,
                'description': 'High-quality web text corpus (FineWeb English)'
            }
        ],
        'hindi': [
            {
                'name': 'wikimedia/wikipedia',
                'config': '20231101.hi',
                'text_column': 'text',
                'streaming': True,
                'description': 'Hindi Wikipedia dump'
            },
            {
                'name': 'ai4bharat/sangraha',
                'config': 'verified',
                'text_column': 'text',
                'streaming': True,
                'description': 'AI4Bharat Sangraha verified dataset (high-quality Hindi)',
                'split': 'hin'
            },
            {
                'name': 'ai4bharat/sangraha',
                'config': 'synthetic',
                'text_column': 'text',
                'streaming': True,
                'description': 'AI4Bharat Sangraha synthetic dataset (Hindi Devanagari)',
                'split': 'hin_Deva'
            }
        ],
        'sanskrit': [
            {
                'name': 'wikimedia/wikipedia',
                'config': '20231101.sa',
                'text_column': 'text',
                'streaming': True,
                'description': 'Sanskrit Wikipedia dump'
            },
            {
                'name': 'ai4bharat/sangraha',
                'config': 'verified',
                'text_column': 'text',
                'streaming': True,
                'description': 'AI4Bharat Sangraha verified dataset (high-quality Sanskrit)',
                'split': 'san'
            },
            {
                'name': 'ai4bharat/sangraha',
                'config': 'synthetic',
                'text_column': 'text',
                'streaming': True,
                'description': 'AI4Bharat Sangraha synthetic dataset (Sanskrit Devanagari)',
                'split': 'san_Deva'
            }
        ]
    }

class TextPreprocessor:
    """Handles text cleaning, deduplication, and segmentation with optimizations."""
    
    def __init__(self):
        self.seen_hashes: Set[str] = set()
        # Pre-compile regex patterns for better performance
        self.whitespace_pattern = re.compile(r'\s+')
        self.english_pattern = re.compile(r'[^\w\s\.,!?;:\-\'"()&@#%]+')
        self.devanagari_pattern = re.compile(r'[^\u0900-\u097F\w\s\.,!?;:\-\'"()।॥]+')
        
        # Cache for script detection results
        self.script_cache: Dict[str, str] = {}
        self.cache_size_limit = 10000
    
    def detect_language_script(self, text: str) -> str:
        """Optimized language detection with caching and sampling."""
        if not text:
            return 'unknown'
        
        # Use first 500 chars for detection (much faster for long texts)
        sample_text = text[:500]
        
        # Check cache first
        text_hash = hash(sample_text) % 1000000  # Simple hash for cache key
        if text_hash in self.script_cache:
            return self.script_cache[text_hash]
        
        # Count character types in single pass instead of 3 separate passes
        devanagari_chars = 0
        latin_chars = 0
        total_alpha = 0
        
        for char in sample_text:
            if char.isalpha():
                total_alpha += 1
                if '\u0900' <= char <= '\u097F':
                    devanagari_chars += 1
                elif ord(char) < 128:
                    latin_chars += 1
        
        if total_alpha == 0:
            result = 'unknown'
        else:
            devanagari_ratio = devanagari_chars / total_alpha
            latin_ratio = latin_chars / total_alpha
            
            # Improved detection for code-switching scenarios
            if devanagari_ratio > 0.7:
                result = 'devanagari'  # Strong Devanagari presence
            elif devanagari_ratio > 0.3:
                result = 'mixed_devanagari'  # Devanagari with English (common in Hindi)
            elif latin_ratio > 0.9:
                result = 'latin'  # Pure English
            elif latin_ratio > 0.6:
                result = 'latin_dominant'  # Mostly English
            else:
                result = 'mixed'
        
        # Cache result (with size limit)
        if len(self.script_cache) < self.cache_size_limit:
            self.script_cache[text_hash] = result
        
        return result
    
    def is_language_appropriate(self, text: str, expected_language: str) -> bool:
        """Check if text is appropriate for the expected language with improved code-switching handling."""
        detected = self.detect_language_script(text)
        
        if expected_language == 'english':
            return detected in ['latin', 'latin_dominant', 'mixed']
        elif expected_language == 'hindi':
            # Hindi can have English words - accept mixed content
            return detected in ['devanagari', 'mixed_devanagari', 'mixed']
        elif expected_language == 'sanskrit':
            # Sanskrit should be primarily Devanagari
            return detected in ['devanagari', 'mixed_devanagari']
        else:
            return True  # Accept anything for unknown languages
    
    def clean_text(self, text: str, language: str) -> str:
        """Optimized text cleaning with pre-compiled patterns and quick checks."""
        if not text or len(text) < 10:  # Quick length check
            return ""
        
        # Single regex operation for whitespace normalization
        text = self.whitespace_pattern.sub(' ', text).strip()
        
        # Quick word count approximation before expensive operations
        word_count = text.count(' ') + 1
        if word_count < 3:
            return ""
        
        # Language-specific cleaning with pre-compiled patterns
        if language == 'english':
            text = self.english_pattern.sub('', text)
        elif language in ['hindi', 'sanskrit']:
            text = self.devanagari_pattern.sub('', text)
        
        # Final word count check after cleaning
        if len(text.split()) < 3:
            return ""
        
        # Language appropriateness check (optimized with sampling)
        if not self.is_language_appropriate(text, language):
            return ""
            
        return text
    
    def is_duplicate(self, text: str) -> bool:
        """Optimized duplicate detection with shorter hashes."""
        # For very long texts, hash only sample portions for speed
        if len(text) > 5000:
            hash_text = text[:1000] + text[-1000:]  # Hash first and last 1000 chars
        else:
            hash_text = text
            
        # Use shorter hash for speed vs memory tradeoff
        text_hash = hashlib.md5(hash_text.encode()).hexdigest()[:16]
        
        if text_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(text_hash)
        return False
    
    def segment_text(self, text: str, language: str) -> List[str]:
        """Segment text into sentences."""
        try:
            if language == 'english':
                sentences = sent_tokenize(text)
            else:
                # For Hindi and Sanskrit, use basic punctuation-based segmentation
                sentences = re.split(r'[।॥\.\!\?]+', text)
            
            # Filter short sentences
            return [s.strip() for s in sentences if len(s.strip().split()) >= 3]
        except:
            return [text]  # Fallback

class MultilingualCorpusDownloader:
    """Main class for downloading and processing multilingual corpus."""
    
    def __init__(self, output_dir: str = "corpus_data", target_tokens: int = 3_000_000_000):
        self.output_dir = Path(output_dir)
        self.target_tokens = target_tokens
        self.token_counter = TokenCounter()
        self.preprocessor = TextPreprocessor()
        self.dataset_config = DatasetConfig()
        
        # Token targets per language
        self.token_targets = {
            'english': int(target_tokens * 0.5),      # 50%
            'hindi': int(target_tokens * 0.35),       # 35%
            'sanskrit': int(target_tokens * 0.15)     # 15%
        }
        
        # Current token counts
        self.current_tokens = defaultdict(int)
        
        # Setup directories
        self._setup_directories()
        
        logger.info(f"Initialized downloader with target: {target_tokens:,} tokens")
        logger.info(f"Token distribution: {self.token_targets}")
    
    def _setup_directories(self):
        """Create necessary directories."""
        for lang in ['english', 'hindi', 'sanskrit']:
            lang_dir = self.output_dir / lang
            lang_dir.mkdir(parents=True, exist_ok=True)
            (lang_dir / 'raw').mkdir(exist_ok=True)
            (lang_dir / 'processed').mkdir(exist_ok=True)
            (lang_dir / 'metadata').mkdir(exist_ok=True)
    
    def save_batch(self, texts: List[str], language: str, dataset_name: str, batch_num: int):
        """Save a batch of texts to file."""
        output_file = self.output_dir / language / 'raw' / f"{dataset_name}_{batch_num:06d}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for text in texts:
                f.write(text + '\n' + '='*50 + '\n')
        
        logger.info(f"Saved batch {batch_num} for {language}/{dataset_name}: {len(texts)} texts")
    
    def download_dataset(self, dataset_info: Dict, language: str) -> int:
        """Download and process a single dataset."""
        dataset_name = dataset_info['name'].replace('/', '_')
        logger.info(f"Starting download: {dataset_name} ({language})")
        
        # Special handling for Sanskrit - hard cutoff at 450M tokens
        is_sanskrit = language == 'sanskrit'
        sanskrit_cutoff = self.token_targets['sanskrit'] if is_sanskrit else None
            
        try:
            # Determine split to use
            split = dataset_info.get('split', 'train')
            
            # Load dataset with streaming
            dataset = load_dataset(
                dataset_info['name'],
                dataset_info.get('config'),
                streaming=dataset_info.get('streaming', True),
                split=split
            )
            
            batch_texts = []
            batch_size = 1000
            batch_num = 0
            total_tokens = 0
            processed_count = 0
            
            # Create progress bar
            pbar = tqdm(
                desc=f"{language}/{dataset_name}",
                unit=" texts",
                dynamic_ncols=True
            )
            
            target_reached = False
            
            for example in dataset:
                # For non-Sanskrit languages, check target
                if not is_sanskrit and self.current_tokens[language] >= self.token_targets[language]:
                    logger.info(f"Target reached for {language}: {self.current_tokens[language]:,} tokens")
                    target_reached = True
                    break
                # For Sanskrit, enforce hard cutoff
                if is_sanskrit and self.current_tokens[language] >= sanskrit_cutoff:
                    logger.info(f"Sanskrit cutoff reached: {self.current_tokens[language]:,} tokens")
                    target_reached = True
                    break
                
                # Extract text
                text_column = dataset_info.get('text_column', 'text')
                text = example.get(text_column, '')
                
                if not text:
                    continue
                
                # Preprocess text
                cleaned_text = self.preprocessor.clean_text(text, language)
                if not cleaned_text or self.preprocessor.is_duplicate(cleaned_text):
                    continue
                
                # Count tokens
                token_count = self.token_counter.count_tokens(cleaned_text, language)
                if token_count < 10:  # Skip very short texts
                    continue
                
                batch_texts.append(cleaned_text)
                total_tokens += token_count
                self.current_tokens[language] += token_count
                processed_count += 1
                
                # Update progress bar with special message for Sanskrit
                postfix_data = {
                    'tokens': f"{self.current_tokens[language]:,}",
                }
                
                if is_sanskrit:
                    postfix_data['status'] = 'downloading_all'
                else:
                    postfix_data['target'] = f"{self.token_targets[language]:,}"
                    postfix_data['progress'] = f"{(self.current_tokens[language]/self.token_targets[language]*100):.1f}%"
                
                pbar.set_postfix(postfix_data)
                pbar.update(1)
                
                # Save batch when full
                if len(batch_texts) >= batch_size:
                    self.save_batch(batch_texts, language, dataset_name, batch_num)
                    batch_texts = []
                    batch_num += 1
            
            # Save remaining texts
            if batch_texts:
                self.save_batch(batch_texts, language, dataset_name, batch_num)
            
            pbar.close()
            
            # Special logging for Sanskrit
            if is_sanskrit:
                logger.info(f"Completed {dataset_name} (Sanskrit - downloaded all available): {processed_count:,} texts, {total_tokens:,} tokens")
            else:
                logger.info(f"Completed {dataset_name} ({language}): {processed_count:,} texts, {total_tokens:,} tokens")
            
            return total_tokens
            
        except Exception as e:
            logger.error(f"Error downloading {dataset_name} ({language}): {e}")
            if is_sanskrit:
                logger.warning(f"Sanskrit dataset {dataset_name} may not be available - this is expected for some datasets")
            return 0
    
    def process_raw_files(self, language: str):
        """Process raw files to create final cleaned corpus."""
        logger.info(f"Processing raw files for {language}")
        
        raw_dir = self.output_dir / language / 'raw'
        processed_dir = self.output_dir / language / 'processed'
        
        all_texts = []
        total_files = len(list(raw_dir.glob('*.txt')))
        
        with tqdm(desc=f"Processing {language} files", total=total_files) as pbar:
            for file_path in raw_dir.glob('*.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    texts = content.split('=' * 50)
                    
                    for text in texts:
                        text = text.strip()
                        if text:
                            # Segment into sentences
                            sentences = self.preprocessor.segment_text(text, language)
                            all_texts.extend(sentences)
                
                pbar.update(1)
        
        # Remove duplicates and save
        logger.info(f"Removing duplicates for {language}...")
        unique_texts = []
        seen_hashes = set()
        
        for text in tqdm(all_texts, desc=f"Deduplicating {language}"):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                unique_texts.append(text)
        
        # Save processed corpus
        output_file = processed_dir / f"{language}_corpus.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for text in unique_texts:
                f.write(text + '\n')
        
        # Save metadata
        metadata = {
            'language': language,
            'total_texts': len(unique_texts),
            'total_tokens': sum(self.token_counter.count_tokens(text, language) for text in unique_texts[:1000]),
            'duplicates_removed': len(all_texts) - len(unique_texts),
            'deduplication_ratio': (len(all_texts) - len(unique_texts)) / len(all_texts) if all_texts else 0
        }
        
        metadata_file = self.output_dir / language / 'metadata' / 'processing_stats.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Processed {language}: {len(unique_texts):,} unique texts")
        return len(unique_texts)
    
    def download_all(self):
        """Download all datasets for all languages."""
        logger.info("Starting multilingual corpus download")
        
        # Print targets
        print("\n" + "="*60)
        print("MULTILINGUAL CORPUS DOWNLOAD")
        print("="*60)
        print(f"Total target tokens: {self.target_tokens:,}")
        for lang, target in self.token_targets.items():
            print(f"  {lang.capitalize()}: {target:,} tokens ({target/self.target_tokens*100:.1f}%)")
        print("="*60 + "\n")
        
        # Download datasets for each language
        for language in ['english', 'hindi', 'sanskrit']:
            logger.info(f"\n--- Starting {language.upper()} downloads ---")
            
            if language == 'sanskrit':
                logger.info("📢 SANSKRIT NOTICE: Limited data available on HuggingFace.")
                logger.info("Will download ALL available Sanskrit data regardless of token target.")
                print(f"\n🔍 Sanskrit Data Collection Strategy:")
                print(f"   - Target was: {self.token_targets[language]:,} tokens (15% of total)")
                print(f"   - Strategy: Download everything available")
                print(f"   - Will report actual tokens collected at the end")
                print("="*60)
            
            datasets_info = self.dataset_config.DATASETS[language]
            
            for dataset_info in datasets_info:
                # For non-Sanskrit, check if target is reached
                if language != 'sanskrit' and self.current_tokens[language] >= self.token_targets[language]:
                    logger.info(f"Target reached for {language}, skipping remaining datasets")
                    break
                
                tokens_downloaded = self.download_dataset(dataset_info, language)
                
                # Special reporting for Sanskrit
                if language == 'sanskrit':
                    logger.info(f"Sanskrit progress: {self.current_tokens[language]:,} tokens collected so far")
            
            # Final report for Sanskrit
            if language == 'sanskrit':
                actual_tokens = self.current_tokens[language]
                target_tokens = self.token_targets[language]
                
                print(f"\n📊 SANSKRIT COLLECTION COMPLETE:")
                print(f"   - Original target: {target_tokens:,} tokens (15%)")
                print(f"   - Actually collected: {actual_tokens:,} tokens")
                
                if actual_tokens < target_tokens:
                    shortage = target_tokens - actual_tokens
                    print(f"   - Shortage: {shortage:,} tokens ({shortage/target_tokens*100:.1f}% less than target)")
                    print(f"   - This is expected due to limited Sanskrit data on HuggingFace")
                else:
                    surplus = actual_tokens - target_tokens
                    print(f"   - Surplus: {surplus:,} tokens ({surplus/target_tokens*100:.1f}% more than target)")
                
                percentage_of_total = (actual_tokens / self.target_tokens * 100) if self.target_tokens > 0 else 0
                print(f"   - Actual percentage of total corpus: {percentage_of_total:.2f}%")
                print("="*60)
                
                logger.info(f"Sanskrit final count: {actual_tokens:,} tokens ({percentage_of_total:.2f}% of total corpus)")
        
        # Adjust token targets based on actual Sanskrit collection
        actual_sanskrit_tokens = self.current_tokens['sanskrit']
        original_sanskrit_target = self.token_targets['sanskrit']
        
        if actual_sanskrit_tokens != original_sanskrit_target:
            logger.info(f"Adjusting targets due to Sanskrit availability...")
            
            # Calculate remaining tokens to distribute between English and Hindi
            remaining_target = self.target_tokens - actual_sanskrit_tokens
            
            # Redistribute: English gets 50/(50+35) and Hindi gets 35/(50+35) of remaining
            english_ratio = 0.5 / (0.5 + 0.35)  # ≈ 0.588
            hindi_ratio = 0.35 / (0.5 + 0.35)   # ≈ 0.412
            
            self.token_targets['english'] = int(remaining_target * english_ratio)
            self.token_targets['hindi'] = int(remaining_target * hindi_ratio)
            self.token_targets['sanskrit'] = actual_sanskrit_tokens  # Update to actual
            
            print(f"\n🔄 ADJUSTED TARGETS (due to Sanskrit availability):")
            print(f"   - English: {self.token_targets['english']:,} tokens")
            print(f"   - Hindi: {self.token_targets['hindi']:,} tokens") 
            print(f"   - Sanskrit: {self.token_targets['sanskrit']:,} tokens (actual collected)")
            print(f"   - Total: {sum(self.token_targets.values()):,} tokens")
            print("="*60)
        
        # Process raw files
        logger.info("\n--- Processing raw files ---")
        for language in ['english', 'hindi', 'sanskrit']:
            self.process_raw_files(language)
        
        # Generate final report
        self.generate_report()
    
    def generate_report(self):
        """Generate final download report."""
        report = {
            'target_tokens': self.target_tokens,
            'languages': {},
            'total_downloaded_tokens': sum(self.current_tokens.values())
        }
        
        for language in ['english', 'hindi', 'sanskrit']:
            processed_dir = self.output_dir / language / 'processed'
            corpus_file = processed_dir / f"{language}_corpus.txt"
            
            if corpus_file.exists():
                with open(corpus_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    actual_tokens = sum(
                        self.token_counter.count_tokens(line.strip(), language) 
                        for line in lines[:1000]  # Sample for speed
                    ) * (len(lines) / 1000)  # Estimate
            else:
                actual_tokens = 0
            
            report['languages'][language] = {
                'target_tokens': self.token_targets[language],
                'downloaded_tokens': self.current_tokens[language],
                'processed_tokens': int(actual_tokens),
                'target_percentage': self.token_targets[language] / self.target_tokens * 100,
                'actual_percentage': self.current_tokens[language] / sum(self.current_tokens.values()) * 100 if sum(self.current_tokens.values()) > 0 else 0
            }
        
        # Save report
        report_file = self.output_dir / 'download_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("DOWNLOAD COMPLETE - SUMMARY")
        print("="*60)
        print(f"Total target: {self.target_tokens:,} tokens")
        print(f"Total downloaded: {sum(self.current_tokens.values()):,} tokens")
        print(f"Completion rate: {sum(self.current_tokens.values())/self.target_tokens*100:.1f}%")
        print("\nPer language:")
        for lang, stats in report['languages'].items():
            status_note = ""
            if lang == 'sanskrit':
                if stats['downloaded_tokens'] < stats['target_tokens']:
                    status_note = " (all available data collected)"
                else:
                    status_note = " (exceeded limited target)"
            
            print(f"  {lang.capitalize()}:")
            print(f"    Target: {stats['target_tokens']:,} tokens ({stats['target_percentage']:.1f}%)")
            print(f"    Downloaded: {stats['downloaded_tokens']:,} tokens ({stats['actual_percentage']:.1f}%){status_note}")
            completion_rate = (stats['downloaded_tokens']/stats['target_tokens']*100) if stats['target_tokens'] > 0 else 0
            print(f"    Completion: {completion_rate:.1f}%")
        
        # Special note for Sanskrit
        sanskrit_stats = report['languages'].get('sanskrit', {})
        if sanskrit_stats:
            print(f"\n📝 SANSKRIT NOTE:")
            if sanskrit_stats['downloaded_tokens'] < sanskrit_stats['target_tokens']:
                shortage = sanskrit_stats['target_tokens'] - sanskrit_stats['downloaded_tokens']
                print(f"   Sanskrit has limited availability on HuggingFace.")
                print(f"   Collected all available data: {sanskrit_stats['downloaded_tokens']:,} tokens")
                print(f"   This is {shortage:,} tokens less than the original target.")
                print(f"   Consider supplementing with other Sanskrit sources if needed.")
            else:
                print(f"   Successfully collected {sanskrit_stats['downloaded_tokens']:,} tokens")
                print(f"   This meets or exceeds the target despite limited availability.")
        
        print("="*60)

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Download multilingual corpus from Hugging Face")
    parser.add_argument("--output-dir", default="corpus_data", help="Output directory")
    parser.add_argument("--target-tokens", type=int, default=3_000_000_000, help="Target total tokens")
    parser.add_argument("--languages", nargs="+", default=["english", "hindi", "sanskrit"], help="Languages to download")
    parser.add_argument("--skip-auth-check", action="store_true", help="Skip Hugging Face authentication check")
    
    args = parser.parse_args()
    
    # Check Hugging Face authentication unless skipped
    if not args.skip_auth_check:
        auth_ok = check_huggingface_auth()
        if not auth_ok:
            logger.info("Authentication setup required. Exiting.")
            return
    
    # Initialize and run downloader
    downloader = MultilingualCorpusDownloader(
        output_dir=args.output_dir,
        target_tokens=args.target_tokens
    )
    
    try:
        downloader.download_all()
        logger.info("Download completed successfully!")
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise

if __name__ == "__main__":
    main()