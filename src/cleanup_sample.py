#!/usr/bin/env python3
"""
Clean up and re-run sample with proper language detection.
"""

import os
import shutil
from pathlib import Path

def cleanup_sample():
    """Remove the old sample with wrong language data."""
    sample_dir = Path("data/sample_corpus")
    if sample_dir.exists():
        print("🧹 Cleaning up previous sample data...")
        shutil.rmtree(sample_dir)
        print("✅ Old sample data removed")
    else:
        print("ℹ️  No previous sample data found")

def main():
    print("="*60)
    print("SAMPLE CLEANUP & LANGUAGE VERIFICATION")
    print("="*60)
    
    cleanup_sample()
    
    print("\n🔄 Ready to run a new sample with proper language detection!")
    print("\nRun this command to test with actual language-specific data:")
    print("  python example.py")
    print("\nThe new sample will:")
    print("  ✅ Use SQuAD for English (authentic English)")
    print("  ✅ Use Hindi Wikipedia for Hindi (authentic Hindi)")
    print("  ✅ Use Sanskrit Wikipedia for Sanskrit (authentic Sanskrit)")
    print("  ✅ Include language detection verification")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
