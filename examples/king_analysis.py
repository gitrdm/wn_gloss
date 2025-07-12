#!/usr/bin/env python3
"""
King Definition Analysis with DuckDB
Shows all definitions of "king" and finds synsets for words used in those definitions.
"""

import duckdb
import json
import re
from collections import defaultdict

def analyze_king_definitions():
    # Connect to DuckDB
    conn = duckdb.connect(':memory:')
    
    jsonl_path = '/home/rdmerrio/lgits/wn_gloss/old_gloss/json_file/wordnet.jsonl'
    
    print("=" * 80)
    print("KING DEFINITION ANALYSIS")
    print("=" * 80)
    
    # Step 1: Find all synsets containing "king" as a term
    print("\n1. All synsets containing 'king' as a term:")
    print("-" * 50)
    
    king_synsets = conn.execute('''
        SELECT synset_id, pos, 
               gloss.original_text as definition,
               gloss.annotations as annotations
        FROM read_json_auto(?) w
        WHERE list_contains(list_transform(w.terms, x -> x.term), 'king')
        ORDER BY synset_id;
    ''', [jsonl_path]).fetchall()
    
    # Store definition words for lookup
    definition_words = set()
    
    for i, (synset_id, pos, definition, annotations) in enumerate(king_synsets, 1):
        print(f"\n{i}. Synset: {synset_id} ({pos})")
        print(f"   Definition: {definition}")
        
        # Extract words from definition (simple tokenization)
        words = re.findall(r'\b[a-zA-Z]+\b', definition.lower())
        # Filter out common words
        significant_words = [w for w in words if len(w) > 3 and w not in {
            'that', 'which', 'with', 'from', 'have', 'been', 'this', 
            'they', 'their', 'where', 'when', 'what', 'very', 'most',
            'some', 'only', 'also', 'each', 'more', 'than', 'such'
        }]
        definition_words.update(significant_words)
        print(f"   Key words: {', '.join(significant_words)}")
    
    # Step 2: Find synsets for words used in king definitions
    print(f"\n\n2. Finding synsets for words used in king definitions:")
    print("-" * 50)
    
    # Convert set to list for SQL query
    word_list = list(definition_words)[:20]  # Limit to first 20 for readability
    
    if word_list:
        # Create a SQL query to find synsets containing these words
        placeholders = ','.join(['?' for _ in word_list])
        
        related_synsets = conn.execute(f'''
            SELECT DISTINCT w.synset_id, w.pos, 
                   list_transform(w.terms, x -> x.term) as terms,
                   w.gloss.original_text as definition
            FROM read_json_auto(?) w
            WHERE EXISTS (
                SELECT 1 FROM unnest(w.terms) as t(term_info)
                WHERE term_info.term IN ({placeholders})
            )
            ORDER BY w.synset_id
            LIMIT 15;
        ''', [jsonl_path] + word_list).fetchall()
        
        print(f"\nFound {len(related_synsets)} synsets containing words from king definitions:")
        
        for synset_id, pos, terms, definition in related_synsets:
            matching_words = [term for term in terms if term.lower() in definition_words]
            print(f"\n• Synset: {synset_id} ({pos})")
            print(f"  Terms: {', '.join(terms)}")
            print(f"  Matching words: {', '.join(matching_words)}")
            print(f"  Definition: {definition[:100]}{'...' if len(definition) > 100 else ''}")
    
    # Step 3: Create a focused example for the most common definition
    print(f"\n\n3. Detailed analysis for 'male sovereign; ruler of a kingdom' (n10231515):")
    print("-" * 50)
    
    # Find synsets for specific words: male, sovereign, ruler, kingdom
    focus_words = ['male', 'sovereign', 'ruler', 'kingdom']
    
    for word in focus_words:
        word_synsets = conn.execute('''
            SELECT synset_id, pos, 
                   list_transform(terms, x -> x.term) as terms,
                   gloss.original_text as definition
            FROM read_json_auto(?) w
            WHERE list_contains(list_transform(w.terms, x -> x.term), ?)
            LIMIT 3;
        ''', [jsonl_path, word]).fetchall()
        
        print(f"\n🔍 Synsets for '{word}':")
        for synset_id, pos, terms, definition in word_synsets:
            print(f"   {synset_id} ({pos}): {', '.join(terms)}")
            print(f"   → {definition}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"• Found {len(king_synsets)} different senses of 'king'")
    print(f"• Extracted {len(definition_words)} unique words from king definitions")
    print(f"• These words help understand the semantic field around 'king'")
    print("• Key concepts: authority, games, hierarchy, leadership, dominance")

if __name__ == "__main__":
    analyze_king_definitions()
