#!/usr/bin/env python3
"""
Simple King Analysis with DuckDB
================================
A simplified version that works reliably with the WordNet JSONL data.

Usage:
    python simple_king_analysis.py
"""

import duckdb
from pathlib import Path
import sys

def main():
    print("🔍 Simple King Analysis with DuckDB")
    print("=" * 50)
    
    # File path
    jsonl_file = "json_file/wordnet.jsonl"
    
    # Check if file exists
    if not Path(jsonl_file).exists():
        print(f"❌ File not found: {jsonl_file}")
        print("   Please check the file path and try again.")
        return 1
    
    try:
        # Connect to DuckDB
        conn = duckdb.connect(':memory:')
        print(f"✅ Connected to DuckDB")
        print(f"📁 Loading file: {jsonl_file}")
        
        # Test basic file reading first
        print("🔄 Testing file access...")
        test_count = conn.execute(f"""
            SELECT COUNT(*) as total_records
            FROM read_json_auto('{jsonl_file}')
        """).fetchone()
        
        print(f"✅ File contains {test_count[0]:,} records")
        
        # Query 1: Find all synsets containing "king"
        print("\n" + "="*60)
        print("🤴 FINDING ALL SYNSETS CONTAINING 'KING'")
        print("="*60)
        
        king_query = f"""
            SELECT synset_id, pos, gloss.original_text as definition
            FROM read_json_auto('{jsonl_file}') 
            WHERE list_contains(list_transform(terms, x -> x.term), 'king')
            ORDER BY synset_id
        """
        
        king_results = conn.execute(king_query).fetchall()
        
        print(f"Found {len(king_results)} synsets containing 'king':")
        for i, (synset_id, pos, definition) in enumerate(king_results, 1):
            print(f"\n{i}. {synset_id} ({pos})")
            # Safely handle definition text
            def_text = definition if definition else "No definition available"
            if len(def_text) > 100:
                def_text = def_text[:100] + "..."
            print(f"   Definition: {def_text}")
        
        # Query 2: Find synsets for key related words
        print("\n" + "="*60)
        print("👑 FINDING SYNSETS FOR RELATED WORDS")
        print("="*60)
        
        related_words = ['sovereign', 'ruler', 'kingdom', 'monarch']
        
        for word in related_words:
            print(f"\n🔍 Synsets for '{word.upper()}':")
            
            related_query = f"""
                SELECT synset_id, pos, gloss.original_text as definition
                FROM read_json_auto('{jsonl_file}') 
                WHERE list_contains(list_transform(terms, x -> x.term), '{word}')
                ORDER BY synset_id
                LIMIT 3
            """
            
            try:
                related_results = conn.execute(related_query).fetchall()
                
                if related_results:
                    for synset_id, pos, definition in related_results:
                        print(f"   • {synset_id} ({pos})")
                        def_text = definition if definition else "No definition"
                        if len(def_text) > 80:
                            def_text = def_text[:80] + "..."
                        print(f"     {def_text}")
                else:
                    print(f"   No synsets found for '{word}'")
            
            except Exception as word_error:
                print(f"   ❌ Error querying '{word}': {word_error}")
        
        # Query 3: Basic statistics
        print("\n" + "="*60)
        print("📊 BASIC STATISTICS")
        print("="*60)
        
        try:
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_synsets,
                    COUNT(DISTINCT pos) as unique_pos,
                    COUNT(DISTINCT synset_id) as unique_synsets
                FROM read_json_auto('{jsonl_file}')
            """
            
            stats = conn.execute(stats_query).fetchone()
            print(f"Total records: {stats[0]:,}")
            print(f"Unique parts of speech: {stats[1]}")
            print(f"Unique synsets: {stats[2]:,}")
            
            # POS distribution
            pos_query = f"""
                SELECT pos, COUNT(*) as count
                FROM read_json_auto('{jsonl_file}')
                GROUP BY pos
                ORDER BY count DESC
            """
            
            pos_results = conn.execute(pos_query).fetchall()
            print(f"\nPart-of-speech distribution:")
            for pos, count in pos_results:
                print(f"   {pos}: {count:,} synsets")
                
        except Exception as stats_error:
            print(f"❌ Statistics error: {stats_error}")
        
        print("\n" + "="*60)
        print("🎯 Analysis complete!")
        print("="*60)
        
        # Ask if user wants to save results
        save_choice = input("\n💾 Save results to file? (y/n): ").lower().strip()
        if save_choice == 'y':
            output_file = "king_analysis_simple_results.txt"
            
            with open(output_file, 'w') as f:
                f.write("Simple King Analysis Results\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("KING SYNSETS:\n")
                f.write("-" * 20 + "\n")
                for i, (synset_id, pos, definition) in enumerate(king_results, 1):
                    f.write(f"{i}. {synset_id} ({pos})\n")
                    f.write(f"   Definition: {definition}\n\n")
                
                f.write("\nRELATED WORDS:\n")
                f.write("-" * 20 + "\n")
                for word in related_words:
                    f.write(f"\nSynsets for '{word}':\n")
                    try:
                        related_query = f"""
                            SELECT synset_id, pos, gloss.original_text as definition
                            FROM read_json_auto('{jsonl_file}') 
                            WHERE list_contains(list_transform(terms, x -> x.term), '{word}')
                            ORDER BY synset_id
                            LIMIT 3
                        """
                        related_results = conn.execute(related_query).fetchall()
                        for synset_id, pos, definition in related_results:
                            f.write(f"   {synset_id} ({pos}): {definition}\n")
                    except:
                        f.write(f"   Error querying '{word}'\n")
            
            print(f"✅ Results saved to: {output_file}")
        
        conn.close()
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        exit_code = 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit_code = 1
    
    sys.exit(exit_code)
