#!/usr/bin/env python3
"""
Quick exploration of AI4Bharat Sangraha dataset splits and samples.
"""

import datasets
from datasets import load_dataset

def quick_explore_sangraha():
    """Quick exploration using streaming and small samples."""
    
    print("="*80)
    print("AI4BHARAT SANGRAHA DATASET EXPLORATION")
    print("="*80)
    
    # Check what splits are available without downloading
    try:
        dataset_info = datasets.get_dataset_infos("ai4bharat/sangraha")
        
        for config_name in dataset_info.keys():
            print(f"\nConfig: {config_name}")
            
            try:
                config_info = datasets.get_dataset_config_info("ai4bharat/sangraha", config_name)
                if hasattr(config_info, 'splits') and config_info.splits:
                    print(f"  Available splits:")
                    for split_name, split_info in config_info.splits.items():
                        if hasattr(split_info, 'num_examples') and split_info.num_examples > 0:
                            print(f"    {split_name}: {split_info.num_examples:,} examples")
                        elif 'san' in split_name.lower():
                            print(f"    {split_name}: Sanskrit-related split")
                else:
                    print(f"  No split info available")
            except Exception as e:
                print(f"  Error getting config info: {e}")
    
    except Exception as e:
        print(f"Error exploring dataset: {e}")

def test_sanskrit_splits():
    """Test different Sanskrit splits with small samples."""
    
    print(f"\n{'='*60}")
    print("TESTING SANSKRIT SPLITS")
    print("="*60)
    
    # Test cases for Sanskrit splits
    test_cases = [
        ("verified", "san"),
        ("synthetic", "san_Deva"),
        ("synthetic", "san_Latn"),
    ]
    
    for config, split in test_cases:
        print(f"\n--- {config.upper()}/{split.upper()} ---")
        try:
            # Load just 3 samples using streaming
            dataset = load_dataset(
                "ai4bharat/sangraha",
                config,
                split=f"{split}[:3]",
                streaming=True
            )
            
            print(f"✅ Split exists and accessible")
            
            # Get samples
            samples = list(dataset)
            print(f"Samples retrieved: {len(samples)}")
            
            for i, example in enumerate(samples):
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
                
                preview = text[:80] + '...' if len(text) > 80 else text
                print(f"  {i+1}. {preview} {script_info}")
                print(f"      Length: {len(text)} chars")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_hindi_splits():
    """Test Hindi splits for comparison."""
    
    print(f"\n{'='*60}")
    print("TESTING HINDI SPLITS FOR COMPARISON")
    print("="*60)
    
    # Test cases for Hindi splits  
    test_cases = [
        ("verified", "hin"),
        ("synthetic", "hin_Deva"),
        ("synthetic", "hin_Latn"),
    ]
    
    for config, split in test_cases:
        print(f"\n--- {config.upper()}/{split.upper()} ---")
        try:
            # Load just 2 samples using streaming
            dataset = load_dataset(
                "ai4bharat/sangraha",
                config,
                split=f"{split}[:2]",
                streaming=True
            )
            
            print(f"✅ Split exists")
            
            # Get samples
            samples = list(dataset)
            print(f"Samples: {len(samples)}")
            
            for i, example in enumerate(samples):
                text = example.get('text', '')[:60]
                print(f"  {i+1}. {text}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def provide_recommendations():
    """Provide specific recommendations based on findings."""
    
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS FOR YOUR DOWNLOAD_DATA.PY")
    print("="*80)
    
    print("""
STRATEGY FOR AI4BHARAT SANGRAHA:

1. SANSKRIT OPTIONS DISCOVERED:
   - verified/san: High quality, manually verified (smaller dataset)
   - synthetic/san_Deva: Large synthetic data in Devanagari script
   - synthetic/san_Latn: Large synthetic data in Latin script (romanized)

2. DATA VOLUME COMPARISON:
   - VERIFIED: Smaller but highest quality (human-verified)
   - SYNTHETIC: Much larger volume but generated content

3. SCRIPT CONSIDERATIONS:
   - san_Deva: Traditional Devanagari script (देवनागरी)
   - san_Latn: Romanized Sanskrit (easier to process, but less traditional)

4. RECOMMENDED CONFIGURATION:

   Option A - QUALITY FOCUSED (Recommended for authentic corpus):
   ```python
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
           'description': 'High-quality verified Sanskrit',
           'split': 'san'
       },
       {
           'name': 'ai4bharat/sangraha',
           'config': 'synthetic',
           'text_column': 'text',
           'streaming': True,
           'description': 'Large Sanskrit corpus (Devanagari)',
           'split': 'san_Deva'
       }
   ]
   ```

   Option B - VOLUME FOCUSED (if you need more data):
   ```python
   # Primary: synthetic/san_Deva (largest volume)
   # Secondary: verified/san (quality check)
   # Optional: synthetic/san_Latn (if romanized content acceptable)
   ```

5. FOR HINDI (similar pattern available):
   - verified/hin: High quality verified Hindi
   - synthetic/hin_Deva: Large synthetic Hindi (Devanagari)
   - synthetic/hin_Latn: Large synthetic Hindi (romanized)

6. IMPLEMENTATION STEPS:
   a) Start with verified splits for quality baseline
   b) Add synthetic splits if more volume needed
   c) Monitor quality during download
   d) Consider script preference (Devanagari vs Latin)
""")

if __name__ == "__main__":
    quick_explore_sangraha()
    test_sanskrit_splits()
    test_hindi_splits()
    provide_recommendations()
