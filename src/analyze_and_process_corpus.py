#!/usr/bin/env python3
"""
Raw Data Analysis and Processing Script
Analyzes downloaded corpus data and processes it according to token distribution requirements:
- English: 50% of total tokens
- Mother tongue (Hindi): 30-40% of total tokens  
- Indian language (Sanskrit): 10-20% of total tokens
- Target: At least 3 billion tokens total
"""

import os
import sys
import json
import hashlib
import re
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import random

# External libraries
from tqdm import tqdm
import tiktoken

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('corpus_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RawDataAnalyzer:
    """Analyzes raw corpus data and provides statistics."""
    
    def __init__(self, corpus_dir: str = "data/corpus_data"):
        self.corpus_dir = Path(corpus_dir)
        self.analysis_results = {}
        
        # Initialize tokenizer for accurate token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
            logger.warning("Could not load tiktoken, using word-based approximation")
    
    def count_tokens_fast(self, text: str, language: str) -> int:
        """Fast token counting with language-specific approximations."""
        if not text.strip():
            return 0
        
        if self.tokenizer and language == 'english':
            try:
                return len(self.tokenizer.encode(text))
            except:
                pass
        
        # Fallback to word-based approximation
        word_count = len(text.split())
        if language == 'english':
            return int(word_count * 1.3)
        elif language == 'hindi':
            return int(word_count * 1.8)
        elif language == 'sanskrit':
            return int(word_count * 2.0)
        else:
            return word_count
    
    def analyze_language_directory(self, language: str, sample_size: int = 1000) -> Dict:
        """Analyze raw data for a specific language."""
        lang_dir = self.corpus_dir / language / 'raw'
        
        if not lang_dir.exists():
            logger.warning(f"No raw data directory found for {language}")
            return {
                'language': language,
                'total_files': 0,
                'total_texts': 0,
                'total_tokens': 0,
                'avg_tokens_per_text': 0,
                'file_size_mb': 0,
                'datasets': {}
            }
        
        # Get all text files
        text_files = list(lang_dir.glob('*.txt'))
        total_files = len(text_files)
        
        if total_files == 0:
            logger.warning(f"No text files found for {language}")
            return {
                'language': language,
                'total_files': 0,
                'total_texts': 0,
                'total_tokens': 0,
                'avg_tokens_per_text': 0,
                'file_size_mb': 0,
                'datasets': {}
            }
        
        logger.info(f"Found {total_files:,} files for {language}")
        
        # Calculate total file size
        total_size = sum(f.stat().st_size for f in text_files)
        total_size_mb = total_size / (1024 * 1024)
        
        # Sample files for detailed analysis
        sample_files = random.sample(text_files, min(sample_size, total_files))
        
        # Analyze sample files
        total_texts = 0
        total_tokens = 0
        datasets = defaultdict(lambda: {'files': 0, 'texts': 0, 'tokens': 0})
        
        logger.info(f"Analyzing {len(sample_files)} sample files for {language}...")
        
        for file_path in tqdm(sample_files, desc=f"Analyzing {language}"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split by separator (assuming '=' * 50 separates texts)
                texts = [t.strip() for t in content.split('=' * 50) if t.strip()]
                file_texts = len(texts)
                
                # Count tokens in this file
                file_tokens = 0
                for text in texts:
                    if text:
                        tokens = self.count_tokens_fast(text, language)
                        file_tokens += tokens
                
                total_texts += file_texts
                total_tokens += file_tokens
                
                # Categorize by dataset
                filename = file_path.name
                if 'wikimedia' in filename:
                    dataset_name = 'wikipedia'
                elif 'ai4bharat' in filename:
                    dataset_name = 'ai4bharat_sangraha'
                elif 'allenai' in filename:
                    dataset_name = 'c4'
                elif 'fineweb' in filename:
                    dataset_name = 'fineweb'
                else:
                    dataset_name = 'unknown'
                
                datasets[dataset_name]['files'] += 1
                datasets[dataset_name]['texts'] += file_texts
                datasets[dataset_name]['tokens'] += file_tokens
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        
        # Extrapolate to full dataset
        if len(sample_files) < total_files:
            extrapolation_factor = total_files / len(sample_files)
            total_texts = int(total_texts * extrapolation_factor)
            total_tokens = int(total_tokens * extrapolation_factor)
            
            for dataset_info in datasets.values():
                dataset_info['files'] = int(dataset_info['files'] * extrapolation_factor)
                dataset_info['texts'] = int(dataset_info['texts'] * extrapolation_factor)
                dataset_info['tokens'] = int(dataset_info['tokens'] * extrapolation_factor)
        
        avg_tokens_per_text = total_tokens / total_texts if total_texts > 0 else 0
        
        return {
            'language': language,
            'total_files': total_files,
            'total_texts': total_texts,
            'total_tokens': total_tokens,
            'avg_tokens_per_text': avg_tokens_per_text,
            'file_size_mb': total_size_mb,
            'datasets': dict(datasets),
            'sample_size': len(sample_files),
            'extrapolated': len(sample_files) < total_files
        }
    
    def analyze_all_languages(self) -> Dict:
        """Analyze all languages in the corpus."""
        languages = ['english', 'hindi', 'sanskrit']
        
        print("=" * 80)
        print("RAW CORPUS DATA ANALYSIS")
        print("=" * 80)
        
        results = {}
        total_tokens_across_languages = 0
        
        for language in languages:
            logger.info(f"Analyzing {language} data...")
            results[language] = self.analyze_language_directory(language)
            total_tokens_across_languages += results[language]['total_tokens']
        
        # Calculate percentages
        for language in languages:
            lang_data = results[language]
            if total_tokens_across_languages > 0:
                lang_data['percentage_of_total'] = (lang_data['total_tokens'] / total_tokens_across_languages) * 100
            else:
                lang_data['percentage_of_total'] = 0
        
        results['summary'] = {
            'total_tokens_all_languages': total_tokens_across_languages,
            'total_files_all_languages': sum(r['total_files'] for r in results.values() if isinstance(r, dict) and 'total_files' in r),
            'total_texts_all_languages': sum(r['total_texts'] for r in results.values() if isinstance(r, dict) and 'total_texts' in r),
            'total_size_mb': sum(r['file_size_mb'] for r in results.values() if isinstance(r, dict) and 'file_size_mb' in r),
            'meets_3b_target': total_tokens_across_languages >= 3_000_000_000
        }
        
        self.analysis_results = results
        return results
    
    def print_analysis_report(self):
        """Print a comprehensive analysis report."""
        if not self.analysis_results:
            logger.error("No analysis results available. Run analyze_all_languages() first.")
            return
        
        results = self.analysis_results
        summary = results['summary']
        
        print("\n" + "=" * 80)
        print("CORPUS ANALYSIS REPORT")
        print("=" * 80)
        
        print(f"📊 OVERALL STATISTICS:")
        print(f"   Total tokens: {summary['total_tokens_all_languages']:,}")
        print(f"   Total files:  {summary['total_files_all_languages']:,}")
        print(f"   Total texts:  {summary['total_texts_all_languages']:,}")
        print(f"   Total size:   {summary['total_size_mb']:.1f} MB")
        print(f"   Meets 3B target: {'✅ YES' if summary['meets_3b_target'] else '❌ NO'}")
        
        print(f"\n📈 LANGUAGE BREAKDOWN:")
        target_percentages = {'english': 50, 'hindi': 35, 'sanskrit': 15}
        
        for language in ['english', 'hindi', 'sanskrit']:
            lang_data = results[language]
            target_pct = target_percentages[language]
            actual_pct = lang_data['percentage_of_total']
            
            status = "✅" if abs(actual_pct - target_pct) <= 10 else "⚠️"
            
            print(f"\n   {language.upper()}:")
            print(f"     Files:     {lang_data['total_files']:,}")
            print(f"     Texts:     {lang_data['total_texts']:,}")
            print(f"     Tokens:    {lang_data['total_tokens']:,}")
            print(f"     Avg/text:  {lang_data['avg_tokens_per_text']:.0f} tokens")
            print(f"     Size:      {lang_data['file_size_mb']:.1f} MB")
            print(f"     Current %: {actual_pct:.1f}%")
            print(f"     Target %:  {target_pct}%")
            print(f"     Status:    {status}")
            
            # Dataset breakdown
            if lang_data['datasets']:
                print(f"     Datasets:")
                for dataset, data in lang_data['datasets'].items():
                    pct_of_lang = (data['tokens'] / lang_data['total_tokens']) * 100 if lang_data['total_tokens'] > 0 else 0
                    print(f"       {dataset}: {data['tokens']:,} tokens ({pct_of_lang:.1f}%)")
        
        print(f"\n🎯 TARGET vs ACTUAL:")
        print(f"   English: {results['english']['percentage_of_total']:.1f}% (target: 50%)")
        print(f"   Hindi:   {results['hindi']['percentage_of_total']:.1f}% (target: 30-40%)")
        print(f"   Sanskrit:{results['sanskrit']['percentage_of_total']:.1f}% (target: 10-20%)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        english_tokens = results['english']['total_tokens']
        hindi_tokens = results['hindi']['total_tokens']
        sanskrit_tokens = results['sanskrit']['total_tokens']
        total_tokens = summary['total_tokens_all_languages']
        
        if total_tokens >= 3_000_000_000:
            print(f"   ✅ You have enough data for 3B+ tokens!")
            
            # Calculate optimal distribution
            if english_tokens > total_tokens * 0.6:  # Too much English
                optimal_english = int(total_tokens * 0.5)
                remaining = total_tokens - optimal_english
                optimal_hindi = int(remaining * 0.7)  # 35% of total
                optimal_sanskrit = remaining - optimal_hindi
                
                print(f"   📊 Suggested processing distribution:")
                print(f"      English:  {optimal_english:,} tokens (50%)")
                print(f"      Hindi:    {optimal_hindi:,} tokens ({optimal_hindi/total_tokens*100:.1f}%)")
                print(f"      Sanskrit: {optimal_sanskrit:,} tokens ({optimal_sanskrit/total_tokens*100:.1f}%)")
            else:
                print(f"   📊 Current distribution is reasonable for processing")
        else:
            shortage = 3_000_000_000 - total_tokens
            print(f"   ⚠️  Need {shortage:,} more tokens to reach 3B target")
            print(f"   💡 Consider downloading more data or using all available data")
        
        print("=" * 80)
    
    def save_analysis_results(self, output_file: str = "raw_data_analysis.json"):
        """Save analysis results to JSON file."""
        if not self.analysis_results:
            logger.error("No analysis results to save")
            return
        
        output_path = self.corpus_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        logger.info(f"Analysis results saved to {output_path}")

class CorpusProcessor:
    """Processes raw corpus data according to target distribution."""
    
    def __init__(self, corpus_dir: str = "data/corpus_data", target_tokens: int = 3_000_000_000):
        self.corpus_dir = Path(corpus_dir)
        self.target_tokens = target_tokens
        
        # Target distribution
        self.targets = {
            'english': int(target_tokens * 0.5),      # 50%
            'hindi': int(target_tokens * 0.35),       # 35%
            'sanskrit': int(target_tokens * 0.15)     # 15%
        }
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
            logger.warning("Could not load tiktoken, using approximation")
        
        # Setup directories
        self.final_dir = self.corpus_dir / 'final_corpus'
        self.final_dir.mkdir(exist_ok=True)
    
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
    
    def process_language_data(self, language: str, target_tokens: int) -> Dict:
        """Process raw data for a specific language according to target."""
        raw_dir = self.corpus_dir / language / 'raw'
        processed_dir = self.corpus_dir / language / 'processed'
        processed_dir.mkdir(exist_ok=True)
        
        if not raw_dir.exists():
            logger.error(f"No raw data found for {language}")
            return {'processed_tokens': 0, 'processed_texts': 0}
        
        text_files = list(raw_dir.glob('*.txt'))
        if not text_files:
            logger.error(f"No text files found for {language}")
            return {'processed_tokens': 0, 'processed_texts': 0}
        
        logger.info(f"Processing {len(text_files)} files for {language}")
        logger.info(f"Target: {target_tokens:,} tokens")
        
        # Shuffle files for random sampling
        random.shuffle(text_files)
        
        processed_texts = []
        total_tokens = 0
        seen_hashes = set()
        
        pbar = tqdm(total=target_tokens, desc=f"Processing {language}", unit="tokens")
        
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
                    
                    processed_texts.append(text)
                    total_tokens += tokens
                    pbar.update(tokens)
                    
                    # Stop if we've reached the target
                    if total_tokens >= target_tokens:
                        break
                        
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        
        pbar.close()
        
        # Save processed corpus
        output_file = processed_dir / f"{language}_corpus.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for text in processed_texts:
                f.write(text + '\n\n')
        
        # Save to final corpus directory too
        final_file = self.final_dir / f"{language}_corpus.txt"
        with open(final_file, 'w', encoding='utf-8') as f:
            for text in processed_texts:
                f.write(text + '\n\n')
        
        # Save metadata
        metadata = {
            'language': language,
            'target_tokens': target_tokens,
            'actual_tokens': total_tokens,
            'total_texts': len(processed_texts),
            'completion_rate': (total_tokens / target_tokens) * 100 if target_tokens > 0 else 0,
            'avg_tokens_per_text': total_tokens / len(processed_texts) if processed_texts else 0,
            'deduplication_ratio': len(seen_hashes) / (len(seen_hashes) + len(processed_texts)) if processed_texts else 0
        }
        
        metadata_file = processed_dir / f"{language}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Processed {language}: {total_tokens:,} tokens, {len(processed_texts):,} texts")
        
        return {
            'processed_tokens': total_tokens,
            'processed_texts': len(processed_texts),
            'metadata': metadata
        }
    
    def process_all_languages(self):
        """Process all languages according to target distribution."""
        print("\n" + "=" * 80)
        print("CORPUS PROCESSING")
        print("=" * 80)
        print(f"Target: {self.target_tokens:,} total tokens")
        print(f"Distribution: English 50%, Hindi 35%, Sanskrit 15%")
        print("=" * 80)
        
        results = {}
        
        for language, target in self.targets.items():
            print(f"\n--- Processing {language.upper()} ---")
            results[language] = self.process_language_data(language, target)
        
        # Generate final report
        total_processed = sum(r['processed_tokens'] for r in results.values())
        
        print(f"\n" + "=" * 80)
        print("PROCESSING COMPLETE")
        print("=" * 80)
        print(f"Total processed tokens: {total_processed:,}")
        print(f"Target tokens: {self.target_tokens:,}")
        print(f"Completion rate: {(total_processed/self.target_tokens)*100:.1f}%")
        
        for language, result in results.items():
            target = self.targets[language]
            actual = result['processed_tokens']
            percentage = (actual / total_processed) * 100 if total_processed > 0 else 0
            
            print(f"\n{language.capitalize()}:")
            print(f"  Processed: {actual:,} tokens ({percentage:.1f}%)")
            print(f"  Target:    {target:,} tokens")
            print(f"  Texts:     {result['processed_texts']:,}")
            print(f"  Status:    {'✅ Complete' if actual >= target * 0.9 else '⚠️ Partial'}")
        
        print("=" * 80)
        print(f"📁 Processed files saved to: {self.final_dir}")
        print("=" * 80)

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Analyze and process multilingual corpus")
    parser.add_argument("--corpus-dir", default="data/corpus_data", help="Corpus data directory")
    parser.add_argument("--target-tokens", type=int, default=3_000_000_000, help="Target total tokens")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze, don't process")
    parser.add_argument("--process-only", action="store_true", help="Only process, don't analyze")
    
    args = parser.parse_args()
    
    if not args.process_only:
        # Analyze raw data
        analyzer = RawDataAnalyzer(args.corpus_dir)
        analyzer.analyze_all_languages()
        analyzer.print_analysis_report()
        analyzer.save_analysis_results()
    
    if not args.analyze_only:
        # Process data according to targets
        print("\n" + "=" * 50)
        user_input = input("Do you want to proceed with processing? (y/n): ").strip().lower()
        if user_input == 'y':
            processor = CorpusProcessor(args.corpus_dir, args.target_tokens)
            processor.process_all_languages()
        else:
            print("Processing skipped.")

if __name__ == "__main__":
    main()
