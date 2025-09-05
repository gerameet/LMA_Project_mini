#!/usr/bin/env python3
"""
Improved language detection for Hindi text with English words.
Addresses the issues found in the current implementation.
"""

import re
from typing import Dict

class ImprovedLanguageDetector:
    """Improved language detection that better handles code-switching."""
    
    def __init__(self):
        # Common English words that frequently appear in Hindi text
        self.common_english_in_hindi = {
            # Technology terms
            'computer', 'laptop', 'mobile', 'phone', 'internet', 'website', 'email', 'app', 'software',
            'hardware', 'programming', 'coding', 'technology', 'digital', 'online', 'offline',
            
            # Business/Work terms  
            'office', 'meeting', 'project', 'manager', 'team', 'company', 'business', 'job', 'work',
            'salary', 'promotion', 'interview', 'resume', 'career',
            
            # Education terms
            'school', 'college', 'university', 'class', 'exam', 'test', 'grade', 'student', 'teacher',
            'degree', 'course', 'subject', 'study', 'education',
            
            # Common adjectives/words
            'good', 'bad', 'nice', 'cool', 'hot', 'cold', 'fast', 'slow', 'big', 'small', 'new', 'old',
            'important', 'serious', 'simple', 'complex', 'easy', 'difficult', 'free', 'busy',
            
            # Sports/Entertainment
            'cricket', 'football', 'tennis', 'movie', 'film', 'song', 'music', 'video', 'game',
            'player', 'match', 'score', 'win', 'lose',
            
            # Medical/Health
            'doctor', 'hospital', 'medicine', 'health', 'disease', 'treatment', 'patient',
            
            # Time/Places
            'time', 'date', 'morning', 'evening', 'night', 'today', 'tomorrow', 'yesterday',
            'market', 'shop', 'store', 'hotel', 'restaurant', 'station', 'airport',
            
            # Modern life
            'facebook', 'whatsapp', 'google', 'youtube', 'instagram', 'twitter', 'covid',
            'lockdown', 'pandemic', 'vaccine', 'mask', 'social', 'media'
        }
        
        # Convert to regex pattern for efficient matching
        self.english_terms_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(word) for word in self.common_english_in_hindi) + r')\b',
            re.IGNORECASE
        )
    
    def analyze_text_composition(self, text: str) -> Dict:
        """Detailed analysis of text composition."""
        if not text:
            return {'script': 'empty', 'confidence': 0, 'details': {}}
        
        # Basic character counts
        total_chars = len(text)
        alpha_chars = sum(1 for c in text if c.isalpha())
        
        if alpha_chars == 0:
            return {'script': 'no_alpha', 'confidence': 0, 'details': {}}
        
        # Script-based character counts
        devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        latin_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
        
        # Word-based analysis
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        
        # Count common English terms in Hindi context
        common_english_words = len(self.english_terms_pattern.findall(text))
        
        # Devanagari words (words containing Devanagari characters)
        devanagari_words = sum(1 for word in words 
                              if any('\u0900' <= c <= '\u097F' for c in word))
        
        # Pure Latin words (excluding common English terms)
        latin_words = sum(1 for word in words 
                         if word.isalpha() and 
                         all(ord(c) < 128 for c in word) and
                         word not in self.common_english_in_hindi)
        
        # Calculate ratios
        devanagari_char_ratio = devanagari_chars / alpha_chars if alpha_chars > 0 else 0
        latin_char_ratio = latin_chars / alpha_chars if alpha_chars > 0 else 0
        
        devanagari_word_ratio = devanagari_words / total_words if total_words > 0 else 0
        common_english_ratio = common_english_words / total_words if total_words > 0 else 0
        pure_latin_ratio = latin_words / total_words if total_words > 0 else 0
        
        details = {
            'total_chars': total_chars,
            'alpha_chars': alpha_chars,
            'devanagari_chars': devanagari_chars,
            'latin_chars': latin_chars,
            'total_words': total_words,
            'devanagari_words': devanagari_words,
            'common_english_words': common_english_words,
            'pure_latin_words': latin_words,
            'devanagari_char_ratio': devanagari_char_ratio,
            'latin_char_ratio': latin_char_ratio,
            'devanagari_word_ratio': devanagari_word_ratio,
            'common_english_ratio': common_english_ratio,
            'pure_latin_ratio': pure_latin_ratio
        }
        
        return details
    
    def detect_language_improved(self, text: str, expected_language: str) -> Dict:
        """Improved language detection with better code-switching support."""
        analysis = self.analyze_text_composition(text)
        
        if analysis.get('script') in ['empty', 'no_alpha']:
            return {
                'detected_language': 'unknown',
                'confidence': 0,
                'is_appropriate': False,
                'reason': 'No alphabetic content',
                'analysis': analysis
            }
        
        # Extract ratios
        devanagari_char_ratio = analysis['devanagari_char_ratio']
        devanagari_word_ratio = analysis['devanagari_word_ratio']
        common_english_ratio = analysis['common_english_ratio']
        pure_latin_ratio = analysis['pure_latin_ratio']
        
        # Decision logic for Hindi
        if expected_language == 'hindi':
            # Strong Hindi indicators
            has_devanagari = devanagari_char_ratio > 0.2  # At least 20% Devanagari chars
            has_hindi_words = devanagari_word_ratio > 0.2  # At least 20% Devanagari words
            
            # English content analysis
            acceptable_english = common_english_ratio <= 0.6  # Up to 60% common English terms
            low_pure_english = pure_latin_ratio <= 0.3  # Max 30% pure English words
            
            # Combined decision
            is_appropriate = (
                has_devanagari and 
                has_hindi_words and 
                acceptable_english and 
                low_pure_english
            )
            
            confidence = (
                devanagari_char_ratio * 0.4 +
                devanagari_word_ratio * 0.4 +
                (1 - pure_latin_ratio) * 0.2
            )
            
            if is_appropriate:
                if devanagari_char_ratio > 0.6:
                    detected_language = 'hindi_dominant'
                else:
                    detected_language = 'hindi_mixed'
            else:
                if pure_latin_ratio > 0.7:
                    detected_language = 'english'
                    reason = f'Too much pure English ({pure_latin_ratio:.1%})'
                elif not has_devanagari:
                    detected_language = 'english'
                    reason = f'No Devanagari script ({devanagari_char_ratio:.1%})'
                else:
                    detected_language = 'ambiguous'
                    reason = f'Mixed content: Dev={devanagari_char_ratio:.1%}, Eng={pure_latin_ratio:.1%}'
        
        elif expected_language == 'english':
            # For English, we want mostly Latin script
            is_appropriate = analysis['latin_char_ratio'] > 0.8
            confidence = analysis['latin_char_ratio']
            detected_language = 'english' if is_appropriate else 'non_english'
            
        else:  # Sanskrit or other
            # Similar to Hindi but potentially stricter
            is_appropriate = devanagari_char_ratio > 0.3 and pure_latin_ratio < 0.4
            confidence = devanagari_char_ratio
            detected_language = expected_language if is_appropriate else 'non_' + expected_language
        
        return {
            'detected_language': detected_language,
            'confidence': confidence,
            'is_appropriate': is_appropriate,
            'reason': reason if not is_appropriate else 'Accepted',
            'analysis': analysis
        }

def test_improved_detection():
    """Test the improved detection on our problem cases."""
    detector = ImprovedLanguageDetector()
    
    # Test cases that were problematic in the original system
    test_cases = [
        'मेरा computer और smartphone दोनों working properly हैं।',
        'यह application बहुत user-friendly है और performance भी good है।',
        'COVID-19 pandemic के दौरान online classes और work from home common हो गया।',
        'मैं university में computer science पढ़ता हूं और programming languages सीखता हूं।',
        'This is mostly English with कुछ Hindi words mixed in.',
        'यह एक बहुत अच्छा दिन है।',  # Pure Hindi
        'Complete English sentence without any Hindi.',  # Pure English
    ]
    
    print("="*80)
    print("IMPROVED LANGUAGE DETECTION TEST")
    print("="*80)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}: {text}")
        result = detector.detect_language_improved(text, 'hindi')
        
        print(f"  Result: {result['detected_language']}")
        print(f"  Appropriate for Hindi: {'✅ YES' if result['is_appropriate'] else '❌ NO'}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Reason: {result['reason']}")
        
        analysis = result['analysis']
        print(f"  Details: Dev={analysis['devanagari_char_ratio']:.1%}, "
              f"Common Eng={analysis['common_english_ratio']:.1%}, "
              f"Pure Eng={analysis['pure_latin_ratio']:.1%}")

if __name__ == "__main__":
    test_improved_detection()
