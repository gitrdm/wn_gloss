"""
Command-line interface for the WordNet Gloss package.

This module provides CLI commands for migrating, querying, and managing
WordNet gloss data.
"""

import click
import json
import logging
from pathlib import Path
from typing import Optional

from .database import WordNetGlossDB


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def cli():
    """WordNet Gloss Database Management CLI."""
    pass


@cli.command()
@click.option('--database-url', required=True, help='Database connection URL')
@click.option('--wordnet-dir', required=True, help='Path to WordNet directory')
@click.option('--batch-size', default=100, help='Batch size for migration')
@click.option('--drop-existing', is_flag=True, help='Drop existing tables before migration')
def migrate(database_url: str, wordnet_dir: str, batch_size: int, drop_existing: bool):
    """Migrate WordNet data to database."""
    wordnet_path = Path(wordnet_dir)
    
    if not wordnet_path.exists():
        click.echo(f"Error: WordNet directory {wordnet_dir} does not exist")
        return
    
    click.echo(f"Connecting to database: {database_url}")
    db = WordNetGlossDB(database_url)
    
    if drop_existing:
        click.echo("Dropping existing tables...")
        db.drop_tables()
    
    click.echo("Creating tables...")
    db.create_tables()
    
    click.echo(f"Starting migration from {wordnet_dir} (batch size: {batch_size})")
    
    try:
        db.migrate_from_wordnet(wordnet_path, batch_size=batch_size)
        click.echo("Migration completed successfully!")
        
        # Show statistics
        stats = db.get_statistics()
        click.echo(f"\nDatabase Statistics:")
        click.echo(f"  Total synsets: {stats['total_synsets']}")
        click.echo(f"  Total glosses: {stats['total_glosses']}")
        click.echo(f"  Total tokens: {stats['total_tokens']}")
        click.echo(f"  Total annotations: {stats['total_annotations']}")
        click.echo(f"  Total collocations: {stats['total_collocations']}")
        click.echo(f"  Disambiguated tokens: {stats['disambiguated_tokens']}")
        
    except Exception as e:
        click.echo(f"Error during migration: {e}")
        logger.error(f"Migration failed: {e}")


@cli.command()
@click.option('--database-url', required=True, help='Database connection URL')
def stats(database_url: str):
    """Show database statistics."""
    db = WordNetGlossDB(database_url)
    
    try:
        stats = db.get_statistics()
        
        click.echo("Database Statistics:")
        click.echo(f"  Total synsets: {stats['total_synsets']}")
        click.echo(f"  Total glosses: {stats['total_glosses']}")
        click.echo(f"  Total tokens: {stats['total_tokens']}")
        click.echo(f"  Total annotations: {stats['total_annotations']}")
        click.echo(f"  Total collocations: {stats['total_collocations']}")
        click.echo(f"  Disambiguated tokens: {stats['disambiguated_tokens']}")
        
        click.echo("\nSynsets by Part of Speech:")
        for pos, count in stats['synsets_by_pos'].items():
            pos_names = {'n': 'Nouns', 'v': 'Verbs', 'a': 'Adjectives', 'r': 'Adverbs'}
            click.echo(f"  {pos_names.get(pos, pos)}: {count}")
        
        click.echo("\nTokens by Part of Speech:")
        for pos, count in stats['tokens_by_pos'].items():
            pos_names = {'n': 'Nouns', 'v': 'Verbs', 'a': 'Adjectives', 'r': 'Adverbs'}
            click.echo(f"  {pos_names.get(pos, pos)}: {count}")
        
    except Exception as e:
        click.echo(f"Error getting statistics: {e}")
        logger.error(f"Statistics query failed: {e}")


@cli.command()
@click.option('--database-url', required=True, help='Database connection URL')
@click.option('--synset-id', help='Synset ID to search for')
@click.option('--pos', help='Part of speech (n, v, a, r)')
@click.option('--term', help='Term to search for')
@click.option('--sense-key', help='Sense key to search for')
@click.option('--text-contains', help='Text to search for in glosses')
@click.option('--limit', default=10, help='Maximum number of results')
@click.option('--output-format', default='text', type=click.Choice(['text', 'json']), help='Output format')
def search(database_url: str, synset_id: Optional[str], pos: Optional[str], 
           term: Optional[str], sense_key: Optional[str], text_contains: Optional[str],
           limit: int, output_format: str):
    """Search WordNet gloss data."""
    db = WordNetGlossDB(database_url)
    
    try:
        results = db.search_complex(
            synset_id=synset_id,
            pos=pos,
            term=term,
            sense_key=sense_key,
            text_contains=text_contains,
            limit=limit
        )
        
        if output_format == 'json':
            click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            click.echo(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                click.echo(f"\n{i}. Synset: {result['synset_id']} ({result['pos']})")
                click.echo(f"   Offset: {result['offset']}")
                click.echo(f"   Original: {result['original_text'][:200]}...")
                
    except Exception as e:
        click.echo(f"Error performing search: {e}")
        logger.error(f"Search query failed: {e}")


@cli.command()
@click.option('--database-url', required=True, help='Database connection URL')
@click.option('--synset-id', required=True, help='Synset ID to query')
@click.option('--include-tokens', is_flag=True, help='Include token details')
@click.option('--include-annotations', is_flag=True, help='Include annotation details')
@click.option('--include-collocations', is_flag=True, help='Include collocation details')
def synset(database_url: str, synset_id: str, include_tokens: bool, 
           include_annotations: bool, include_collocations: bool):
    """Get detailed information about a synset."""
    db = WordNetGlossDB(database_url)
    
    try:
        synset_obj = db.get_synset_by_id(synset_id)
        
        if not synset_obj:
            click.echo(f"Synset {synset_id} not found")
            return
        
        click.echo(f"Synset: {synset_obj.id}")
        click.echo(f"Part of Speech: {synset_obj.pos}")
        click.echo(f"Offset: {synset_obj.offset}")
        
        click.echo(f"\nTerms:")
        for term in synset_obj.terms:
            click.echo(f"  - {term.term}")
        
        click.echo(f"\nSense Keys:")
        for sk in synset_obj.sense_keys:
            click.echo(f"  - {sk.sense_key}")
        
        for gloss in synset_obj.glosses:
            click.echo(f"\nGloss:")
            click.echo(f"  Original: {gloss.original_text}")
            click.echo(f"  Tokenized: {gloss.tokenized_text}")
            
            if include_tokens:
                click.echo(f"\n  Tokens ({len(gloss.tokens)}):")
                for token in gloss.tokens[:20]:  # Limit to first 20
                    click.echo(f"    {token.token_id}: '{token.text}' ({token.pos}/{token.tag})")
                if len(gloss.tokens) > 20:
                    click.echo(f"    ... and {len(gloss.tokens) - 20} more")
            
            if include_annotations:
                annotations = [ann for token in gloss.tokens for ann in token.annotations]
                if annotations:
                    click.echo(f"\n  Annotations ({len(annotations)}):")
                    for ann in annotations[:10]:  # Limit to first 10
                        click.echo(f"    {ann.annotation_id}: {ann.sense_key}")
                    if len(annotations) > 10:
                        click.echo(f"    ... and {len(annotations) - 10} more")
            
            if include_collocations:
                if gloss.collocations:
                    click.echo(f"\n  Collocations ({len(gloss.collocations)}):")
                    for coll in gloss.collocations:
                        discon = " (discontiguous)" if coll.is_discontiguous else ""
                        click.echo(f"    {coll.collocation_id}: '{coll.text}' -> {coll.sense_key}{discon}")
        
    except Exception as e:
        click.echo(f"Error querying synset: {e}")
        logger.error(f"Synset query failed: {e}")


@cli.command()
@click.option('--database-url', required=True, help='Database connection URL')
@click.option('--output-file', required=True, help='Output JSON file path')
@click.option('--synset-ids', help='Comma-separated list of synset IDs to export')
@click.option('--pos', help='Part of speech to export (n, v, a, r)')
@click.option('--limit', help='Maximum number of synsets to export')
def export(database_url: str, output_file: str, synset_ids: Optional[str], 
           pos: Optional[str], limit: Optional[int]):
    """Export WordNet data to JSON format."""
    db = WordNetGlossDB(database_url)
    
    try:
        if synset_ids:
            synset_id_list = [s.strip() for s in synset_ids.split(',')]
        else:
            synset_id_list = None
        
        if pos:
            # Get synsets by part of speech
            synsets = db.get_synsets_by_pos(pos)
            if limit:
                synsets = synsets[:limit]
            synset_id_list = [s.id for s in synsets]
        
        click.echo(f"Exporting to {output_file}...")
        db.export_to_json(output_file, synset_id_list)
        click.echo("Export completed successfully!")
        
    except Exception as e:
        click.echo(f"Error during export: {e}")
        logger.error(f"Export failed: {e}")


@cli.command()
@click.option('--database-url', required=True, help='Database connection URL')
def validate(database_url: str):
    """Validate database integrity."""
    db = WordNetGlossDB(database_url)
    
    try:
        report = db.validate_data_integrity()
        
        click.echo("Data Integrity Report:")
        click.echo(f"  Total synsets: {report['total_synsets']}")
        click.echo(f"  Orphaned glosses: {report['orphaned_glosses']}")
        click.echo(f"  Orphaned tokens: {report['orphaned_tokens']}")
        click.echo(f"  Orphaned annotations: {report['orphaned_annotations']}")
        click.echo(f"  Orphaned collocations: {report['orphaned_collocations']}")
        click.echo(f"  Synsets without glosses: {report['synsets_without_glosses']}")
        click.echo(f"  Tokens without text: {report['tokens_without_text']}")
        click.echo(f"  Annotations without sense keys: {report['annotations_without_sense_keys']}")
        
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
            click.echo("\n✅ Database integrity is good!")
        else:
            click.echo(f"\n⚠️  Found {issues} potential issues")
        
    except Exception as e:
        click.echo(f"Error validating database: {e}")
        logger.error(f"Validation failed: {e}")


@cli.command()
@click.option('--database-url', required=True, help='Database connection URL')
@click.option('--confirm', is_flag=True, help='Confirm deletion')
def drop(database_url: str, confirm: bool):
    """Drop all database tables."""
    if not confirm:
        click.echo("Use --confirm flag to confirm deletion of all tables")
        return
    
    db = WordNetGlossDB(database_url)
    
    try:
        db.drop_tables()
        click.echo("All tables dropped successfully!")
        
    except Exception as e:
        click.echo(f"Error dropping tables: {e}")
        logger.error(f"Drop tables failed: {e}")


if __name__ == '__main__':
    cli()
