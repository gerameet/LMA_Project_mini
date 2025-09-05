#!/bin/bash

echo "Setting up multilingual corpus downloader..."

# Install Python dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

# Download NLTK data
echo "Downloading NLTK data..."
python -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords')
print('NLTK data downloaded successfully')
"

# Download spaCy models (optional, for better text processing)
echo "Downloading spaCy models..."
python -m spacy download en_core_web_sm
python -m spacy download xx_core_web_sm  # multilingual model

# Test Hugging Face datasets access
echo "Testing Hugging Face datasets access..."
python -c "
from datasets import load_dataset
print('Testing dataset access...')
try:
    # Test with a small dataset
    ds = load_dataset('wikipedia', '20220301.en', streaming=True, split='train')
    example = next(iter(ds))
    print('✓ Hugging Face datasets working correctly')
except Exception as e:
    print(f'⚠ Warning: {e}')
    print('You may need to authenticate with Hugging Face Hub for some datasets')
"

echo "Setup complete! You can now run:"
echo "python download_data.py --help"
