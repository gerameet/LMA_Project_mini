#!/usr/bin/env python3
"""
Optimized text cleaning operations to reduce computational load.
"""

import re
import hashlib
from typing import Set, Dict

class OptimizedTextPreprocessor:
    """Lighter-weight text preprocessing with performance optimizations."""
    
    def __init__(self):
        self.seen_hashes: Set[str] = set()
        # Pre-compile regex patterns for better performance
        self.whitespace_pattern = re.compile(r'\s+')
        self.english_pattern = re.compile(r'[^\w\s\.,!?;:\-\'"()&@#%]+')
        self.devanagari_pattern = re.compile(r'[^\u0900-\u097F\w\s\.,!?;:\-\'"()।॥]+')
        
        # Cache for script detection results
        self.script_cache: Dict[str, str] = {}
        self.cache_size_limit = 10000
    
    def detect_language_script_optimized(self, text: str) -> str:
        """Optimized language detection with caching and sampling."""
        if not text:
            return 'unknown'
        
        # Use first 500 chars for detection (much faster for long texts)
        sample_text = text[:500]
        
        # Check cache first
        text_hash = hash(sample_text)
        if text_hash in self.script_cache:
            return self.script_cache[text_hash]
        
        # Count character types (on sample only)
        devanagari_chars = 0
        latin_chars = 0
        total_alpha = 0
        
        # Single pass through text instead of 3 separate passes
        for char in sample_text:
            if char.isalpha():
                total_alpha += 1
                if '\u0900' <= char <= '\u097F':
                    devanagari_chars += 1
                elif ord(char) < 128:
                    latin_chars += 1
        
        if total_alpha == 0:
            result = 'unknown'
        else:
            devanagari_ratio = devanagari_chars / total_alpha
            latin_ratio = latin_chars / total_alpha
            
            # Same logic as before but optimized
            if devanagari_ratio > 0.7:
                result = 'devanagari'
            elif devanagari_ratio > 0.3:
                result = 'mixed_devanagari'
            elif latin_ratio > 0.9:
                result = 'latin'
            elif latin_ratio > 0.6:
                result = 'latin_dominant'
            else:
                result = 'mixed'
        
        # Cache result (with size limit)
        if len(self.script_cache) < self.cache_size_limit:
            self.script_cache[text_hash] = result
        
        return result
    
    def clean_text_lightweight(self, text: str, language: str) -> str:
        """Lightweight text cleaning with minimal operations."""
        if not text or len(text) < 10:  # Quick length check
            return ""
        
        # Single regex operation for whitespace
        text = self.whitespace_pattern.sub(' ', text).strip()
        
        # Quick word count check before expensive operations
        word_count = text.count(' ') + 1  # Approximate word count
        if word_count < 3:
            return ""
        
        # Language-specific cleaning (pre-compiled patterns)
        if language == 'english':
            text = self.english_pattern.sub('', text)
        elif language in ['hindi', 'sanskrit']:
            text = self.devanagari_pattern.sub('', text)
        
        # Skip expensive language appropriateness check for obviously good text
        # Only check if text looks suspicious (too short after cleaning)
        if len(text.split()) < 3:
            return ""
        
        # Optional: Skip language appropriateness check entirely for speed
        # if not self.is_language_appropriate(text, language):
        #     return ""
            
        return text
    
    def is_duplicate_optimized(self, text: str) -> bool:
        """Optimized duplicate detection."""
        # Use a shorter hash for speed vs memory tradeoff
        # Or hash only first/last parts of very long texts
        if len(text) > 5000:
            # For very long texts, hash first and last 1000 chars
            hash_text = text[:1000] + text[-1000:]
        else:
            hash_text = text
            
        text_hash = hashlib.md5(hash_text.encode()).hexdigest()[:16]  # Shorter hash
        
        if text_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(text_hash)
        return False

class FastTokenCounter:
    """Faster token counting with approximations."""
    
    def __init__(self):
        # Use simpler tokenization methods
        pass
    
    def count_tokens_fast(self, text: str, language: str) -> int:
        """Fast approximate token counting."""
        if not text:
            return 0
        
        if language == 'english':
            # Simple word-based approximation (much faster than tiktoken)
            return len(text.split()) * 1.3  # Rough conversion factor
        elif language in ['hindi', 'sanskrit']:
            # Word-based counting for Devanagari (skip transformer tokenization)
            words = text.split()
            # Devanagari words tend to be longer in tokens
            return len(words) * 1.8  # Rough conversion factor
        else:
            return len(text.split())

# Performance comparison
def performance_comparison():
    """Compare original vs optimized performance."""
    import time
    
    # Sample texts
    english_text = "This is a sample English text with various punctuation marks and symbols!"
    hindi_text = "यह एक नमूना हिंदी टेक्स्ट है जिसमें अंग्रेजी शब्द (English words) भी हैं।"
    
    # Original processor (from your main script)
    from download_data import TextPreprocessor, TokenCounter
    original_processor = TextPreprocessor()
    original_counter = TokenCounter()
    
    # Optimized processor
    optimized_processor = OptimizedTextPreprocessor()
    fast_counter = FastTokenCounter()
    
    texts = [english_text, hindi_text] * 1000  # 2000 texts
    
    print("Performance Comparison:")
    print("=" * 50)
    
    # Original method
    start_time = time.time()
    for text in texts:
        cleaned = original_processor.clean_text(text, 'hindi')
        if cleaned:
            tokens = original_counter.count_tokens(cleaned, 'hindi')
    original_time = time.time() - start_time
    
    # Optimized method
    start_time = time.time()
    for text in texts:
        cleaned = optimized_processor.clean_text_lightweight(text, 'hindi')
        if cleaned:
            tokens = fast_counter.count_tokens_fast(cleaned, 'hindi')
    optimized_time = time.time() - start_time
    
    print(f"Original method:  {original_time:.2f} seconds")
    print(f"Optimized method: {optimized_time:.2f} seconds")
    print(f"Speedup:          {original_time/optimized_time:.1f}x faster")
    print(f"Time per text:    {optimized_time/len(texts)*1000:.2f} ms")

if __name__ == "__main__":
    performance_comparison()
