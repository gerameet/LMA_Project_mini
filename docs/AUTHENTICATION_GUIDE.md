# Hugging Face Authentication & Troubleshooting Guide

## 🔐 Do You Need a Hugging Face Token?

**Short Answer**: Not for most datasets, but **highly recommended** for accessing all datasets reliably.

### Datasets That DON'T Require Authentication:
- Wikipedia (all languages)
- SQuAD
- Most public datasets
- OpenWebText
- C4 (Common Crawl)

### Datasets That MAY Require Authentication:
- Some AI4Bharat datasets (Hindi)
- Certain gated/restricted datasets
- Large commercial datasets
- Private organization datasets

## 🛠️ Fixes Applied for Your Errors

### 1. **Protobuf Library Error** ✅ FIXED
```bash
# The error you saw:
# "requires the protobuf library but it was not found"

# Fix applied:
pip install protobuf>=3.20.0
```

### 2. **Code Bug** ✅ FIXED
```bash
# The error you saw:
# "local variable 'is_sanskrit' referenced before assignment"

# Fix: Moved variable declaration to proper scope in download_dataset()
```

### 3. **Dataset Script Errors** ✅ FIXED
```bash
# The error you saw:
# "Dataset scripts are no longer supported, but found IndicParaphrase.py"

# Fix: Replaced problematic datasets with reliable alternatives:
# - ai4bharat/IndicParaphrase → CohereForAI/aya_dataset
# - Custom script datasets → Standard HuggingFace datasets
```

## 🚀 How to Get Your Token (If Needed)

### Option 1: Get Token Online
1. Go to: https://huggingface.co/settings/tokens
2. Click "New token"
3. Name: "corpus_download"
4. Type: "Read"
5. Click "Generate"
6. Copy the token (starts with hf_...)

### Option 2: Use Command Line
```bash
# Install HuggingFace CLI (already included in requirements)
huggingface-cli login
# Enter your token when prompted
```

### Option 3: Skip Authentication (Fallback)
```bash
# Run with authentication skip
python download_data.py --skip-auth-check
```

## 🧪 Test Your Setup

### 1. Quick Test
```bash
python test_setup.py
```

### 2. Small Sample
```bash
python example.py
# Choose option 1 for small sample
```

### 3. Check Sanskrit Data
```bash
python check_sanskrit.py
```

## 🔄 Current Status After Fixes

✅ **Dependencies**: All installed including protobuf  
✅ **Code bugs**: Fixed variable scope issues  
✅ **Dataset compatibility**: Replaced problematic datasets  
✅ **Authentication**: Optional with graceful fallback  

## 🎯 Ready to Run Commands

```bash
# Basic download (will prompt for auth if needed)
python download_data.py

# Skip authentication check
python download_data.py --skip-auth-check

# Monitor progress
python monitor_progress.py

# Check what you'll get for Sanskrit
python check_sanskrit.py
```

## 📊 Expected Behavior Now

1. **With Token**: Access to all datasets, maximum data collection
2. **Without Token**: Most datasets work, some may be skipped with warnings
3. **Sanskrit**: Will collect all available data regardless of token status
4. **Progress**: Clear reporting of what's collected vs. what was skipped

The script is now robust and will work with or without authentication! 🎉
