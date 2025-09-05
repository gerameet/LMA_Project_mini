#!/usr/bin/env python3
"""
Sanskrit Dataset Explorer
Check available Sanskrit datasets on Hugging Face and estimate token counts.
"""

import sys
import logging
from pathlib import Path

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

try:
    from datasets import load_dataset
    from tqdm import tqdm
    import tiktoken
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please run: pip install datasets tqdm tiktoken")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.WARNING)  # Suppress most logs

def estimate_tokens(text, method='words'):
    """Estimate token count using different methods."""
    if not text:
        return 0
    
    if method == 'words':
        return len(text.split())
    elif method == 'chars':
        return len(text) // 4  # Rough estimate: 4 chars per token
    else:
        # Use tiktoken as fallback
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except:
            return len(text.split())

def check_dataset(name, config=None, text_column='text', sample_size=100):
    """Check a Sanskrit dataset and estimate its size."""
    print(f"\n🔍 Checking: {name}" + (f" (config: {config})" if config else ""))
    
    try:
        # Load dataset
        dataset = load_dataset(name, config, streaming=True, split='train')
        
        sample_texts = []
        total_chars = 0
        sample_count = 0
        
        # Sample some examples
        pbar = tqdm(desc="Sampling", total=sample_size, leave=False)
        
        for example in dataset:
            if sample_count >= sample_size:
                break
                
            text = example.get(text_column, '')
            if text and len(text.strip()) > 0:
                sample_texts.append(text)
                total_chars += len(text)
                sample_count += 1
                pbar.update(1)
        
        pbar.close()
        
        if sample_texts:
            # Calculate statistics
            avg_chars_per_sample = total_chars / len(sample_texts)
            avg_tokens_per_sample = sum(estimate_tokens(text) for text in sample_texts) / len(sample_texts)
            
            print(f"  ✓ Found {len(sample_texts)} samples")
            print(f"  📊 Avg chars per sample: {avg_chars_per_sample:.0f}")
            print(f"  📊 Avg tokens per sample: {avg_tokens_per_sample:.0f}")
            
            # Try to estimate total size (this is rough since we can't know exact dataset size)
            print(f"  📝 Sample texts preview:")
            for i, text in enumerate(sample_texts[:3]):
                preview = text[:100].replace('\n', ' ')
                print(f"    {i+1}. {preview}...")
            
            return {
                'available': True,
                'samples_found': len(sample_texts),
                'avg_tokens': avg_tokens_per_sample,
                'avg_chars': avg_chars_per_sample,
                'sample_texts': sample_texts[:5]  # Keep a few for quality check
            }
        else:
            print(f"  ⚠️  No text found in column '{text_column}'")
            return {'available': False, 'reason': 'no_text_found'}
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {'available': False, 'reason': str(e)}

def main():
    """Check all Sanskrit datasets."""
    print("=" * 60)
    print("SANSKRIT DATASET AVAILABILITY CHECK")
    print("=" * 60)
    print("Checking available Sanskrit datasets on Hugging Face...")
    
    # Sanskrit datasets to check
    sanskrit_datasets = [
        {
            'name': 'wikipedia',
            'config': '20220301.sa',
            'text_column': 'text',
            'description': 'Sanskrit Wikipedia'
        },
        {
            'name': 'rahular/itihasa',
            'config': None,
            'text_column': 'text',
            'description': 'Sanskrit Itihasa texts'
        },
        {
            'name': 'cfilt/HiEn_AnyTask',
            'config': 'classification',
            'text_column': 'text',
            'description': 'Sanskrit classification dataset'
        },
        {
            'name': 'sanskrit_classic',
            'config': None,
            'text_column': 'text',
            'description': 'Classical Sanskrit texts'
        },
        {
            'name': 'ai4bharat/samanantar',
            'config': 'sa',
            'text_column': 'tgt',
            'description': 'Sanskrit parallel corpus'
        }
    ]
    
    available_datasets = []
    total_estimated_tokens = 0
    
    for dataset_info in sanskrit_datasets:
        print(f"\n📚 {dataset_info['description']}")
        result = check_dataset(
            dataset_info['name'],
            dataset_info.get('config'),
            dataset_info['text_column']
        )
        
        if result['available']:
            available_datasets.append({**dataset_info, **result})
            # Rough estimate: assume 1000-10000 samples per dataset
            estimated_total_tokens = result['avg_tokens'] * 5000  # Conservative estimate
            total_estimated_tokens += estimated_total_tokens
            print(f"  📈 Estimated total tokens: ~{estimated_total_tokens:,.0f}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Available datasets: {len(available_datasets)}/{len(sanskrit_datasets)}")
    print(f"Estimated total Sanskrit tokens: ~{total_estimated_tokens:,.0f}")
    print(f"Original target was: 450,000,000 tokens")
    
    if total_estimated_tokens < 450_000_000:
        shortage = 450_000_000 - total_estimated_tokens
        print(f"⚠️  Potential shortage: ~{shortage:,.0f} tokens")
        print("   This is expected - Sanskrit has limited digital resources")
    else:
        print("✅ Estimated available data meets target!")
    
    percentage = (total_estimated_tokens / 3_000_000_000) * 100
    print(f"Estimated Sanskrit percentage of total corpus: {percentage:.2f}%")
    
    if available_datasets:
        print(f"\n📋 RECOMMENDED STRATEGY:")
        print(f"   1. Download all available Sanskrit datasets")
        print(f"   2. Collect ~{total_estimated_tokens:,.0f} tokens (actual may vary)")
        print(f"   3. Adjust English/Hindi targets to compensate if needed")
        print(f"   4. Total corpus will still be close to 3B tokens")
    
    print("\n🚀 Ready to start download with:")
    print("   python download_data.py")

if __name__ == "__main__":
    main()
