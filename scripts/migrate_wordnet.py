#!/usr/bin/env python3
"""
Migration script for WordNet Gloss Disambiguation Project data.

This script demonstrates how to migrate XML data to a modern database format.
"""

import argparse
import logging
import sys
from pathlib import Path

from wn_gloss import WordNetGlossDB


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate WordNet Gloss Disambiguation Project data to database"
    )
    parser.add_argument(
        "--wordnet-dir",
        required=True,
        help="Path to WordNet directory (containing merged/ or standoff/ subdirectories)"
    )
    parser.add_argument(
        "--database-url",
        required=True,
        help="Database connection URL (e.g., postgresql://user:pass@localhost/dbname)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for database inserts (default: 100)"
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing tables before migration"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate data integrity after migration"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Validate WordNet directory
    wordnet_path = Path(args.wordnet_dir)
    if not wordnet_path.exists():
        logger.error(f"WordNet directory does not exist: {wordnet_path}")
        sys.exit(1)
    
    # Check for expected subdirectories
    has_merged = (wordnet_path / "merged").exists()
    has_standoff = (wordnet_path / "standoff").exists()
    
    if not has_merged and not has_standoff:
        logger.error(f"WordNet directory must contain 'merged' or 'standoff' subdirectory")
        sys.exit(1)
    
    if has_merged:
        logger.info(f"Found merged format in {wordnet_path / 'merged'}")
    if has_standoff:
        logger.info(f"Found standoff format in {wordnet_path / 'standoff'}")
    
    try:
        # Initialize database
        logger.info(f"Connecting to database: {args.database_url}")
        db = WordNetGlossDB(args.database_url)
        
        # Drop existing tables if requested
        if args.drop_existing:
            logger.info("Dropping existing tables...")
            db.drop_tables()
        
        # Create tables
        logger.info("Creating database tables...")
        db.create_tables()
        
        # Migrate data
        logger.info(f"Starting migration from {wordnet_path}")
        logger.info(f"Batch size: {args.batch_size}")
        
        db.migrate_from_wordnet(wordnet_path, batch_size=args.batch_size)
        
        # Get statistics
        logger.info("Migration completed! Getting statistics...")
        stats = db.get_statistics()
        
        print("\n" + "="*50)
        print("MIGRATION SUMMARY")
        print("="*50)
        print(f"Total synsets: {stats['total_synsets']:,}")
        print(f"Total glosses: {stats['total_glosses']:,}")
        print(f"Total tokens: {stats['total_tokens']:,}")
        print(f"Total annotations: {stats['total_annotations']:,}")
        print(f"Total collocations: {stats['total_collocations']:,}")
        print(f"Disambiguated tokens: {stats['disambiguated_tokens']:,}")
        
        print("\nSynsets by Part of Speech:")
        pos_names = {'n': 'Nouns', 'v': 'Verbs', 'a': 'Adjectives', 'r': 'Adverbs'}
        for pos, count in stats['synsets_by_pos'].items():
            print(f"  {pos_names.get(pos, pos)}: {count:,}")
        
        # Validate data integrity if requested
        if args.validate:
            logger.info("Validating data integrity...")
            report = db.validate_data_integrity()
            
            print("\nData Integrity Report:")
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
                print(f"⚠️  Found {issues} potential issues:")
                for key, value in report.items():
                    if value > 0 and key != 'total_synsets':
                        print(f"  {key.replace('_', ' ').title()}: {value}")
        
        print("\n" + "="*50)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
