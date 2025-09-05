#!/usr/bin/env python3
"""
Test actual access to AI4Bharat Sangraha splits.
"""

from datasets import load_dataset

def test_actual_splits():
    """Test the actual splits that work."""
    
    print("="*80)
    print("TESTING ACTUAL AI4BHARAT SANGRAHA SPLITS")
    print("="*80)
    
    # Test cases based on available splits
    test_cases = [
        # Verified config
        ("verified", "san"),
        ("verified", "hin"),
        
        # Synthetic config
        ("synthetic", "san_Deva"),
        ("synthetic", "san_Latn"), 
        ("synthetic", "hin_Deva"),
        ("synthetic", "hin_Latn"),
    ]
    
    for config, split in test_cases:
        print(f"\n--- {config.upper()}/{split.upper()} ---")
        try:
            # Load small sample using streaming
            dataset = load_dataset(
                "ai4bharat/sangraha",
                config,
                split=split,
                streaming=True
            )
            
            print(f"✅ Split exists and accessible")
            
            # Get first few samples
            samples = []
            for i, example in enumerate(dataset):
                if i >= 3:  # Just get 3 samples
                    break
                samples.append(example)
            
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
                
                preview = text[:100] + '...' if len(text) > 100 else text
                print(f"  {i+1}. {preview}")
                print(f"      Length: {len(text)} chars {script_info}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def count_examples():
    """Try to estimate dataset sizes."""
    
    print(f"\n{'='*60}")
    print("ESTIMATING DATASET SIZES")
    print("="*60)
    
    configs_to_test = [
        ("verified", "san"),
        ("verified", "hin"),
        ("synthetic", "san_Deva"),
        ("synthetic", "hin_Deva"),
    ]
    
    for config, split in configs_to_test:
        print(f"\n{config}/{split}:")
        try:
            # Load with streaming and count first 1000
            dataset = load_dataset(
                "ai4bharat/sangraha",
                config,
                split=split,
                streaming=True
            )
            
            count = 0
            total_chars = 0
            
            for example in dataset:
                count += 1
                text = example.get('text', '')
                total_chars += len(text)
                
                if count >= 1000:  # Stop after 1000 to get estimate
                    break
            
            avg_chars = total_chars / count if count > 0 else 0
            print(f"  First {count} examples:")
            print(f"  Average text length: {avg_chars:.0f} characters")
            print(f"  Estimated tokens per text: {avg_chars/4:.0f}")  # Rough estimate
            
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_actual_splits()
    count_examples()
