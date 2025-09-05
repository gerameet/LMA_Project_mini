#!/usr/bin/env python3
"""
Test script to demonstrate how the language detection handles Hindi text with English words.
"""

import sys
from pathlib import Path

# Import from download_data.py
sys.path.append(str(Path(__file__).parent))
from download_data import TextPreprocessor

def test_mixed_language_content():
    """Test how the system handles Hindi text with English words."""
    
    preprocessor = TextPreprocessor()
    
    # Test cases: Hindi text with varying amounts of English
    test_cases = [
        {
            'text': 'यह एक बहुत अच्छा दिन है।',
            'description': 'Pure Hindi text',
            'expected': 'accepted'
        },
        {
            'text': 'मैं cricket खेलना पसंद करता हूं।',
            'description': 'Hindi with one English word (cricket)',
            'expected': 'accepted'
        },
        {
            'text': 'आज मैं office जाकर meeting attend करूंगा।',
            'description': 'Hindi with multiple English words (office, meeting, attend)',
            'expected': 'accepted'
        },
        {
            'text': 'मेरा computer और smartphone दोनों working properly हैं।',
            'description': 'Hindi with technical English terms',
            'expected': 'accepted'
        },
        {
            'text': 'यह application बहुत user-friendly है और performance भी good है।',
            'description': 'Hindi with technical English phrases',
            'expected': 'accepted'
        },
        {
            'text': 'आज weather बहुत hot है, इसलिए मैं indoor रहूंगा।',
            'description': 'Hindi with common English adjectives',
            'expected': 'accepted'
        },
        {
            'text': 'This is mostly English with कुछ Hindi words mixed in.',
            'description': 'Mostly English with some Hindi words',
            'expected': 'mixed - depends on ratio'
        },
        {
            'text': 'Complete English sentence without any Hindi.',
            'description': 'Pure English text',
            'expected': 'rejected for Hindi'
        },
        {
            'text': 'मैं university में computer science पढ़ता हूं और programming languages सीखता हूं।',
            'description': 'Hindi with multiple English technical terms',
            'expected': 'accepted'
        },
        {
            'text': 'COVID-19 pandemic के दौरान online classes और work from home common हो गया।',
            'description': 'Hindi with modern English terms and phrases',
            'expected': 'accepted'
        }
    ]
    
    print("="*80)
    print("TESTING HINDI TEXT WITH ENGLISH WORDS")
    print("="*80)
    print(f"{'Test Case':<50} {'Script Detection':<15} {'Accepted?':<10} {'Cleaned Length':<15}")
    print("-"*90)
    
    for i, case in enumerate(test_cases, 1):
        text = case['text']
        description = case['description']
        
        # Test script detection
        detected_script = preprocessor.detect_language_script(text)
        
        # Test language appropriateness for Hindi
        is_appropriate = preprocessor.is_language_appropriate(text, 'hindi')
        
        # Test cleaning
        cleaned_text = preprocessor.clean_text(text, 'hindi')
        
        # Results
        accepted = "✅ YES" if cleaned_text else "❌ NO"
        cleaned_length = len(cleaned_text) if cleaned_text else 0
        
        print(f"{f'{i}. {description[:45]}':<50} {detected_script:<15} {accepted:<10} {cleaned_length:<15}")
        
        if cleaned_text:
            print(f"   Original: {text}")
            print(f"   Cleaned:  {cleaned_text}")
        print()
    
    # Detailed analysis of character ratios
    print("\n" + "="*80)
    print("DETAILED CHARACTER ANALYSIS")
    print("="*80)
    
    analysis_cases = [
        'यह एक बहुत अच्छा दिन है।',  # Pure Hindi
        'मैं cricket खेलना पसंद करता हूं।',  # Hindi with English
        'आज मैं office जाकर meeting attend करूंगा।',  # More English
        'This is mostly English with कुछ Hindi words mixed in.',  # Mostly English
    ]
    
    for i, text in enumerate(analysis_cases, 1):
        print(f"\nCase {i}: {text}")
        
        # Character analysis
        total_chars = len(text)
        alpha_chars = sum(1 for c in text if c.isalpha())
        devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        latin_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
        
        if alpha_chars > 0:
            devanagari_ratio = devanagari_chars / alpha_chars
            latin_ratio = latin_chars / alpha_chars
            
            print(f"  Total chars: {total_chars}, Alpha chars: {alpha_chars}")
            print(f"  Devanagari chars: {devanagari_chars} ({devanagari_ratio:.2%})")
            print(f"  Latin chars: {latin_chars} ({latin_ratio:.2%})")
            print(f"  Script detection: {preprocessor.detect_language_script(text)}")
            print(f"  Appropriate for Hindi: {preprocessor.is_language_appropriate(text, 'hindi')}")

def demonstrate_thresholds():
    """Demonstrate the current threshold logic."""
    print("\n" + "="*80)
    print("CURRENT THRESHOLD LOGIC")
    print("="*80)
    print("Script Detection Rules:")
    print("- devanagari_ratio > 0.5  → 'devanagari' (Hindi/Sanskrit)")
    print("- latin_ratio > 0.8       → 'latin' (English)")
    print("- else                    → 'mixed'")
    print()
    print("Language Appropriateness for Hindi:")
    print("- Accept: 'devanagari' OR 'mixed'")
    print("- Reject: 'latin'")
    print()
    print("Character Cleaning for Hindi:")
    print("- Keeps: Devanagari chars (\\u0900-\\u097F) + word chars + punctuation")
    print("- This PRESERVES English letters within Hindi text!")

if __name__ == "__main__":
    test_mixed_language_content()
    demonstrate_thresholds()
