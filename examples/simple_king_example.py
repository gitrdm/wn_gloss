#!/usr/bin/env python3
"""
Simple DuckDB Example: King Definitions with Related Word Synsets
This shows how to find definitions of "king" and the synsets of key words used in those definitions.
"""

import duckdb

def main():
    # Connect to DuckDB
    conn = duckdb.connect(':memory:')
    jsonl_path = '/home/rdmerrio/lgits/wn_gloss/old_gloss/json_file/wordnet.jsonl'
    
    print("🔍 QUERY EXAMPLE: King Definitions with Related Synsets")
    print("=" * 70)
    
    # Query 1: Find all "king" synsets
    print("\n1️⃣  All definitions of 'king':")
    print("-" * 40)
    
    king_results = conn.execute('''
        SELECT synset_id, pos, gloss.original_text as definition
        FROM read_json_auto(?) w
        WHERE list_contains(list_transform(w.terms, x -> x.term), 'king')
        ORDER BY synset_id;
    ''', [jsonl_path]).fetchall()
    
    for synset_id, pos, definition in king_results:
        print(f"• {synset_id} ({pos}): {definition}")
    
    # Query 2: Find synsets for specific words used in king definitions
    print(f"\n2️⃣  Synsets for key words used to define 'king':")
    print("-" * 50)
    
    key_words = ['male', 'sovereign', 'ruler', 'kingdom', 'piece', 'competitor']
    
    for word in key_words:
        print(f"\n🔸 Synsets containing '{word}':")
        
        word_synsets = conn.execute('''
            SELECT synset_id, pos, gloss.original_text as definition
            FROM read_json_auto(?) w
            WHERE list_contains(list_transform(w.terms, x -> x.term), ?)
            ORDER BY synset_id
            LIMIT 3;
        ''', [jsonl_path, word]).fetchall()
        
        for synset_id, pos, definition in word_synsets:
            # Truncate long definitions
            short_def = definition[:80] + "..." if len(definition) > 80 else definition
            print(f"   {synset_id} ({pos}): {short_def}")
    
    # Query 3: Combined query showing relationships
    print(f"\n3️⃣  Example combined query (for the most common sense - 'male sovereign'):")
    print("-" * 60)
    
    combined_result = conn.execute('''
        WITH king_main AS (
            SELECT synset_id, gloss.original_text as definition
            FROM read_json_auto(?) w
            WHERE list_contains(list_transform(w.terms, x -> x.term), 'king')
              AND synset_id = 'n10231515'  -- male sovereign sense
        )
        SELECT 
            k.synset_id as king_synset,
            k.definition as king_definition,
            w.synset_id as related_synset,
            list_transform(w.terms, x -> x.term)[1] as related_term,
            w.gloss.original_text as related_definition
        FROM king_main k
        CROSS JOIN read_json_auto(?) w
        WHERE list_contains(list_transform(w.terms, x -> x.term), 'male')
           OR list_contains(list_transform(w.terms, x -> x.term), 'sovereign')
           OR list_contains(list_transform(w.terms, x -> x.term), 'ruler')
           OR list_contains(list_transform(w.terms, x -> x.term), 'kingdom')
        ORDER BY w.synset_id
        LIMIT 8;
    ''', [jsonl_path, jsonl_path]).fetchall()
    
    if combined_result:
        king_synset, king_def = combined_result[0][0], combined_result[0][1]
        print(f"King synset: {king_synset}")
        print(f"Definition: {king_def}")
        print(f"\nRelated synsets (words used in definition):")
        
        for _, _, related_synset, related_term, related_def in combined_result:
            short_def = related_def[:60] + "..." if len(related_def) > 60 else related_def
            print(f"• {related_synset}: {related_term} → {short_def}")
    
    print(f"\n" + "=" * 70)
    print("💡 HOW TO USE THIS PATTERN:")
    print("1. Find target word synsets (e.g., 'king')")
    print("2. Extract key words from their definitions")
    print("3. Query for synsets containing those key words")
    print("4. This reveals the semantic network around your target concept")

if __name__ == "__main__":
    main()
