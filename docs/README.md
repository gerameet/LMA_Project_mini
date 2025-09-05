# Multilingual Corpus Downloader

A comprehensive tool for downloading and preprocessing large-scale multilingual text corpora from Hugging Face datasets. Designed to collect 3 billion tokens across English (50%), Hindi (30-40%), and Sanskrit (10-20%) with efficient memory usage and robust preprocessing.

## Features

- **Large-scale data collection**: Target 3 billion tokens with configurable distribution
- **Memory efficient**: Streaming downloads with batch processing
- **Multi-language support**: English, Hindi, and Sanskrit with language-specific preprocessing
- **Real-time monitoring**: Progress bars and monitoring tools
- **Robust preprocessing**: Cleaning, deduplication, and segmentation
- **Configurable**: JSON-based configuration for easy customization
- **Resumable**: Can resume interrupted downloads
- **Comprehensive logging**: Detailed logs and final reports

## Quick Start

### 1. Setup

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup to install dependencies
./setup.sh
```

### 2. Basic Usage

```bash
# Start download with default settings (3B tokens)
python download_data.py

# Monitor progress in another terminal
python monitor_progress.py
```

### 3. Custom Configuration

```bash
# Download with custom token target
python download_data.py --target-tokens 1000000000

# Use custom output directory
python download_data.py --output-dir /path/to/custom/directory

# Download specific languages only
python download_data.py --languages english hindi
```

## Project Structure

```
Mini_Project/
├── download_data.py      # Main download script
├── monitor_progress.py   # Progress monitoring tool
├── config.json          # Configuration file
├── requirements.txt      # Python dependencies
├── setup.sh             # Setup script
├── README.md            # This file
└── corpus_data/         # Downloaded data (created during execution)
    ├── english/
    │   ├── raw/          # Raw downloaded files
    │   ├── processed/    # Cleaned and deduplicated corpus
    │   └── metadata/     # Processing statistics
    ├── hindi/
    │   ├── raw/
    │   ├── processed/
    │   └── metadata/
    ├── sanskrit/
    │   ├── raw/
    │   ├── processed/
    │   └── metadata/
    └── download_report.json  # Final download report
```

## Configuration

Edit `config.json` to customize:

- **Target tokens and distribution**: Adjust total tokens and per-language percentages
- **Datasets**: Add/remove Hugging Face datasets for each language
- **Processing parameters**: Batch size, text length limits, etc.
- **Output settings**: Directory structure and file formats

## Datasets Included

### English (50% of tokens)
- OpenWebText: Large web text corpus
- Wikipedia (English): English Wikipedia dump
- C4: Cleaned Common Crawl
- BookCorpus: Collection of books

### Hindi (35% of tokens)
- Wikipedia (Hindi): Hindi Wikipedia dump
- Samanantar: Hindi parallel corpus
- IndicParaphrase: Hindi paraphrase dataset
- Aya Dataset: Multilingual dataset (Hindi filtered)

### Sanskrit (15% of tokens - **collect all available**)
- Wikipedia (Sanskrit): Sanskrit Wikipedia dump
- Itihasa: Sanskrit classical texts
- Classification datasets: Additional Sanskrit content
- Parallel corpora: Sanskrit translations

**Note**: Sanskrit has limited availability on HuggingFace. The script will download ALL available Sanskrit data regardless of the 450M token target, then report the actual amount collected.

## Memory Management

The script is designed to handle large datasets efficiently:

- **Streaming downloads**: No need to load entire datasets into memory
- **Batch processing**: Processes data in configurable batch sizes
- **Progress checkpointing**: Can resume from interruptions
- **Automatic cleanup**: Removes temporary files after processing

## Monitoring and Logging

### Real-time Monitoring
```bash
# Basic monitoring (updates every 30 seconds)
python monitor_progress.py

# Custom refresh interval
python monitor_progress.py --refresh-interval 60

# Monitor custom directory
python monitor_progress.py --corpus-dir /path/to/corpus
```

### Log Files
- `download_data.log`: Detailed download and processing logs
- `corpus_data/download_report.json`: Final statistics and summary
- `corpus_data/<language>/metadata/processing_stats.json`: Per-language statistics

## Text Preprocessing

The script performs comprehensive preprocessing:

1. **Cleaning**:
   - Normalize whitespace
   - Remove special characters
   - Language-specific character filtering
   - Minimum length filtering

2. **Deduplication**:
   - MD5 hash-based duplicate detection
   - Cross-file deduplication
   - Statistics on duplicate removal

3. **Segmentation**:
   - Sentence-level segmentation
   - Language-aware punctuation handling
   - Minimum sentence length filtering

## Sanskrit Data Collection Strategy

Sanskrit presents unique challenges due to limited digital availability:

### **Automatic Handling**
- The script automatically detects Sanskrit's limited availability
- Downloads **ALL available Sanskrit data** instead of stopping at 450M tokens
- Reports actual tokens collected with detailed statistics
- Adjusts English/Hindi targets to maintain ~3B total tokens

### **Check Sanskrit Availability**
```bash
# Check what Sanskrit data is available before starting
python check_sanskrit.py
```

### **Expected Outcomes**
- Sanskrit may collect 50M-200M tokens (varies by availability)
- Script will clearly report: "Sanskrit: collected X tokens (all available)"
- English/Hindi will be adjusted to compensate for any shortfall
- Total corpus will still target 3 billion tokens

## Token Counting

Uses language-appropriate tokenizers:
- **English**: tiktoken (GPT-style tokenization)
- **Hindi**: AI4Bharat IndicBERT tokenizer
- **Sanskrit**: Word-based tokenization (fallback)

## Error Handling and Recovery

- **Automatic retries**: Network errors are automatically retried
- **Graceful degradation**: Falls back to alternative datasets if one fails
- **Progress preservation**: Can resume from the last successful batch
- **Comprehensive error logging**: All errors logged with context

## Performance Optimization

- **Parallel processing**: Multi-threaded downloads where safe
- **Efficient I/O**: Buffered reading and writing
- **Memory monitoring**: Tracks and reports memory usage
- **Progress estimation**: Accurate progress bars and time estimates

## Troubleshooting

### Common Issues

1. **Authentication errors**:
   ```bash
   # Login to Hugging Face
   huggingface-cli login
   ```

2. **Memory issues**:
   - Reduce batch size in config.json
   - Use fewer parallel downloads
   - Increase system swap space

3. **Network issues**:
   - Check internet connection
   - Some datasets may be temporarily unavailable
   - Script will automatically retry failed downloads

4. **Disk space**:
   - Ensure at least 100GB free space for full corpus
   - Use external storage if needed
   - Enable compression in config.json

### Getting Help

1. Check the log file: `download_data.log`
2. View the download report: `corpus_data/download_report.json`
3. Run with verbose logging: `python download_data.py --verbose`

## Advanced Usage

### Custom Dataset Integration

Add new datasets to `config.json`:

```json
{
  "name": "your_dataset_name",
  "config": "dataset_config",
  "text_column": "text_column_name",
  "streaming": true,
  "description": "Dataset description",
  "priority": 1
}
```

### Resuming Downloads

The script automatically resumes from the last checkpoint:

```bash
# Resume interrupted download
python download_data.py --output-dir corpus_data
```

### Quality Control

After download completion:

```bash
# View final statistics
python monitor_progress.py --final-stats

# Check corpus quality
python -c "
import json
with open('corpus_data/download_report.json') as f:
    report = json.load(f)
    print(json.dumps(report, indent=2))
"
```

## System Requirements

- **Python**: 3.8 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 100GB+ free space for full corpus
- **Network**: Stable internet connection
- **OS**: Linux, macOS, or Windows

## License

This tool is for educational and research purposes. Please respect the licenses of individual datasets from Hugging Face.

## Citation

If you use this tool in your research, please cite the relevant Hugging Face datasets and this repository.
