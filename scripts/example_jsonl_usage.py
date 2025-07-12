"""
Example usage script for the WordNet Gloss JSONL Processor.

This script demonstrates various ways to convert XML data to JSONL format
and analyze the resulting data.
"""

from pathlib import Path
import json
import duckdb
from wn_gloss import WordNetGlossProcessor


def main():
    """Run example usage scenarios."""
    
    # File paths - adjust as needed
    WORDNET_DIR = "./old_gloss"
    JSONL_FILE = "./wordnet_glosses.jsonl"
    DTD_FILE = "./old_gloss/glosstag.dtd"
    
    print("WordNet Gloss JSONL Processor Example Usage")
    print("=" * 50)
    
    # Initialize processor
    processor = WordNetGlossProcessor(dtd_path=DTD_FILE)
    
    # Example 1: Convert XML to JSONL with DTD validation
    print("\n1. Converting XML to JSONL with DTD validation:")
    try:
        result = processor.convert_to_jsonl(
            input_dir=WORDNET_DIR,
            output_file=JSONL_FILE,
            validate_dtd=True,
            batch_size=1000
        )
        
        print(f"   ✅ Converted {result.synsets_processed} synsets")
        print(f"   ⏱️  Conversion time: {result.conversion_time:.2f}s")
        print(f"   📋 DTD validated: {result.dtd_validated}")
        
        if result.validation_errors:
            print(f"   ⚠️  Validation errors: {len(result.validation_errors)}")
            
    except Exception as e:
        print(f"   ❌ Conversion failed: {e}")
    
    # Example 2: Get JSONL statistics
    print("\n2. JSONL Data Statistics:")
    try:
        stats = processor.get_statistics(JSONL_FILE)
        
        print(f"   Total synsets: {stats['total_synsets']}")
        print(f"   Total annotations: {stats['total_annotations']}")
        
        print("\n   Synsets by Part of Speech:")
        for pos, count in stats['synsets_by_pos'].items():
            pos_names = {'n': 'Nouns', 'v': 'Verbs', 'a': 'Adjectives', 'r': 'Adverbs'}
            print(f"     {pos_names.get(pos, pos)}: {count:,}")
        
        print("\n   Average Gloss Lengths:")
        for pos, lengths in stats['avg_gloss_lengths'].items():
            print(f"     {pos}: {lengths['gloss_length']:.1f} chars, {lengths['token_count']:.1f} tokens")
            
    except Exception as e:
        print(f"   ❌ Statistics failed: {e}")
    
    # Example 3: Search for specific synsets
    print("\n3. Searching for synsets:")
    try:
        # Search by synset ID
        results = processor.search_jsonl(
            jsonl_file=JSONL_FILE,
            synset_id="n00003553",
            limit=1
        )
        
        if results:
            result = results[0]
            terms = ", ".join([t['term'] for t in result['terms']])
            print(f"   Synset {result['synset_id']}: {terms}")
            print(f"   Gloss: {result['gloss']['original_text'][:100]}...")
        
        # Search by term
        results = processor.search_jsonl(
            jsonl_file=JSONL_FILE,
            term="computer",
            limit=3
        )
        
        print(f"\n   Found {len(results)} synsets containing 'computer':")
        for result in results:
            terms = ", ".join([t['term'] for t in result['terms']])
            print(f"     {result['synset_id']}: {terms}")
            
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
    
    # Example 4: DuckDB Analytics
    print("\n4. DuckDB Analytics Examples:")
    try:
        # Count synsets by POS
        df = processor.analyze_with_duckdb(
            jsonl_file=JSONL_FILE,
            sql_query=f"""
            SELECT pos, COUNT(*) as count 
            FROM read_json_auto('{JSONL_FILE}') 
            GROUP BY pos ORDER BY count DESC
            """
        )
        print("   Synsets by POS:")
        for _, row in df.iterrows():
            print(f"     {row['pos']}: {row['count']:,}")
        
        # Find longest glosses
        df = processor.analyze_with_duckdb(
            jsonl_file=JSONL_FILE,
            sql_query=f"""
            SELECT synset_id, pos, LENGTH(gloss.original_text) as gloss_length
            FROM read_json_auto('{JSONL_FILE}')
            ORDER BY gloss_length DESC LIMIT 5
            """
        )
        print("\n   Longest glosses:")
        for _, row in df.iterrows():
            print(f"     {row['synset_id']} ({row['pos']}): {row['gloss_length']} chars")
        
        # Analyze annotations
        df = processor.analyze_with_duckdb(
            jsonl_file=JSONL_FILE,
            sql_query=f"""
            SELECT 
                pos,
                COUNT(*) as synsets,
                AVG(ARRAY_LENGTH(gloss.annotations)) as avg_annotations
            FROM read_json_auto('{JSONL_FILE}')
            GROUP BY pos
            ORDER BY avg_annotations DESC
            """
        )
        print("\n   Average annotations per synset by POS:")
        for _, row in df.iterrows():
            print(f"     {row['pos']}: {row['avg_annotations']:.2f} annotations")
            
    except Exception as e:
        print(f"   ❌ DuckDB analytics failed: {e}")
    
    # Example 5: Export to CSV
    print("\n5. Exporting data to CSV:")
    try:
        csv_file = "./wordnet_nouns_sample.csv"
        processor.export_to_csv(
            jsonl_file=JSONL_FILE,
            output_file=csv_file,
            sql_query=f"""
            SELECT 
                synset_id, 
                pos,
                gloss.original_text as gloss_text,
                ARRAY_LENGTH(gloss.tokens) as token_count,
                ARRAY_LENGTH(gloss.annotations) as annotation_count
            FROM read_json_auto('{JSONL_FILE}')
            WHERE pos = 'n'
            LIMIT 100
            """
        )
        print(f"   ✅ Exported noun sample to: {csv_file}")
        
    except Exception as e:
        print(f"   ❌ CSV export failed: {e}")
    
    # Example 6: Direct DuckDB queries
    print("\n6. Direct DuckDB Integration:")
    try:
        conn = duckdb.connect(":memory:")
        
        # Load JSONL into DuckDB table
        conn.execute(f"""
            CREATE TABLE wordnet_data AS 
            SELECT * FROM read_json_auto('{JSONL_FILE}')
        """)
        
        # Complex analytical query
        result = conn.execute("""
            SELECT 
                pos,
                COUNT(*) as synset_count,
                AVG(LENGTH(gloss.original_text)) as avg_gloss_length,
                MAX(LENGTH(gloss.original_text)) as max_gloss_length,
                AVG(ARRAY_LENGTH(gloss.tokens)) as avg_tokens,
                SUM(ARRAY_LENGTH(gloss.annotations)) as total_annotations
            FROM wordnet_data
            GROUP BY pos
            ORDER BY synset_count DESC
        """).fetchall()
        
        print("   Comprehensive analysis by POS:")
        headers = ["POS", "Synsets", "Avg Gloss", "Max Gloss", "Avg Tokens", "Total Annotations"]
        print(f"     {' | '.join(f'{h:>12}' for h in headers)}")
        print(f"     {'-' * 80}")
        
        for row in result:
            pos, count, avg_gloss, max_gloss, avg_tokens, annotations = row
            print(f"     {pos:>12} | {count:>12,} | {avg_gloss:>12.1f} | {max_gloss:>12} | {avg_tokens:>12.1f} | {annotations:>12}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Direct DuckDB integration failed: {e}")
    
    # Example 7: Schema validation
    print("\n7. JSONL Schema Validation:")
    try:
        errors = processor.validate_jsonl_schema(JSONL_FILE)
        
        if errors:
            print(f"   ⚠️  Found {len(errors)} schema errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"     - {error}")
            if len(errors) > 5:
                print(f"     ... and {len(errors) - 5} more errors")
        else:
            print("   ✅ JSONL schema validation passed!")
            
    except Exception as e:
        print(f"   ❌ Schema validation failed: {e}")
    
    print("\n" + "=" * 50)
    print("Example usage completed! 🎉")
    print(f"\nGenerated files:")
    print(f"  📄 JSONL data: {JSONL_FILE}")
    if Path("./wordnet_nouns_sample.csv").exists():
        print(f"  📊 CSV sample: ./wordnet_nouns_sample.csv")


if __name__ == "__main__":
    main()
