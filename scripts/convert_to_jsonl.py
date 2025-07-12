"""
JSONL conversion script for WordNet Gloss Disambiguation Project data.

This script demonstrates how to convert XML data to JSONL format
with comprehensive DTD validation and analysis.
"""

import argparse
import sys
import time
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wn_gloss import WordNetGlossProcessor


def main():
    """Convert WordNet XML data to JSONL format."""
    parser = argparse.ArgumentParser(
        description="Convert WordNet Gloss Disambiguation Project data to JSONL"
    )
    
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Input directory containing WordNet XML files"
    )
    
    parser.add_argument(
        "--output-file",
        required=True,
        help="Output JSONL file path"
    )
    
    parser.add_argument(
        "--dtd-path",
        help="Path to DTD file for validation"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for processing (default: 1000)"
    )
    
    parser.add_argument(
        "--validate-dtd",
        action="store_true",
        help="Enable DTD validation during conversion"
    )
    
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics for existing JSONL file"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate input paths
    input_path = Path(args.input_dir)
    output_path = Path(args.output_file)
    
    if not args.stats_only and not input_path.exists():
        print(f"❌ Error: Input directory {args.input_dir} does not exist")
        return 1
    
    if args.dtd_path and not Path(args.dtd_path).exists():
        print(f"❌ Error: DTD file {args.dtd_path} does not exist")
        return 1
    
    # Initialize processor
    processor = WordNetGlossProcessor(dtd_path=args.dtd_path)
    
    if args.stats_only:
        # Just show statistics for existing JSONL file
        if not output_path.exists():
            print(f"❌ Error: JSONL file {args.output_file} does not exist")
            return 1
        
        print(f"📊 Analyzing JSONL file: {args.output_file}")
        try:
            stats = processor.get_statistics(output_path)
            print_statistics(stats)
            return 0
        except Exception as e:
            print(f"❌ Error analyzing JSONL file: {e}")
            return 1
    
    # Perform conversion
    print(f"🔄 Converting XML data to JSONL format")
    print(f"   Input:  {args.input_dir}")
    print(f"   Output: {args.output_file}")
    print(f"   DTD validation: {'✅ Enabled' if args.validate_dtd else '❌ Disabled'}")
    if args.dtd_path:
        print(f"   DTD file: {args.dtd_path}")
    print(f"   Batch size: {args.batch_size}")
    
    try:
        start_time = time.time()
        
        result = processor.convert_to_jsonl(
            input_dir=input_path,
            output_file=output_path,
            validate_dtd=args.validate_dtd,
            batch_size=args.batch_size
        )
        
        total_time = time.time() - start_time
        
        print("\n✅ Conversion completed successfully!")
        print(f"   📈 Synsets processed: {result.synsets_processed:,}")
        print(f"   ⏱️  Total time: {total_time:.2f}s")
        print(f"   🚀 Processing rate: {result.synsets_processed / total_time:.1f} synsets/sec")
        print(f"   💾 Output file: {result.output_file}")
        
        if result.validation_errors:
            print(f"   ⚠️  Validation errors: {len(result.validation_errors)}")
            if args.verbose:
                print("\n   Error details:")
                for error in result.validation_errors[:10]:  # Show first 10 errors
                    print(f"     - {error}")
                if len(result.validation_errors) > 10:
                    print(f"     ... and {len(result.validation_errors) - 10} more errors")
        
        # Show basic statistics
        print("\n📊 JSONL Data Statistics:")
        try:
            stats = processor.get_statistics(output_path)
            print_statistics(stats)
        except Exception as e:
            print(f"   ⚠️  Could not generate statistics: {e}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def print_statistics(stats):
    """Print statistics in a formatted way."""
    print(f"   Total synsets: {stats['total_synsets']:,}")
    print(f"   Total annotations: {stats['total_annotations']:,}")
    
    print("\n   Synsets by Part of Speech:")
    pos_names = {'n': 'Nouns', 'v': 'Verbs', 'a': 'Adjectives', 'r': 'Adverbs'}
    for pos, count in sorted(stats['synsets_by_pos'].items(), key=lambda x: x[1], reverse=True):
        print(f"     {pos_names.get(pos, pos):>12}: {count:>8,} ({count/stats['total_synsets']*100:5.1f}%)")
    
    print("\n   Average Gloss Characteristics:")
    for pos, data in sorted(stats['avg_gloss_lengths'].items()):
        print(f"     {pos}: {data['gloss_length']:5.1f} chars, {data['token_count']:5.1f} tokens")


if __name__ == "__main__":
    sys.exit(main())
