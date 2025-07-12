#!/usr/bin/env python3
"""
Data Distribution Helper for WordNet JSONL Files
Helps package and prepare WordNet JSONL data for sharing.
"""

import os
import hashlib
import gzip
import json
from pathlib import Path
import requests

def get_file_info(filepath):
    """Get file size and MD5 hash for verification."""
    if not os.path.exists(filepath):
        return None
    
    size = os.path.getsize(filepath)
    
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    
    return {
        "size_mb": round(size / (1024 * 1024), 2),
        "md5": hash_md5.hexdigest()
    }

def compress_jsonl(input_path, output_path=None):
    """Compress JSONL file with gzip for smaller uploads."""
    if output_path is None:
        output_path = str(input_path) + ".gz"
    
    print(f"Compressing {input_path} to {output_path}...")
    
    with open(input_path, 'rb') as f_in:
        with gzip.open(output_path, 'wb') as f_out:
            f_out.writelines(f_in)
    
    original_info = get_file_info(input_path)
    compressed_info = get_file_info(output_path)
    
    compression_ratio = round(compressed_info['size_mb'] / original_info['size_mb'], 2)
    
    print(f"Original: {original_info['size_mb']} MB")
    print(f"Compressed: {compressed_info['size_mb']} MB")
    print(f"Compression ratio: {compression_ratio:.2f}")
    
    return output_path, compressed_info

def create_metadata_file(jsonl_path, metadata_path=None):
    """Create metadata file for the dataset."""
    if metadata_path is None:
        metadata_path = str(jsonl_path).replace('.jsonl', '_metadata.json')
    
    file_info = get_file_info(jsonl_path)
    
    # Count records and analyze structure
    record_count = 0
    pos_counts = {}
    
    print("Analyzing JSONL structure...")
    with open(jsonl_path, 'r') as f:
        for line in f:
            record = json.loads(line)
            record_count += 1
            pos = record.get('pos', 'unknown')
            pos_counts[pos] = pos_counts.get(pos, 0) + 1
            
            if record_count % 10000 == 0:
                print(f"  Processed {record_count} records...")
    
    metadata = {
        "dataset_name": "WordNet Gloss Disambiguation Project - JSONL Format",
        "description": "Modernized JSONL format of Princeton University's WordNet Gloss Disambiguation Project (2008)",
        "format": "JSONL (JSON Lines)",
        "total_records": record_count,
        "file_info": file_info,
        "pos_distribution": pos_counts,
        "schema": {
            "synset_id": "Unique synset identifier (e.g., 'n00003553')",
            "pos": "Part of speech (n, v, a, r)",
            "terms": "List of terms/words in the synset",
            "sense_keys": "WordNet sense keys",
            "gloss": {
                "original_text": "Original definition text",
                "tokens": "Tokenized gloss with POS tags",
                "annotations": "Linguistic annotations",
                "collocations": "Multi-word expressions"
            },
            "metadata": "Conversion and validation metadata"
        },
        "usage_examples": [
            "DuckDB: SELECT * FROM read_json_auto('wordnet_glosses.jsonl') LIMIT 5;",
            "Python: import json; [json.loads(line) for line in open('wordnet_glosses.jsonl')]",
            "CLI: wn-gloss query --jsonl wordnet_glosses.jsonl --sql 'SELECT pos, COUNT(*) FROM data GROUP BY pos'"
        ]
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Metadata saved to {metadata_path}")
    return metadata

def generate_download_script(download_url, filename="wordnet_glosses.jsonl"):
    """Generate download script for users."""
    script_content = f'''#!/bin/bash
# WordNet JSONL Download Script
# This script downloads the pre-converted WordNet JSONL data

set -e  # Exit on error

FILENAME="{filename}"
URL="{download_url}"

echo "🔄 Downloading WordNet JSONL data..."
echo "📁 File: $FILENAME"
echo "🔗 URL: $URL"
echo

if [ -f "$FILENAME" ]; then
    echo "⚠️  File already exists: $FILENAME"
    read -p "Do you want to re-download? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "✅ Using existing file."
        exit 0
    fi
fi

# Download with progress bar
if command -v wget &> /dev/null; then
    wget --progress=bar:force:noscroll "$URL" -O "$FILENAME"
elif command -v curl &> /dev/null; then
    curl -L --progress-bar "$URL" -o "$FILENAME"
else
    echo "❌ Error: Neither wget nor curl found. Please install one of them."
    exit 1
fi

# Verify download
if [ -f "$FILENAME" ]; then
    SIZE=$(du -h "$FILENAME" | cut -f1)
    echo "✅ Download complete! File size: $SIZE"
    echo "🔍 First few lines:"
    head -3 "$FILENAME"
else
    echo "❌ Download failed!"
    exit 1
fi
'''
    
    with open("download_wordnet_data.sh", "w") as f:
        f.write(script_content)
    
    os.chmod("download_wordnet_data.sh", 0o755)
    print("Generated download_wordnet_data.sh")

def main():
    jsonl_path = "old_gloss/json_file/wordnet.jsonl"
    
    if not os.path.exists(jsonl_path):
        print(f"❌ JSONL file not found: {jsonl_path}")
        print("Please ensure the WordNet JSONL file exists.")
        return
    
    print("📊 WordNet JSONL Distribution Helper")
    print("=" * 50)
    
    # 1. Analyze original file
    print("\n1️⃣ Analyzing original file...")
    info = get_file_info(jsonl_path)
    print(f"File: {jsonl_path}")
    print(f"Size: {info['size_mb']} MB")
    print(f"MD5: {info['md5']}")
    
    # 2. Create compressed version
    print(f"\n2️⃣ Creating compressed version...")
    compressed_path, comp_info = compress_jsonl(jsonl_path, "wordnet_glosses.jsonl.gz")
    
    # 3. Generate metadata
    print(f"\n3️⃣ Generating metadata...")
    metadata = create_metadata_file(jsonl_path)
    
    # 4. Distribution recommendations
    print(f"\n4️⃣ Distribution Recommendations:")
    print(f"📁 Original file: {info['size_mb']} MB")
    print(f"📦 Compressed file: {comp_info['size_mb']} MB")
    print()
    
    if info['size_mb'] < 25:
        print("✅ Small enough for GitHub release attachments")
    elif info['size_mb'] < 100:
        print("💡 Consider GitHub LFS or Zenodo")
    else:
        print("📚 Recommend academic repository (Zenodo, Figshare)")
    
    print(f"\n🔗 Next steps:")
    print(f"1. Upload wordnet_glosses.jsonl.gz to your chosen platform")
    print(f"2. Get the download URL")
    print(f"3. Run: generate_download_script('<your-url>')")
    print(f"4. Update README.md with download instructions")

if __name__ == "__main__":
    main()
