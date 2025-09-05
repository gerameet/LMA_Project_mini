#!/usr/bin/env python3
"""
Test script to verify that all dependencies are properly installed
and the basic functionality works before starting the full download.
"""

import sys
import importlib
import warnings
warnings.filterwarnings("ignore")

def test_import(module_name, description):
    """Test if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✓ {description}")
        return True
    except ImportError as e:
        print(f"✗ {description} - Error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of the corpus downloader."""
    print("Testing basic functionality...")
    
    try:
        # Test tokenizer initialization
        from download_data import TokenCounter
        counter = TokenCounter()
        
        # Test token counting
        test_text = "This is a test sentence for token counting."
        tokens = counter.count_tokens(test_text, 'english')
        print(f"✓ Token counting works: '{test_text}' = {tokens} tokens")
        
        # Test text preprocessing
        from download_data import TextPreprocessor
        preprocessor = TextPreprocessor()
        
        cleaned = preprocessor.clean_text("  This is a test!  ", 'english')
        print(f"✓ Text cleaning works: cleaned to '{cleaned}'")
        
        # Test segmentation
        segments = preprocessor.segment_text("First sentence. Second sentence! Third question?", 'english')
        print(f"✓ Text segmentation works: {len(segments)} segments")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def test_huggingface_access():
    """Test Hugging Face datasets access."""
    print("Testing Hugging Face access...")
    
    try:
        from datasets import load_dataset
        
        # Test with a very small dataset
        print("  Attempting to load a small test dataset...")
        ds = load_dataset("squad", split="train[:1]")
        print(f"✓ Hugging Face access works: loaded {len(ds)} example(s)")
        return True
        
    except Exception as e:
        print(f"✗ Hugging Face access failed: {e}")
        print("  You may need to run: huggingface-cli login")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("MULTILINGUAL CORPUS DOWNLOADER - DEPENDENCY TEST")
    print("="*60)
    
    # Test core dependencies
    print("\n1. Testing Python package imports...")
    required_modules = [
        ("datasets", "Hugging Face Datasets"),
        ("transformers", "Hugging Face Transformers"),
        ("tiktoken", "TikToken (OpenAI tokenizer)"),
        ("nltk", "Natural Language Toolkit"),
        ("tqdm", "Progress bars"),
        ("numpy", "NumPy"),
    ]
    
    all_imports_ok = True
    for module, desc in required_modules:
        if not test_import(module, desc):
            all_imports_ok = False
    
    # Test optional dependencies
    print("\n2. Testing optional dependencies...")
    optional_modules = [
        ("spacy", "spaCy (advanced NLP)"),
        ("pandas", "Pandas (data manipulation)"),
    ]
    
    for module, desc in optional_modules:
        test_import(module, f"{desc} (optional)")
    
    if not all_imports_ok:
        print("\n❌ Some required dependencies are missing!")
        print("Please run: ./setup.sh or pip install -r requirements.txt")
        return False
    
    # Test basic functionality
    print("\n3. Testing basic functionality...")
    if not test_basic_functionality():
        return False
    
    # Test Hugging Face access
    print("\n4. Testing Hugging Face access...")
    hf_ok = test_huggingface_access()
    
    # Final summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if all_imports_ok and hf_ok:
        print("🎉 ALL TESTS PASSED!")
        print("\nYou're ready to start downloading:")
        print("  python download_data.py")
        print("\nTo monitor progress:")
        print("  python monitor_progress.py")
        return True
    else:
        print("⚠️  SOME TESTS FAILED")
        if not all_imports_ok:
            print("- Missing required dependencies")
        if not hf_ok:
            print("- Hugging Face access issues")
        print("\nPlease fix the issues above before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
