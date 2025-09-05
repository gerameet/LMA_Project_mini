# AI4Bharat Sangraha Dataset Configuration Recommendations

## Dataset Analysis Summary

Based on testing the AI4Bharat Sangraha dataset, here are the optimal configurations for Sanskrit and Hindi corpus collection:

## Available Splits

### Sanskrit
- **verified/san**: ~1,028 tokens/text (high quality, smaller volume)
- **synthetic/san_Deva**: ~877 tokens/text (larger volume, Devanagari script)
- **synthetic/san_Latn**: ~877 tokens/text (larger volume, Latin transliteration)

### Hindi  
- **verified/hin**: ~550 tokens/text (high quality, includes some code-switching)
- **synthetic/hin_Deva**: ~700 tokens/text (larger volume, Devanagari script)
- **synthetic/hin_Latn**: ~700 tokens/text (larger volume, Latin transliteration)

## Recommended Strategy

### For Sanskrit (Target: 15% of corpus)
1. **Primary**: `verified/san` - Highest quality Sanskrit content
2. **Secondary**: `synthetic/san_Deva` - More volume, Devanagari script
3. **Skip**: `synthetic/san_Latn` - Latin transliteration may confuse language models

**Rationale**: 
- Quality over quantity for Sanskrit
- Devanagari script maintains authenticity
- Limited Sanskrit data availability makes every quality source valuable

### For Hindi (Target: 35% of corpus)
1. **Primary**: `verified/hin` - High quality, handles code-switching well
2. **Secondary**: `synthetic/hin_Deva` - Large volume for token targets
3. **Skip**: `synthetic/hin_Latn` - Latin transliteration less authentic

**Rationale**:
- Verified data includes natural code-switching (Hindi with English words)
- Synthetic Devanagari data provides volume for large token targets
- Maintains script authenticity

## Code-Switching Handling

### Hindi Documents with English Words
- **Status**: Common and acceptable in modern Hindi
- **Detection**: Improved language detection handles mixed content
- **Strategy**: Accept documents with 30-70% Devanagari characters
- **Examples**: Technical terms, proper nouns, modern vocabulary

### Implementation Details
```python
# Improved detection ratios
if devanagari_ratio > 0.7:
    return 'devanagari'  # Pure Hindi/Sanskrit
elif devanagari_ratio > 0.3:
    return 'mixed_devanagari'  # Hindi with English words (ACCEPT)
elif latin_ratio > 0.9:
    return 'latin'  # Pure English
```

## Dataset Quality Assessment

### Verified vs Synthetic
- **Verified**: Human-reviewed, higher quality, natural language patterns
- **Synthetic**: Machine-processed, larger volume, may have artifacts

### Script Preference
- **Devanagari (Recommended)**: Authentic script, better for language models
- **Latin Transliteration**: Avoid - can confuse tokenization and model training

## Updated Configuration

The main script now uses:
```python
'hindi': [
    'wikimedia/wikipedia(20231101.hi)',
    'ai4bharat/sangraha(verified/hin)',
    'ai4bharat/sangraha(synthetic/hin_Deva)'
],
'sanskrit': [
    'wikimedia/wikipedia(20231101.sa)', 
    'ai4bharat/sangraha(verified/san)',
    'ai4bharat/sangraha(synthetic/san_Deva)'
]
```

## Data Volume Expectations

### Sanskrit Reality Check
- **Limited Availability**: Sanskrit has very limited digital corpus availability
- **Strategy**: Collect ALL available Sanskrit data regardless of original target
- **Expectation**: May not reach 15% target - this is normal and acceptable
- **Recommendation**: Use all verified + synthetic Devanagari for maximum coverage

### Hindi Scaling
- **Abundant Data**: Synthetic dataset provides large volume
- **Strategy**: Use quality thresholds to select best content
- **Expected**: Should easily meet 35% target
- **Balance**: Start with verified, add synthetic to reach token targets

## Quality vs Volume Trade-offs

1. **High Quality, Lower Volume**: Use only verified splits
2. **Balanced**: Verified + synthetic Devanagari (RECOMMENDED)
3. **Maximum Volume**: All splits including Latin (NOT recommended)

## Implementation Notes

- Code-switching detection improved to handle Hindi-English mixing
- Script filtering ensures authentic Devanagari content
- Deduplication prevents overlap between verified and synthetic
- Progress tracking accounts for Sanskrit data limitations

This configuration provides the best balance of authenticity, quality, and volume for multilingual corpus collection.
