#!/usr/bin/env python3
"""
Monitor the progress of corpus download and provide real-time statistics.
"""

import os
import json
import time
import argparse
from pathlib import Path
from collections import defaultdict

def count_files_and_size(directory):
    """Count files and total size in a directory."""
    if not os.path.exists(directory):
        return 0, 0
    
    file_count = 0
    total_size = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                file_count += 1
                total_size += os.path.getsize(file_path)
    
    return file_count, total_size

def format_size(size_bytes):
    """Format size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def estimate_tokens(file_count, avg_tokens_per_file=5000):
    """Estimate total tokens based on file count."""
    return file_count * avg_tokens_per_file

def monitor_progress(corpus_dir, target_tokens=3_000_000_000, refresh_interval=30):
    """Monitor download progress."""
    corpus_path = Path(corpus_dir)
    
    if not corpus_path.exists():
        print(f"Corpus directory {corpus_dir} does not exist. Starting monitoring...")
        corpus_path.mkdir(parents=True, exist_ok=True)
    
    languages = ['english', 'hindi', 'sanskrit']
    target_distribution = {'english': 0.5, 'hindi': 0.35, 'sanskrit': 0.15}
    
    print(f"Monitoring corpus download in: {corpus_dir}")
    print(f"Target: {target_tokens:,} tokens")
    print(f"Refresh interval: {refresh_interval} seconds")
    print("Press Ctrl+C to stop monitoring\n")
    
    try:
        while True:
            print(f"\n{'='*80}")
            print(f"CORPUS DOWNLOAD PROGRESS - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}")
            
            total_files = 0
            total_size = 0
            
            for lang in languages:
                lang_dir = corpus_path / lang / 'raw'
                files, size = count_files_and_size(lang_dir)
                estimated_tokens = estimate_tokens(files)
                target_lang_tokens = int(target_tokens * target_distribution[lang])
                progress_pct = (estimated_tokens / target_lang_tokens * 100) if target_lang_tokens > 0 else 0
                
                status_info = ""
                if lang == 'sanskrit':
                    status_info = " (collecting all available)"
                elif progress_pct >= 100:
                    status_info = " (target reached)"
                
                total_files += files
                total_size += size
                
                print(f"{lang.upper():<10} | "
                      f"Files: {files:>6} | "
                      f"Size: {format_size(size):>8} | "
                      f"Est. tokens: {estimated_tokens:>10,} | "
                      f"Target: {target_lang_tokens:>10,} | "
                      f"Progress: {progress_pct:>5.1f}%{status_info}")
            
            total_estimated_tokens = estimate_tokens(total_files)
            overall_progress = (total_estimated_tokens / target_tokens * 100) if target_tokens > 0 else 0
            
            print(f"{'-'*80}")
            print(f"{'TOTAL':<10} | "
                  f"Files: {total_files:>6} | "
                  f"Size: {format_size(total_size):>8} | "
                  f"Est. tokens: {total_estimated_tokens:>10,} | "
                  f"Target: {target_tokens:>10,} | "
                  f"Progress: {overall_progress:>5.1f}%")
            
            # Check for completion
            if total_estimated_tokens >= target_tokens:
                print(f"\n🎉 TARGET REACHED! Estimated {total_estimated_tokens:,} tokens collected.")
                break
            
            # Check for report file
            report_file = corpus_path / 'download_report.json'
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report = json.load(f)
                    print(f"\n📊 Latest report: {report.get('total_downloaded_tokens', 0):,} tokens downloaded")
            
            print(f"\nNext update in {refresh_interval} seconds...")
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
    except Exception as e:
        print(f"\nError during monitoring: {e}")

def show_final_stats(corpus_dir):
    """Show final statistics after download completion."""
    corpus_path = Path(corpus_dir)
    report_file = corpus_path / 'download_report.json'
    
    if not report_file.exists():
        print("No download report found.")
        return
    
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    print(f"\n{'='*60}")
    print("FINAL DOWNLOAD STATISTICS")
    print(f"{'='*60}")
    
    print(f"Target tokens: {report['target_tokens']:,}")
    print(f"Downloaded tokens: {report['total_downloaded_tokens']:,}")
    print(f"Completion rate: {report['total_downloaded_tokens']/report['target_tokens']*100:.1f}%")
    
    print(f"\nPer language breakdown:")
    for lang, stats in report['languages'].items():
        print(f"  {lang.capitalize()}:")
        print(f"    Target: {stats['target_tokens']:,} tokens ({stats['target_percentage']:.1f}%)")
        print(f"    Downloaded: {stats['downloaded_tokens']:,} tokens")
        print(f"    Actual percentage: {stats['actual_percentage']:.1f}%")
        print(f"    Completion: {stats['downloaded_tokens']/stats['target_tokens']*100:.1f}%")

def main():
    parser = argparse.ArgumentParser(description="Monitor multilingual corpus download progress")
    parser.add_argument("--corpus-dir", default="data/corpus_data", help="Corpus directory to monitor")
    parser.add_argument("--target-tokens", type=int, default=3_000_000_000, help="Target total tokens")
    parser.add_argument("--refresh-interval", type=int, default=30, help="Refresh interval in seconds")
    parser.add_argument("--final-stats", action="store_true", help="Show final statistics only")
    
    args = parser.parse_args()
    
    if args.final_stats:
        show_final_stats(args.corpus_dir)
    else:
        monitor_progress(args.corpus_dir, args.target_tokens, args.refresh_interval)

if __name__ == "__main__":
    main()
