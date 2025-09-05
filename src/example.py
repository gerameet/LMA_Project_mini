#!/usr/bin/env python3
"""
Example script demonstrating how to use the multilingual corpus downloader
with a small sample for testing purposes.
"""

import os
import sys
from pathlib import Path

# Add the current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from download_data import MultilingualCorpusDownloader

def run_small_sample():
    """Run a small sample download for testing."""
    print("="*60)
    print("MULTILINGUAL CORPUS DOWNLOADER - SAMPLE RUN")
    print("="*60)
    print("This will download a small sample (10K tokens) for testing.")
    print("Full download target: 3 billion tokens")
    print("Note: Using Wikipedia datasets for authentic language data")
    print("="*60)
    
    # Check authentication first
    try:
        from download_data import check_huggingface_auth
        print("🔐 Checking Hugging Face authentication...")
        auth_ok = check_huggingface_auth()
        if not auth_ok:
            print("❌ Authentication required for Wikipedia datasets.")
            print("Please run: huggingface-cli login")
            print("Or get a token from: https://huggingface.co/settings/tokens")
            return
        print("✅ Authentication successful!")
    except Exception as e:
        print(f"⚠️  Authentication check failed: {e}")
        print("Continuing anyway...")
    
    # Create downloader with small target for testing
    downloader = MultilingualCorpusDownloader(
    output_dir="data/sample_corpus",
        target_tokens=10_000  # Very small sample
    )
    
    # Override the dataset config for faster testing with Wikipedia datasets
    test_datasets = {
        'english': [
            {
                'name': 'HuggingFaceFW/fineweb',
                'config': 'sample-10BT',
                'text_column': 'text',
                'streaming': True,
                'description': 'FineWeb English (high-quality web text)'
            }
        ],
        'hindi': [
            {
                'name': 'wikimedia/wikipedia',
                'config': '20231101.hi',
                'text_column': 'text',
                'streaming': True,
                'description': 'Hindi Wikipedia (authentic Hindi text)'
            }
        ],
        'sanskrit': [
            {
                'name': 'wikimedia/wikipedia',
                'config': '20231101.sa',
                'text_column': 'text',
                'streaming': True,
                'description': 'Sanskrit Wikipedia (authentic Sanskrit text)'
            }
        ]
    }
    
    # Override the dataset configuration
    downloader.dataset_config.DATASETS = test_datasets
    
    try:
        print("\nStarting sample download with Wikipedia datasets...")
        print("📝 Note: Hindi and Sanskrit will get authentic Devanagari text!")
        downloader.download_all()
        print("\n🎉 Sample download completed successfully!")
        print("\nSample data saved in: data/sample_corpus/")

        # Check what was actually downloaded
        corpus_dir = Path("data/sample_corpus")
        print("\n📊 LANGUAGE VERIFICATION:")
        for lang in ['english', 'hindi', 'sanskrit']:
            processed_file = corpus_dir / lang / 'processed' / f'{lang}_corpus.txt'
            if processed_file.exists():
                with open(processed_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    total_lines = sum(1 for line in f)
                # Show sample of what was downloaded
                preview = first_line[:100] + "..." if len(first_line) > 100 else first_line
                print(f"  {lang.capitalize()}:")
                print(f"    Lines: {total_lines + 1}")
                print(f"    Sample: {preview}")
                # Language verification
                if lang == 'english':
                    non_ascii_chars = sum(1 for c in first_line if ord(c) > 127)
                    if non_ascii_chars < len(first_line) * 0.1:  # Less than 10% non-ASCII
                        print(f"    ✅ Authentic English content detected")
                    else:
                        print(f"    ⚠️  Contains significant non-ASCII characters")
                elif lang in ['hindi', 'sanskrit']:
                    devanagari_chars = sum(1 for c in first_line if '\u0900' <= c <= '\u097F')
                    total_chars = len([c for c in first_line if c.isalpha()])
                    if devanagari_chars > 0:
                        devanagari_percentage = (devanagari_chars / total_chars * 100) if total_chars > 0 else 0
                        print(f"    ✅ Contains Devanagari script ({devanagari_percentage:.1f}% of alphabetic chars)")
                        print(f"    ✅ Authentic {lang.capitalize()} content detected!")
                    else:
                        print(f"    ⚠️  No Devanagari script detected - may need manual verification")
            else:
                print(f"  {lang.capitalize()}: No processed file found")
        print("\nTo run the full download:")
        print("  python download_data.py")
    except KeyboardInterrupt:
        print("\n\nSample download interrupted by user.")
    except Exception as e:
        print(f"\n❌ Sample download failed: {e}")
        print("This might be due to:")
        print("1. Authentication issues - ensure you're logged in to Hugging Face")
        print("2. Network connectivity issues")
        print("3. Dataset availability")
        print("\nTry:")
        print("  huggingface-cli login")
        print("  python example.py")

def show_usage_examples():
    """Show usage examples for the main script."""
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("="*60)
    
    examples = [
        ("Basic usage (3B tokens)", "python download_data.py"),
        ("Custom token target", "python download_data.py --target-tokens 1000000000"),
        ("Custom output directory", "python download_data.py --output-dir /path/to/corpus"),
        ("Specific languages only", "python download_data.py --languages english hindi"),
        ("Monitor progress", "python monitor_progress.py"),
        ("Monitor with custom interval", "python monitor_progress.py --refresh-interval 60"),
        ("View final statistics", "python monitor_progress.py --final-stats"),
        ("Test setup", "python test_setup.py"),
    ]
    
    for desc, cmd in examples:
        print(f"  {desc}:")
        print(f"    {cmd}")
        print()

def main():
    """Main function with interactive menu."""
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        run_small_sample()
        return
    
    print("="*60)
    print("MULTILINGUAL CORPUS DOWNLOADER")
    print("="*60)
    print("Choose an option:")
    print("1. Run small sample (for testing)")
    print("2. Show usage examples")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == "1":
                run_small_sample()
                break
            elif choice == "2":
                show_usage_examples()
                break
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break

if __name__ == "__main__":
    main()
