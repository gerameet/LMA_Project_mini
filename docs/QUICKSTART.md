# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
./setup.sh
```

### Step 2: Test Your Setup
```bash
python test_setup.py
```

### Step 3: Run a Small Sample (Optional)
```bash
python example.py --sample
```

### Step 4: Start Full Download
```bash
# In terminal 1: Start download
python download_data.py

# In terminal 2: Monitor progress
python monitor_progress.py
```

## ⚙️ Configuration

The script will download:
- **English**: ~1.5B tokens (50%) from FineWeb English
- **Hindi**: ~1.05B tokens (35%) from Wikipedia, Samanantar, IndicParaphrase
- **Sanskrit**: up to **450M tokens** (15%) from Wikipedia, Itihasa, classical texts
  - Hard cutoff at 450M tokens (script will stop collecting Sanskrit after this)
  - Actual amount will be reported during and after download
  - If less than 450M tokens are available, all will be collected

### Check Sanskrit Data First (Optional)
```bash
python check_sanskrit.py
```

## 📊 What You'll Get

```
corpus_data/
├── english/processed/english_corpus.txt     # ~1.5B tokens
├── hindi/processed/hindi_corpus.txt         # ~1.05B tokens  
├── sanskrit/processed/sanskrit_corpus.txt   # Variable (all available)
└── download_report.json                     # Statistics with actual counts
```

## 🔧 Troubleshooting

**Import errors?** → Run `./setup.sh`  
**Network issues?** → Check internet, some datasets may be temporarily unavailable  
**Memory issues?** → Reduce batch_size in config.json  
**HuggingFace errors?** → Run `huggingface-cli login`  

## 📈 Expected Timeline

- **Small sample**: 2-5 minutes
- **Full download**: 6-24 hours depending on internet speed
- **Processing**: Additional 2-4 hours for cleaning and deduplication

Ready to start? Run `python download_data.py`!
