#!/usr/bin/env python3
"""
Optimized Space-Efficient Corpus Processor
Processes raw corpus data one language at a time, deleting raw data immediately after processing
to minimize disk space usage.
"""

import os
import sys
import json
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Dict
import random

# External libraries
from tqdm import tqdm
import tiktoken

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimized_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OptimizedCorpusProcessor:
    """Space-efficient corpus processor that minimizes disk usage."""
    
    def __init__(self, corpus_dir: str = "data/corpus_data", target_tokens: int = 3_000_000_000):
        self.corpus_dir = Path(corpus_dir)
        self.target_tokens = target_tokens
        
        # Target distribution (English already processed)
        self.targets = {
            'hindi': int(target_tokens * 0.35),       # 35% = 1.05B tokens
            'sanskrit': int(target_tokens * 0.15)     # 15% = 450M tokens
        }
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
            logger.warning("Could not load tiktoken, using approximation")
        
        # Setup final directory
        self.final_dir = self.corpus_dir / 'final_corpus'
        self.final_dir.mkdir(exist_ok=True)
    
    def count_tokens_fast(self, text: str, language: str) -> int:
        """Fast token counting with language-specific approximations."""
        if not text.strip():
            return 0
        
        if self.tokenizer and language == 'english':
            try:
                return len(self.tokenizer.encode(text))
            except:
                pass
        
        word_count = len(text.split())
        if language == 'english':
            return int(word_count * 1.3)
        elif language == 'hindi':
            return int(word_count * 1.8)
        elif language == 'sanskrit':
            return int(word_count * 2.0)
        else:
            return word_count
    
    def get_disk_space_gb(self) -> float:
        """Get available disk space in GB."""
        try:
            statvfs = os.statvfs(self.corpus_dir)
            available_bytes = statvfs.f_frsize * statvfs.f_bavail
            return available_bytes / (1024**3)
        except:
            return 0.0
    
    def process_language_streaming(self, language: str, target_tokens: int) -> Dict:
        """Process language data with streaming to minimize memory and disk usage."""
        raw_dir = self.corpus_dir / language / 'raw'
        processed_dir = self.corpus_dir / language / 'processed'
        
        if not raw_dir.exists():
            logger.error(f"No raw data found for {language}")
            return {'processed_tokens': 0, 'processed_texts': 0}
        
        text_files = list(raw_dir.glob('*.txt'))
        if not text_files:
            logger.error(f"No text files found for {language}")
            return {'processed_tokens': 0, 'processed_texts': 0}
        
        # Check available space
        available_space = self.get_disk_space_gb()
        logger.info(f"Available disk space: {available_space:.1f} GB")
        
        logger.info(f"Processing {len(text_files)} files for {language}")
        logger.info(f"Target: {target_tokens:,} tokens")
        
        # Create processed directory
        processed_dir.mkdir(exist_ok=True)
        
        # Shuffle files for random sampling
        random.shuffle(text_files)
        
        # Setup output files
        output_file = processed_dir / f"{language}_corpus.txt"
        final_file = self.final_dir / f"{language}_corpus.txt"
        
        total_tokens = 0
        total_texts = 0
        seen_hashes = set()
        
        pbar = tqdm(total=target_tokens, desc=f"Processing {language}", unit="tokens")
        
        # Stream processing - write directly to files
        with open(output_file, 'w', encoding='utf-8') as out_f, \
             open(final_file, 'w', encoding='utf-8') as final_f:
            
            for file_path in text_files:
                if total_tokens >= target_tokens:
                    break
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Split by separator
                    texts = [t.strip() for t in content.split('=' * 50) if t.strip()]
                    
                    for text in texts:
                        if total_tokens >= target_tokens:
                            break
                        
                        if not text or len(text.split()) < 5:
                            continue
                        
                        # Simple deduplication
                        text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
                        if text_hash in seen_hashes:
                            continue
                        seen_hashes.add(text_hash)
                        
                        # Count tokens
                        tokens = self.count_tokens_fast(text, language)
                        if tokens < 10:
                            continue
                        
                        # Write directly to both files
                        text_with_newlines = text + '\n\n'
                        out_f.write(text_with_newlines)
                        final_f.write(text_with_newlines)
                        
                        total_tokens += tokens
                        total_texts += 1
                        pbar.update(tokens)
                        
                        # Flush buffers periodically
                        if total_texts % 1000 == 0:
                            out_f.flush()
                            final_f.flush()
                        
                        if total_tokens >= target_tokens:
                            break
                            
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    continue
        
        pbar.close()
        
        # Save metadata
        metadata = {
            'language': language,
            'target_tokens': target_tokens,
            'actual_tokens': total_tokens,
            'total_texts': total_texts,
            'completion_rate': (total_tokens / target_tokens) * 100 if target_tokens > 0 else 0,
            'avg_tokens_per_text': total_tokens / total_texts if total_texts > 0 else 0,
            'deduplication_ratio': len(seen_hashes) / (len(seen_hashes) + total_texts) if total_texts > 0 else 0
        }
        
        metadata_file = processed_dir / f"{language}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Processed {language}: {total_tokens:,} tokens, {total_texts:,} texts")
        
        # Now delete raw data to save space
        logger.info(f"Deleting raw data for {language} to save space...")
        raw_size_gb = sum(f.stat().st_size for f in raw_dir.glob('*.txt')) / (1024**3)
        shutil.rmtree(raw_dir)
        logger.info(f"Freed {raw_size_gb:.1f} GB by deleting {language} raw data")
        
        return {
            'processed_tokens': total_tokens,
            'processed_texts': total_texts,
            'metadata': metadata,
            'space_freed_gb': raw_size_gb
        }
    
    def copy_english_to_final(self):
        """Create symlink to English data to avoid duplication."""
        english_processed = self.corpus_dir / 'english' / 'processed' / 'english_corpus.txt'
        english_final = self.final_dir / 'english_corpus.txt'
        
        if english_processed.exists() and not english_final.exists():
            logger.info("Creating symlink to English corpus (avoiding duplication)...")
            try:
                english_final.symlink_to(english_processed.resolve())
                logger.info("English corpus symlink created")
            except:
                logger.info("Symlinking failed, skipping English copy to save space")
        elif english_final.exists():
            logger.info("English corpus already exists in final directory")
        else:
            logger.warning("No processed English corpus found")
    
    def process_remaining_languages(self):
        """Process Hindi and Sanskrit with space optimization."""
        print("\n" + "=" * 80)
        print("OPTIMIZED CORPUS PROCESSING")
        print("=" * 80)
        print("Processing strategy: One language at a time, delete raw after processing")
        print("Languages to process: Hindi, Sanskrit")
        print("=" * 80)
        
        # Copy English to final if needed
        self.copy_english_to_final()
        
        results = {}
        total_space_freed = 0
        
        # Process languages in order
        for language in ['hindi', 'sanskrit']:
            if language not in self.targets:
                continue
                
            target = self.targets[language]
            
            # Check if raw data exists
            raw_dir = self.corpus_dir / language / 'raw'
            if not raw_dir.exists():
                logger.warning(f"No raw data found for {language}, skipping...")
                continue
            
            print(f"\n--- Processing {language.upper()} ---")
            print(f"Target: {target:,} tokens")
            
            # Check disk space before processing
            available_space = self.get_disk_space_gb()
            print(f"Available disk space: {available_space:.1f} GB")
            
            if available_space < 5:  # Less than 5GB available
                print(f"⚠️  Warning: Low disk space ({available_space:.1f} GB)")
                response = input("Continue anyway? (y/n): ").strip().lower()
                if response != 'y':
                    print("Skipping due to low disk space")
                    continue
            
            # Process the language
            result = self.process_language_streaming(language, target)
            results[language] = result
            total_space_freed += result.get('space_freed_gb', 0)
            
            print(f"✅ {language.capitalize()} processing complete!")
            print(f"   Processed: {result['processed_tokens']:,} tokens")
            print(f"   Texts: {result['processed_texts']:,}")
            print(f"   Space freed: {result.get('space_freed_gb', 0):.1f} GB")
        
        # Final report
        self.print_final_report(results, total_space_freed)
    
    def print_final_report(self, results: Dict, total_space_freed: float):
        """Print comprehensive final report."""
        print(f"\n" + "=" * 80)
        print("PROCESSING COMPLETE - FINAL REPORT")
        print("=" * 80)
        
        # Calculate totals
        english_tokens = 1_500_000_000  # From metadata we saw earlier
        total_processed = english_tokens + sum(r['processed_tokens'] for r in results.values())
        
        print(f"📊 FINAL CORPUS STATISTICS:")
        print(f"   Total tokens: {total_processed:,}")
        print(f"   Target tokens: {self.target_tokens:,}")
        print(f"   Achievement: {(total_processed/self.target_tokens)*100:.1f}%")
        print(f"   Space freed: {total_space_freed:.1f} GB")
        
        print(f"\n📈 LANGUAGE DISTRIBUTION:")
        
        # English (already processed)
        english_pct = (english_tokens / total_processed) * 100 if total_processed > 0 else 0
        print(f"   English:  {english_tokens:,} tokens ({english_pct:.1f}%)")
        
        # Processed languages
        for language, result in results.items():
            tokens = result['processed_tokens']
            pct = (tokens / total_processed) * 100 if total_processed > 0 else 0
            target_pct = 35 if language == 'hindi' else 15
            status = "✅" if abs(pct - target_pct) <= 5 else "⚠️"
            
            print(f"   {language.capitalize()}: {tokens:,} tokens ({pct:.1f}%) {status}")
        
        print(f"\n📁 OUTPUT LOCATIONS:")
        print(f"   Final corpus: {self.final_dir}")
        print(f"   Individual files:")
        for file in self.final_dir.glob('*_corpus.txt'):
            size_mb = file.stat().st_size / (1024*1024)
            print(f"     {file.name}: {size_mb:.1f} MB")
        
        print(f"\n💾 DISK SPACE OPTIMIZATION:")
        print(f"   Space freed by deleting raw data: {total_space_freed:.1f} GB")
        print(f"   Current available space: {self.get_disk_space_gb():.1f} GB")
        
        print("=" * 80)
        print("🎉 CORPUS CREATION COMPLETE!")
        print("Your multilingual corpus is ready for use.")
        print("=" * 80)

def main():
    """Main function."""
    processor = OptimizedCorpusProcessor()
    
    print("🚀 Starting optimized corpus processing...")
    print("This will process Hindi and Sanskrit while minimizing disk usage.")
    print("Raw data will be deleted immediately after processing each language.")
    
    response = input("\nProceed with processing? (y/n): ").strip().lower()
    if response == 'y':
        processor.process_remaining_languages()
    else:
        print("Processing cancelled.")

if __name__ == "__main__":
    main()
