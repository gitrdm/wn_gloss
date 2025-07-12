"""
Command-line interface for the WordNet Gloss package.

This module provides CLI commands for converting XML to JSONL, querying,
and analyzing WordNet gloss data.
"""

import click
import json
import logging
from pathlib import Path
from typing import Optional

from .jsonl_processor import WordNetGlossProcessor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def cli():
    """WordNet Gloss JSONL Management CLI."""
    pass

@cli.command()
@click.option('--input', 'input_dir', required=True, help='Path to WordNet XML directory')
@click.option('--output', 'output_file', required=True, help='Output JSONL file path')
@click.option('--validate-dtd', is_flag=True, help='Enable DTD validation during conversion')
@click.option('--dtd', 'dtd_path', help='Path to DTD file for validation')
@click.option('--batch-size', default=1000, help='Batch size for processing')
def convert(input_dir: str, output_file: str, validate_dtd: bool, dtd_path: Optional[str], batch_size: int):
    """Convert WordNet XML files to JSONL format with optional DTD validation."""
    input_path = Path(input_dir)
    output_path = Path(output_file)
    
    if not input_path.exists():
        click.echo(f"Error: Input directory {input_dir} does not exist")
        return
    
    click.echo(f"Converting XML data from {input_dir} to JSONL format: {output_file}")
    
    # Initialize processor
    processor = WordNetGlossProcessor(dtd_path=dtd_path)
    
    try:
        result = processor.convert_to_jsonl(
            input_dir=input_path,
            output_file=output_path,
            validate_dtd=validate_dtd,
            batch_size=batch_size
        )
        
        click.echo("Conversion completed successfully!")
        click.echo(f"  Synsets processed: {result.synsets_processed}")
        click.echo(f"  Conversion time: {result.conversion_time:.2f}s")
        click.echo(f"  DTD validated: {result.dtd_validated}")
        
        if result.validation_errors:
            click.echo(f"  Validation errors: {len(result.validation_errors)}")
            for error in result.validation_errors[:5]:  # Show first 5 errors
                click.echo(f"    - {error}")
            if len(result.validation_errors) > 5:
                click.echo(f"    ... and {len(result.validation_errors) - 5} more errors")
        
    except Exception as e:
        click.echo(f"Error during conversion: {e}")
        logger.error(f"Conversion failed: {e}")


@cli.command()
@click.option('--jsonl', 'jsonl_file', required=True, help='Path to JSONL file')
@click.option('--sql', 'sql_query', required=True, help='SQL query to execute with DuckDB')
def query(jsonl_file: str, sql_query: str):
    """Query JSONL data using DuckDB SQL."""
    jsonl_path = Path(jsonl_file)
    
    if not jsonl_path.exists():
        click.echo(f"Error: JSONL file {jsonl_file} does not exist")
        return
    
    processor = WordNetGlossProcessor()
    
    try:
        result = processor.analyze_with_duckdb(jsonl_path, sql_query)
        click.echo("Query Results:")
        click.echo(result.to_string(index=False))
        
    except Exception as e:
        click.echo(f"Error executing query: {e}")
        logger.error(f"Query failed: {e}")


@cli.command()
@click.option('--jsonl', 'jsonl_file', required=True, help='Path to JSONL file')
@click.option('--synset-id', help='Search for specific synset ID')
@click.option('--pos', help='Filter by part of speech (n, v, a, r)')
@click.option('--term', help='Search for term in synset')
@click.option('--limit', default=10, help='Maximum number of results')
@click.option('--output-format', default='table', type=click.Choice(['table', 'json']), help='Output format')
def search(jsonl_file: str, synset_id: Optional[str], pos: Optional[str], 
           term: Optional[str], limit: int, output_format: str):
    """Search for synsets in JSONL data."""
    jsonl_path = Path(jsonl_file)
    
    if not jsonl_path.exists():
        click.echo(f"Error: JSONL file {jsonl_file} does not exist")
        return
    
    processor = WordNetGlossProcessor()
    
    try:
        results = processor.search_jsonl(
            jsonl_file=jsonl_path,
            synset_id=synset_id,
            pos=pos,
            term=term,
            limit=limit
        )
        
        if not results:
            click.echo("No results found")
            return
        
        if output_format == 'json':
            click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            click.echo(f"Found {len(results)} results:")
            for result in results:
                terms_str = ", ".join([t['term'] for t in result.get('terms', [])])
                click.echo(f"  {result['synset_id']} ({result['pos']}): {terms_str}")
                click.echo(f"    Gloss: {result['gloss']['original_text'][:100]}...")
                click.echo()
        
    except Exception as e:
        click.echo(f"Error during search: {e}")
        logger.error(f"Search failed: {e}")


@cli.command()
@click.option('--input', 'input_dir', required=True, help='Path to WordNet XML directory')
@click.option('--dtd', 'dtd_path', help='Path to DTD file')
@click.option('--report-errors', is_flag=True, help='Show detailed error report')
def validate(input_dir: str, dtd_path: Optional[str], report_errors: bool):
    """Validate XML files against DTD without conversion."""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        click.echo(f"Error: Input directory {input_dir} does not exist")
        return
    
    if dtd_path and not Path(dtd_path).exists():
        click.echo(f"Error: DTD file {dtd_path} does not exist")
        return
    
    click.echo(f"Validating XML files in {input_dir}")
    
    # Use the existing DTD validation from parser
    from .parser import parse_wordnet_directory
    
    try:
        # This will validate but not convert
        gloss_data = list(parse_wordnet_directory(
            str(input_path),
            dtd_path=dtd_path,
            validate_dtd=True
        ))
        
        click.echo(f"Validation completed successfully!")
        click.echo(f"  Files processed: {len(gloss_data)}")
        
    except Exception as e:
        click.echo(f"Validation failed: {e}")
        logger.error(f"Validation error: {e}")


@cli.command()
@click.option('--jsonl', 'jsonl_file', required=True, help='Path to JSONL file')
@click.option('--output', 'output_file', help='Output file for analysis results')
@click.option('--include-stats', is_flag=True, help='Include comprehensive statistics')
def analyze(jsonl_file: str, output_file: Optional[str], include_stats: bool):
    """Analyze JSONL data and generate statistics."""
    jsonl_path = Path(jsonl_file)
    
    if not jsonl_path.exists():
        click.echo(f"Error: JSONL file {jsonl_file} does not exist")
        return
    
    processor = WordNetGlossProcessor()
    
    try:
        stats = processor.get_statistics(jsonl_path)
        
        click.echo("JSONL Data Analysis:")
        click.echo(f"  Total synsets: {stats['total_synsets']}")
        click.echo(f"  Total annotations: {stats['total_annotations']}")
        
        click.echo("\nSynsets by Part of Speech:")
        for pos, count in stats['synsets_by_pos'].items():
            pos_names = {'n': 'Nouns', 'v': 'Verbs', 'a': 'Adjectives', 'r': 'Adverbs'}
            click.echo(f"  {pos_names.get(pos, pos)}: {count}")
        
        if include_stats:
            click.echo("\nAverage Gloss Lengths:")
            for pos, lengths in stats['avg_gloss_lengths'].items():
                click.echo(f"  {pos}: {lengths['gloss_length']:.1f} chars, {lengths['token_count']:.1f} tokens")
        
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w') as f:
                json.dump(stats, f, indent=2)
            click.echo(f"\nAnalysis results saved to: {output_file}")
        
    except Exception as e:
        click.echo(f"Error during analysis: {e}")
        logger.error(f"Analysis failed: {e}")


@cli.command()
@click.option('--jsonl', 'jsonl_file', required=True, help='Path to JSONL file')
@click.option('--output', 'output_file', required=True, help='Output CSV file')
@click.option('--sql', 'sql_query', help='Custom SQL query for export')
def export(jsonl_file: str, output_file: str, sql_query: Optional[str]):
    """Export JSONL data to CSV format."""
    jsonl_path = Path(jsonl_file)
    output_path = Path(output_file)
    
    if not jsonl_path.exists():
        click.echo(f"Error: JSONL file {jsonl_file} does not exist")
        return
    
    processor = WordNetGlossProcessor()
    
    try:
        processor.export_to_csv(
            jsonl_file=jsonl_path,
            output_file=output_path,
            sql_query=sql_query
        )
        click.echo(f"Data exported successfully to: {output_file}")
        
    except Exception as e:
        click.echo(f"Error during export: {e}")
        logger.error(f"Export failed: {e}")

if __name__ == "__main__":
    cli()
