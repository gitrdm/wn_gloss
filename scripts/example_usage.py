#!/usr/bin/env python3
"""
Example usage script for the WordNet Gloss Database.

This script demonstrates various ways to query and interact with the
migrated WordNet gloss data.
"""

import json
from pathlib import Path
from wn_gloss import WordNetGlossDB


def main():
    """Main example function."""
    # Database connection - adjust as needed
    DATABASE_URL = "postgresql://user:password@localhost/wordnet_gloss"
    # DATABASE_URL = "sqlite:///wordnet_gloss.db"  # Alternative: SQLite
    
    print("WordNet Gloss Database Example Usage")
    print("=" * 50)
    
    # Initialize database connection
    db = WordNetGlossDB(DATABASE_URL)
    
    # Example 1: Get database statistics
    print("\n1. Database Statistics:")
    print("-" * 25)
    stats = db.get_statistics()
    print(f"Total synsets: {stats['total_synsets']:,}")
    print(f"Total glosses: {stats['total_glosses']:,}")
    print(f"Total tokens: {stats['total_tokens']:,}")
    print(f"Total annotations: {stats['total_annotations']:,}")
    print(f"Total collocations: {stats['total_collocations']:,}")
    print(f"Disambiguated tokens: {stats['disambiguated_tokens']:,}")
    
    # Example 2: Query synsets by part of speech
    print("\n2. Synsets by Part of Speech:")
    print("-" * 32)
    noun_synsets = db.get_synsets_by_pos("n")
    print(f"Found {len(noun_synsets)} noun synsets")
    
    if noun_synsets:
        # Show first few examples
        print("\nFirst 3 noun synsets:")
        for synset in noun_synsets[:3]:
            print(f"  {synset.id}: {[term.term for term in synset.terms]}")
    
    # Example 3: Find synsets containing specific terms
    print("\n3. Find Synsets by Term:")
    print("-" * 24)
    entity_synsets = db.find_synsets_by_term("entity")
    print(f"Found {len(entity_synsets)} synsets containing 'entity'")
    
    if entity_synsets:
        print("\nFirst 3 synsets with 'entity':")
        for synset in entity_synsets[:3]:
            print(f"  {synset.id}: {[term.term for term in synset.terms]}")
    
    # Example 4: Search glosses containing specific text
    print("\n4. Search Glosses by Text:")
    print("-" * 25)
    computer_glosses = db.find_glosses_containing("computer")
    print(f"Found {len(computer_glosses)} glosses containing 'computer'")
    
    if computer_glosses:
        print("\nFirst 2 glosses with 'computer':")
        for gloss in computer_glosses[:2]:
            print(f"  {gloss.synset_id}: {gloss.original_text[:80]}...")
    
    # Example 5: Get detailed synset information
    print("\n5. Detailed Synset Information:")
    print("-" * 32)
    synset = db.get_synset_by_id("n00003553")  # Example synset
    if synset:
        print(f"Synset: {synset.id} ({synset.pos})")
        print(f"Terms: {[term.term for term in synset.terms]}")
        print(f"Sense Keys: {[sk.sense_key for sk in synset.sense_keys]}")
        
        for gloss in synset.glosses:
            print(f"\nGloss: {gloss.original_text}")
            print(f"Tokens: {len(gloss.tokens)}")
            print(f"Annotations: {len([ann for token in gloss.tokens for ann in token.annotations])}")
            print(f"Collocations: {len(gloss.collocations)}")
            
            # Show some tokens
            if gloss.tokens:
                print("\nFirst 5 tokens:")
                for token in gloss.tokens[:5]:
                    print(f"  '{token.text}' ({token.pos}/{token.tag})")
            
            # Show collocations
            if gloss.collocations:
                print("\nCollocations:")
                for coll in gloss.collocations:
                    discon = " (discontiguous)" if coll.is_discontiguous else ""
                    print(f"  '{coll.text}' -> {coll.sense_key}{discon}")
    
    # Example 6: Complex search
    print("\n6. Complex Search:")
    print("-" * 17)
    results = db.search_complex(
        pos="n",
        text_contains="assemblage",
        limit=5
    )
    print(f"Found {len(results)} results for nouns containing 'assemblage'")
    
    for result in results:
        print(f"  {result['synset_id']}: {result['original_text'][:60]}...")
    
    # Example 7: Find collocations
    print("\n7. Find Collocations:")
    print("-" * 19)
    collocations = db.find_collocations_by_sense_key("regard_as%2:31:00::")
    print(f"Found {len(collocations)} collocations with sense key 'regard_as%2:31:00::'")
    
    for coll in collocations:
        print(f"  '{coll.text}' in synset {coll.gloss.synset_id}")
    
    # Example 8: Get disambiguated tokens
    print("\n8. Disambiguated Tokens:")
    print("-" * 22)
    disambiguated_tokens = db.get_disambiguated_tokens()
    print(f"Found {len(disambiguated_tokens)} disambiguated tokens")
    
    if disambiguated_tokens:
        print("\nFirst 5 disambiguated tokens:")
        for token in disambiguated_tokens[:5]:
            for ann in token.annotations:
                if ann.sense_key:
                    print(f"  '{token.text}' -> {ann.sense_key}")
                    break
    
    # Example 9: Export data to JSON
    print("\n9. Export Data:")
    print("-" * 13)
    export_file = Path("wordnet_sample.json")
    
    # Export first 5 noun synsets
    sample_synsets = [synset.id for synset in noun_synsets[:5]]
    db.export_to_json(export_file, synset_ids=sample_synsets)
    print(f"Exported {len(sample_synsets)} synsets to {export_file}")
    
    # Show exported data structure
    if export_file.exists():
        with open(export_file, 'r') as f:
            data = json.load(f)
            print(f"\nExported data structure preview:")
            if data:
                sample = data[0]
                print(f"  Synset: {sample['synset_id']}")
                print(f"  Terms: {sample['terms']}")
                print(f"  Glosses: {len(sample['glosses'])}")
                if sample['glosses']:
                    gloss = sample['glosses'][0]
                    print(f"  Tokens: {len(gloss['tokens'])}")
                    print(f"  Annotations: {len(gloss['annotations'])}")
                    print(f"  Collocations: {len(gloss['collocations'])}")
    
    # Example 10: Validate data integrity
    print("\n10. Data Integrity Validation:")
    print("-" * 31)
    report = db.validate_data_integrity()
    
    issues = sum([
        report['orphaned_glosses'],
        report['orphaned_tokens'],
        report['orphaned_annotations'],
        report['orphaned_collocations'],
        report['synsets_without_glosses'],
        report['tokens_without_text'],
        report['annotations_without_sense_keys']
    ])
    
    if issues == 0:
        print("✅ Database integrity is good!")
    else:
        print(f"⚠️  Found {issues} potential issues")
        for key, value in report.items():
            if value > 0 and key != 'total_synsets':
                print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\n" + "=" * 50)
    print("EXAMPLE USAGE COMPLETED!")
    print("=" * 50)


if __name__ == "__main__":
    main()
