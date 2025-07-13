#!/usr/bin/env python3
"""
Simple DuckDB explorer for WordNet JSONL data.
This script demonstrates how to explore JSONL data using DuckDB programmatically.
"""

import duckdb
import sys
from pathlib import Path
from typing import Union

def explore_jsonl(jsonl_file: Union[str, Path]) -> None:
    """Explore a JSONL file using DuckDB."""
    if not Path(jsonl_file).exists():
        print(f"Error: File {jsonl_file} does not exist")
        return
    
    conn = duckdb.connect(':memory:')
    
    print(f"=== Exploring {jsonl_file} ===\n")
    
    # Basic statistics
    print("1. Basic Statistics:")
    try:
        result = conn.execute(f"""
            SELECT 
                COUNT(*) as total_synsets,
                COUNT(DISTINCT pos) as unique_pos,
                AVG(LENGTH(gloss.original_text)) as avg_gloss_length
            FROM read_json_auto('{jsonl_file}')
        """).fetchone()
        
        if result:
            print(f"   Total synsets: {result[0]:,}")
            print(f"   Unique parts of speech: {result[1]}")
            print(f"   Average gloss length: {result[2]:.1f} characters")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Part of Speech Distribution:")
    try:
        results = conn.execute(f"""
            SELECT pos, COUNT(*) as count 
            FROM read_json_auto('{jsonl_file}')
            GROUP BY pos 
            ORDER BY count DESC
        """).fetchall()
        
        for pos, count in results:
            print(f"   {pos}: {count:,}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Sample Records:")
    try:
        results = conn.execute(f"""
            SELECT synset_id, pos, gloss.original_text
            FROM read_json_auto('{jsonl_file}')
            WHERE LENGTH(gloss.original_text) > 20
            LIMIT 3
        """).fetchall()
        
        for synset_id, pos, gloss in results:
            print(f"   {synset_id} ({pos}): {gloss[:100]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n4. Annotation Statistics:")
    try:
        results = conn.execute(f"""
            SELECT 
                pos,
                AVG(ARRAY_LENGTH(gloss.annotations)) as avg_annotations,
                AVG(ARRAY_LENGTH(gloss.tokens)) as avg_tokens
            FROM read_json_auto('{jsonl_file}')
            GROUP BY pos
            ORDER BY avg_annotations DESC
        """).fetchall()
        
        for pos, avg_ann, avg_tok in results:
            print(f"   {pos}: {avg_ann:.1f} annotations, {avg_tok:.1f} tokens")
    except Exception as e:
        print(f"   Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python explore_jsonl.py <jsonl_file>")
        sys.exit(1)
    
    jsonl_file = sys.argv[1]
    explore_jsonl(jsonl_file)
