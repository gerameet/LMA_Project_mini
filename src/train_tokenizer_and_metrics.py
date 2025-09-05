#!/usr/bin/env python3
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
"""
Train a Byte-Level BPE tokenizer on the processed corpus and report metrics.
"""

from pathlib import Path
import collections
import re
import os
import json

CORPUS_DIR = Path("data/corpus_data")
PROCESSED_PATHS = [
    CORPUS_DIR / "english" / "processed" / "english_corpus.txt",
    CORPUS_DIR / "hindi" / "processed" / "hindi_corpus.txt",
    CORPUS_DIR / "sanskrit" / "processed" / "sanskrit_corpus.txt"
]

from tokenizers import ByteLevelBPETokenizer

TOKENIZER_DIR = Path("tokenizer/tokenizer_bpe")
TOKENIZER_DIR.mkdir(exist_ok=True)

# --- Preprocessing steps ---
# Pre-compile regex patterns for speed
WHITESPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[^\w\s]", re.ASCII)

def normalize_text(text):
    # Fast normalization: lowercase, strip, collapse whitespace
    text = text.lower().strip()
    text = WHITESPACE_RE.sub(" ", text)
    # Fast ASCII punctuation removal
    text = PUNCT_RE.sub("", text)
    return text

# --- Sentence segmentation ---
def segment_sentences(text, lang):
    # Simple rule-based segmentation
    if lang == "english":
        # Split on period, exclamation, question mark
        return re.split(r"[.!?]+", text)
    else:
        # For Hindi/Sanskrit, split on danda (।) and double danda (॥)
        return re.split(r"[।॥]+", text)


# --- Train or load ByteLevel BPE Tokenizer ---
VOCAB_SIZE = 50000
MIN_FREQ = 2
SPECIAL_TOKENS = ["<s>", "<pad>", "</s>", "<unk>", "<mask>"]

VOCAB_PATH = TOKENIZER_DIR / "vocab.json"
MERGES_PATH = TOKENIZER_DIR / "merges.txt"

if VOCAB_PATH.exists() and MERGES_PATH.exists():
    print("Loading existing ByteLevel BPE tokenizer...")
    tokenizer = ByteLevelBPETokenizer(str(VOCAB_PATH), str(MERGES_PATH))
else:
    print("Training ByteLevel BPE tokenizer using tokenizers library...")
    tokenizer = ByteLevelBPETokenizer()
    tokenizer.train(
        files=[str(p) for p in PROCESSED_PATHS],
        vocab_size=VOCAB_SIZE,
        min_frequency=MIN_FREQ,
        special_tokens=SPECIAL_TOKENS
    )
    tokenizer.save_model(str(TOKENIZER_DIR))
    print(f"Tokenizer saved to {TOKENIZER_DIR}")


# --- Multiprocessing tokenization and metrics ---
import multiprocessing

def process_line(args):
    line, lang = args
    line = line.strip()
    if not line:
        return None
    norm_line = normalize_text(line)
    bytes_len = len(norm_line.encode("utf-8"))
    encoding = tokenizer.encode(norm_line)
    tokens = encoding.tokens
    tokens_len = len(tokens)
    compressed_bytes = len(" ".join(tokens).encode("utf-8"))
    words = norm_line.split()
    fertility = tokens_len / (len(words) if words else 1)
    lang_type = lang if lang in ["english", "hindi", "sanskrit"] else "english"
    sentences = segment_sentences(norm_line, lang_type)
    sentences_count = len([s for s in sentences if s.strip()])
    return {
        "lines": 1,
        "bytes": bytes_len,
        "tokens": tokens_len,
        "words": len(words),
        "sentences": sentences_count,
        "fertility_sum": fertility,
        "compressed_bytes": compressed_bytes
    }

metrics = {}
cpu_count = min(40, multiprocessing.cpu_count())
for path in PROCESSED_PATHS:
    lang = path.parts[-3]
    print(f"\nCalculating metrics for {lang} corpus with {cpu_count} processes...")
    with open(path, "r", encoding="utf-8") as f:
        args = ((line, lang) for line in f)
        with multiprocessing.Pool(cpu_count) as pool:
            results = pool.map(process_line, args, chunksize=1000)
    # Aggregate results
    total_lines = total_bytes = total_tokens = total_words = total_sentences = fertility_sum = compressed_bytes = 0
    for r in results:
        if r is None:
            continue
        total_lines += r["lines"]
        total_bytes += r["bytes"]
        total_tokens += r["tokens"]
        total_words += r["words"]
        total_sentences += r["sentences"]
        fertility_sum += r["fertility_sum"]
        compressed_bytes += r["compressed_bytes"]
    compression_ratio = total_bytes / (compressed_bytes if compressed_bytes else 1)
    metrics[lang] = {
        "lines": total_lines,
        "bytes": total_bytes,
        "tokens": total_tokens,
        "words": total_words,
        "sentences": total_sentences,
        "avg_tokens_per_line": total_tokens / total_lines if total_lines else 0,
        "avg_bytes_per_line": total_bytes / total_lines if total_lines else 0,
        "compression_ratio": compression_ratio,
        "avg_fertility": fertility_sum / total_lines if total_lines else 0
    }
    print(json.dumps(metrics[lang], indent=2))

with open(TOKENIZER_DIR / "corpus_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
print(f"\nMetrics saved to {TOKENIZER_DIR / 'corpus_metrics.json'}")

data_sources = {
    "english": "FineWeb",
    "hindi": "Wikipedia, Sangraha",
    "sanskrit": "Wikipedia, Sangraha"
}
print("\nData sources:")
for lang, src in data_sources.items():
    print(f"{lang}: {src}")

