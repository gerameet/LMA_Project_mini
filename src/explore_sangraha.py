#!/usr/bin/env python3
"""
Explore AI4Bharat Sangraha dataset structure to understand splits and data volumes.
"""

import datasets
from datasets import load_dataset
from collections import defaultdict
import json

def explore_sangraha_dataset():
    """Explore the complete structure of AI4Bharat Sangraha dataset."""
    
    print("="*80)
    print("EXPLORING AI4BHARAT SANGRAHA DATASET")
    print("="*80)
    
    try:
        # Load dataset info without downloading
        dataset_info = datasets.get_dataset_infos("ai4bharat/sangraha")
        
        print("Available configs:")
        for config_name, info in dataset_info.items():
            print(f"  - {config_name}")
            if hasattr(info, 'splits') and info.splits:
                for split_name, split_info in info.splits.items():
                    if hasattr(split_info, 'num_examples'):
                        print(f"    └─ {split_name}: {split_info.num_examples:,} examples")
                    else:
                        print(f"    └─ {split_name}: size unknown")
        
        print(f"\n{'='*60}")
        print("DETAILED EXPLORATION OF 'verified' CONFIG")
        print("="*60)
        
        # Load just the verified config to see all splits
        try:
            dataset = load_dataset("ai4bharat/sangraha", "verified", streaming=False)
            
            print("Available splits in 'verified' config:")
            total_examples = 0
            
            for split_name in dataset.keys():
                split_size = len(dataset[split_name])
                total_examples += split_size
                print(f"  {split_name}: {split_size:,} examples")
                
                # Show sample for language-specific splits
                if split_name in ['san', 'san_Deva', 'san_Latn', 'hin']:
                    sample = dataset[split_name][0] if split_size > 0 else None
                    if sample:
                        text = sample.get('text', '')
                        preview = text[:100] + '...' if len(text) > 100 else text
                        print(f"    Sample: {preview}")
                        print(f"    Text length: {len(text)} chars")
            
            print(f"\nTotal verified examples: {total_examples:,}")
            
        except Exception as e:
            print(f"Error loading verified config: {e}")
        
        print(f"\n{'='*60}")
        print("EXPLORING 'synthetic' CONFIG")
        print("="*60)
        
        # Check synthetic config
        try:
            # Just peek at the splits without loading all data
            synthetic_info = datasets.get_dataset_config_info("ai4bharat/sangraha", "synthetic")
            
            print("Available splits in 'synthetic' config:")
            if hasattr(synthetic_info, 'splits') and synthetic_info.splits:
                synthetic_total = 0
                for split_name, split_info in synthetic_info.splits.items():
                    if hasattr(split_info, 'num_examples'):
                        size = split_info.num_examples
                        synthetic_total += size
                        print(f"  {split_name}: {size:,} examples")
                    else:
                        print(f"  {split_name}: size unknown")
                
                print(f"\nTotal synthetic examples: {synthetic_total:,}")
                
                # Load small sample from synthetic Sanskrit splits
                print(f"\n{'='*40}")
                print("SYNTHETIC SANSKRIT SAMPLES")
                print("="*40)
                
                for san_split in ['san', 'san_Deva', 'san_Latn']:
                    try:
                        sample_dataset = load_dataset(
                            "ai4bharat/sangraha", 
                            "synthetic", 
                            split=f"{san_split}[:5]",  # Just first 5 examples
                            streaming=False
                        )
                        
                        print(f"\n{san_split.upper()} samples:")
                        for i, example in enumerate(sample_dataset):
                            text = example.get('text', '')
                            preview = text[:80] + '...' if len(text) > 80 else text
                            print(f"  {i+1}. {preview}")
                            
                    except Exception as e:
                        print(f"  {san_split}: Error - {e}")
            
        except Exception as e:
            print(f"Error exploring synthetic config: {e}")
        
    except Exception as e:
        print(f"Error exploring dataset: {e}")

def compare_sanskrit_quality():
    """Compare quality between verified and synthetic Sanskrit data."""
    
    print(f"\n{'='*60}")
    print("QUALITY COMPARISON: VERIFIED vs SYNTHETIC")
    print("="*60)
    
    configs_splits = [
        ("verified", "san"),
        ("synthetic", "san"),
        ("synthetic", "san_Deva"), 
        ("synthetic", "san_Latn")
    ]
    
    for config, split in configs_splits:
        print(f"\n--- {config.upper()}/{split.upper()} ---")
        try:
            # Load small sample
            sample = load_dataset(
                "ai4bharat/sangraha",
                config,
                split=f"{split}[:3]",
                streaming=False
            )
            
            for i, example in enumerate(sample):
                text = example.get('text', '')
                
                # Analyze script
                devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
                latin_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
                total_alpha = sum(1 for c in text if c.isalpha())
                
                script_info = ""
                if total_alpha > 0:
                    dev_ratio = devanagari_chars / total_alpha
                    lat_ratio = latin_chars / total_alpha
                    script_info = f"(Dev: {dev_ratio:.1%}, Lat: {lat_ratio:.1%})"
                
                preview = text[:100] + '...' if len(text) > 100 else text
                print(f"  {i+1}. {preview} {script_info}")
                
        except Exception as e:
            print(f"  Error: {e}")

def recommend_strategy():
    """Provide recommendations based on findings."""
    
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print("="*80)
    
    print("""
SANSKRIT DATA STRATEGY:

1. SCRIPT VARIANTS:
   - san_Deva: Sanskrit in Devanagari script (traditional)
   - san_Latn: Sanskrit in Latin script (romanized)
   - san: Mixed or default script

2. DATA VOLUME:
   - synthetic: Much larger dataset (potentially millions of examples)
   - verified: Smaller but manually curated/verified

3. RECOMMENDED APPROACH:
   
   Option A - QUALITY FIRST (Recommended):
   - Primary: verified/san (highest quality)
   - Secondary: synthetic/san_Deva (large volume, Devanagari)
   - Tertiary: synthetic/san_Latn (if needed for romanized Sanskrit)
   
   Option B - VOLUME FIRST:
   - Primary: synthetic/san_Deva (large volume)
   - Secondary: verified/san (quality check)
   - Include both Devanagari and Latin if script diversity needed
   
   Option C - COMPREHENSIVE:
   - Use both verified and synthetic
   - Include both Devanagari and Latin scripts
   - Apply quality filtering during processing

4. IMPLEMENTATION:
   - Start with verified data for quality baseline
   - Add synthetic data if more volume needed
   - Consider separate handling for Devanagari vs Latin scripts
   - Monitor quality during download and adjust accordingly
""")

if __name__ == "__main__":
    explore_sangraha_dataset()
    compare_sanskrit_quality()
    recommend_strategy()
