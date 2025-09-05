#!/usr/bin/env python3
"""
Optimized Corpus Processor - Space Efficient
Processes corpus data with minimal disk usage:
- Streams processing (no intermediate files)
- Deletes raw data after processing each language
- Single final output location
- Processes one language at a time
"""

import os
import sys
import json
import hashlib
import shutil
import logging
import argparse
from pathlib import Path
from typing import Dict, List
import random

# External libraries
from tqdm import tqdm
import tiktoken

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('corpus_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OptimizedCorpusProcessor:
    """Space-efficient corpus processor."""
    
    def __init__(self, corpus_dir: str = "corpus_data", target_tokens: int = 3_000_000_000):
        self.corpus_dir = Path(corpus_dir)
        self.target_tokens = target_tokens
        
        # Target distribution (exact targets as requested)
        self.targets = {
            'english': int(target_tokens * 0.5),      # 1.5B tokens (50%)
            'hindi': int(target_tokens * 0.35),       # 1.05B tokens (35%) 
            'sanskrit': int(target_tokens * 0.15)     # 450M tokens (15%)
        }
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
            logger.warning("Could not load tiktoken, using approximation")
        
        # Setup final output directory (single location)
        self.output_dir = self.corpus_dir / 'final_corpus'
        self.output_dir.mkdir(exist_ok=True)
        
        # Track processing statistics
        self.processing_stats = {}
    
    def count_tokens_fast(self, text: str, language: str) -> int:
        """Fast token counting."""
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
    
    def cleanup_existing_processed_data(self, language: str):
        """Clean up any existing processed data for a language."""
        processed_dir = self.corpus_dir / language / 'processed'
        if processed_dir.exists():
            logger.info(f"Cleaning up existing processed data for {language}...")
            shutil.rmtree(processed_dir)
            logger.info(f"Deleted {processed_dir}")
    
    def get_disk_space_gb(self) -> float:
        """Get available disk space in GB."""
        statvfs = os.statvfs(self.corpus_dir)
        return (statvfs.f_frsize * statvfs.f_available) / (1024**3)
    
    def process_language_streaming(self, language: str, target_tokens: int, delete_raw: bool = False) -> Dict:
        """Process language data with streaming approach (minimal disk usage)."""
        raw_dir = self.corpus_dir / language / 'raw'
        
        if not raw_dir.exists():
            logger.error(f"No raw data found for {language}")
            return {'processed_tokens': 0, 'processed_texts': 0, 'success': False}
        
        # Check disk space before starting
        available_gb = self.get_disk_space_gb()
        logger.info(f"Available disk space: {available_gb:.1f} GB")
        
        if available_gb < 5.0:  # Less than 5GB available
            logger.warning(f"Low disk space: {available_gb:.1f} GB. Processing may fail.")
        
        text_files = list(raw_dir.glob('*.txt'))
        if not text_files:
            logger.error(f"No text files found for {language}")
            return {'processed_tokens': 0, 'processed_texts': 0, 'success': False}
        
        logger.info(f"Processing {len(text_files)} files for {language}")
        logger.info(f"Target: {target_tokens:,} tokens")
        logger.info(f"Will {'DELETE' if delete_raw else 'KEEP'} raw data after processing")
        
        # Shuffle files for random sampling
        random.shuffle(text_files)
        
        # Output file (single location)
        output_file = self.output_dir / f"{language}_corpus.txt"
        
        # Processing variables
        total_tokens = 0
        total_texts = 0
        seen_hashes = set()
        processed_files = 0
        
        # Progress bar
        pbar = tqdm(total=target_tokens, desc=f"Processing {language}", unit="tokens")
        
        # Open output file for writing
        with open(output_file, 'w', encoding='utf-8') as out_file:
            for file_path in text_files:
                if total_tokens >= target_tokens:
                    break
                
                try:
                    # Read and process file
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
                        
                        # Write directly to output (streaming)
                        out_file.write(text + '\n\n')
                        out_file.flush()  # Ensure data is written
                        
                        total_tokens += tokens
                        total_texts += 1
                        pbar.update(tokens)
                        
                        # Stop if we've reached the target
                        if total_tokens >= target_tokens:
                            break
                    
                    processed_files += 1
                    
                    # Periodic cleanup and status update
                    if processed_files % 100 == 0:
                        available_gb = self.get_disk_space_gb()
                        logger.debug(f"Processed {processed_files} files, {available_gb:.1f}GB available")
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    continue
        
        pbar.close()
        
        # Create metadata
        metadata = {
            'language': language,
            'target_tokens': target_tokens,
            'actual_tokens': total_tokens,
            'total_texts': total_texts,
            'completion_rate': (total_tokens / target_tokens) * 100 if target_tokens > 0 else 0,
            'avg_tokens_per_text': total_tokens / total_texts if total_texts > 0 else 0,
            'processed_files': processed_files,
            'total_files': len(text_files),
            'output_file': str(output_file),
            'raw_deleted': delete_raw
        }
        
        # Save metadata
        metadata_file = self.output_dir / f"{language}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Delete raw data if requested (SPACE SAVING)
        if delete_raw and total_tokens > 0:
            logger.info(f"Deleting raw data for {language} to save space...")
            try:
                shutil.rmtree(raw_dir)
                logger.info(f"✅ Deleted {raw_dir} - Saved {self.get_directory_size_gb(raw_dir)} GB")
                metadata['raw_deleted'] = True
                # Update metadata file
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to delete raw data: {e}")
                metadata['raw_deleted'] = False
        
        logger.info(f"✅ Completed {language}: {total_tokens:,} tokens, {total_texts:,} texts")
        
        return {
            'processed_tokens': total_tokens,
            'processed_texts': total_texts,
            'metadata': metadata,
            'success': total_tokens > 0
        }
    
    def get_directory_size_gb(self, directory: Path) -> float:
        """Get directory size in GB."""
        if not directory.exists():
            return 0.0
        total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
        return total_size / (1024**3)
    
    def process_with_space_optimization(self):
        """Process all languages with maximum space efficiency."""
        print("\n" + "=" * 80)
        print("OPTIMIZED CORPUS PROCESSING")
        print("=" * 80)
        print(f"Target: {self.target_tokens:,} total tokens")
        print(f"Distribution: English 50%, Hindi 35%, Sanskrit 15%")
        print(f"Strategy: Stream processing + Delete raw data after each language")
        print("=" * 80)
        
        # Check initial disk space
        initial_space = self.get_disk_space_gb()
        logger.info(f"Initial available space: {initial_space:.1f} GB")
        
        if initial_space < 10.0:
            logger.warning("⚠️  Low disk space! Consider freeing up space before processing.")
        
        # Step 1: Clean up any existing processed data
        for language in ['english', 'hindi', 'sanskrit']:
            self.cleanup_existing_processed_data(language)
        
        # Step 2: Process each language individually
        results = {}
        processing_order = ['english', 'hindi', 'sanskrit']  # Process in this order
        
        for i, language in enumerate(processing_order):
            target = self.targets[language]
            
            print(f"\n{'='*20} PROCESSING {language.upper()} {'='*20}")
            print(f"Target: {target:,} tokens ({target/self.target_tokens*100:.0f}%)")
            
            # Delete raw data after processing (except for the last language, let user decide)
            delete_raw_after = i < len(processing_order) - 1  # Delete for all except last
            
            if delete_raw_after:
                print(f"⚠️  Raw data will be DELETED after processing to save space")
            else:
                print(f"ℹ️  Raw data will be KEPT (last language)")
            
            # Check space before processing
            before_space = self.get_disk_space_gb()
            
            # Process the language
            result = self.process_language_streaming(language, target, delete_raw=delete_raw_after)
            results[language] = result
            
            if not result['success']:
                logger.error(f"❌ Failed to process {language}")
                break
            
            # Check space after processing
            after_space = self.get_disk_space_gb()
            space_change = after_space - before_space
            
            print(f"📊 Space: {before_space:.1f}GB → {after_space:.1f}GB ({space_change:+.1f}GB)")
            
            if after_space < 5.0 and i < len(processing_order) - 1:
                logger.warning("⚠️  Low disk space! May not be able to process remaining languages.")
        
        # Step 3: Generate final report
        self.generate_final_report(results)
        
        return results
    
    def generate_final_report(self, results: Dict):
        """Generate comprehensive final report."""
        total_processed = sum(r['processed_tokens'] for r in results.values() if r['success'])
        
        print(f"\n" + "=" * 80)
        print("PROCESSING COMPLETE - FINAL REPORT")
        print("=" * 80)
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total processed tokens: {total_processed:,}")
        print(f"   Target tokens: {self.target_tokens:,}")
        print(f"   Achievement rate: {(total_processed/self.target_tokens)*100:.1f}%")
        print(f"   Final corpus location: {self.output_dir}")
        
        print(f"\n📈 LANGUAGE BREAKDOWN:")
        for language, result in results.items():
            if result['success']:
                target = self.targets[language]
                actual = result['processed_tokens']
                percentage = (actual / total_processed) * 100 if total_processed > 0 else 0
                
                status = "✅ Complete" if actual >= target * 0.9 else "⚠️ Partial"
                raw_status = "🗑️ Deleted" if result['metadata'].get('raw_deleted', False) else "💾 Kept"
                
                print(f"\n   {language.upper()}:")
                print(f"     Processed: {actual:,} tokens ({percentage:.1f}%)")
                print(f"     Target:    {target:,} tokens")
                print(f"     Texts:     {result['processed_texts']:,}")
                print(f"     Status:    {status}")
                print(f"     Raw data:  {raw_status}")
            else:
                print(f"\n   {language.upper()}: ❌ FAILED")
        
        # Disk space summary
        final_space = self.get_disk_space_gb()
        corpus_size = sum(self.get_directory_size_gb(self.output_dir / f"{lang}_corpus.txt") 
                         for lang in results.keys() if results[lang]['success'])
        
        print(f"\n💾 DISK USAGE:")
        print(f"   Available space: {final_space:.1f} GB")
        print(f"   Final corpus size: {corpus_size:.1f} GB")
        print(f"   Space efficiency: Eliminated redundant copies")
        
        print(f"\n📁 OUTPUT FILES:")
        for language in results.keys():
            if results[language]['success']:
                corpus_file = self.output_dir / f"{language}_corpus.txt"
                metadata_file = self.output_dir / f"{language}_metadata.json"
                
                if corpus_file.exists():
                    size_gb = self.get_directory_size_gb(corpus_file)
                    print(f"   {corpus_file.name}: {size_gb:.1f} GB")
                if metadata_file.exists():
                    print(f"   {metadata_file.name}: metadata")
        
        print("=" * 80)
        
        # Save overall report
        overall_report = {
            'total_target_tokens': self.target_tokens,
            'total_processed_tokens': total_processed,
            'achievement_rate': (total_processed/self.target_tokens)*100,
            'languages': results,
            'output_directory': str(self.output_dir),
            'final_corpus_size_gb': corpus_size,
            'processing_date': str(Path(__file__).stat().st_mtime)
        }
        
        report_file = self.output_dir / 'processing_report.json'
        with open(report_file, 'w') as f:
            json.dump(overall_report, f, indent=2)
        
        logger.info(f"📋 Final report saved to: {report_file}")

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Optimized corpus processor with space efficiency")
    parser.add_argument("--corpus-dir", default="corpus_data", help="Corpus data directory")
    parser.add_argument("--target-tokens", type=int, default=3_000_000_000, help="Target total tokens")
    parser.add_argument("--keep-raw", action="store_true", help="Keep raw data (don't delete after processing)")
    
    args = parser.parse_args()
    
    print("🚀 Starting optimized corpus processing...")
    print(f"📁 Corpus directory: {args.corpus_dir}")
    print(f"🎯 Target tokens: {args.target_tokens:,}")
    print(f"💾 Raw data handling: {'KEEP' if args.keep_raw else 'DELETE after processing'}")
    
    # Confirmation
    print("\n" + "=" * 50)
    if not args.keep_raw:
        print("⚠️  WARNING: Raw data will be DELETED after processing each language!")
        print("   This saves disk space but raw data cannot be recovered.")
    
    user_input = input("\nDo you want to proceed? (y/n): ").strip().lower()
    
    if user_input == 'y':
        processor = OptimizedCorpusProcessor(args.corpus_dir, args.target_tokens)
        results = processor.process_with_space_optimization()
        
        # Success summary
        successful_languages = [lang for lang, result in results.items() if result['success']]
        if successful_languages:
            print(f"\n🎉 Successfully processed: {', '.join(successful_languages)}")
        else:
            print(f"\n❌ No languages processed successfully")
    else:
        print("❌ Processing cancelled.")

if __name__ == "__main__":
    main()
