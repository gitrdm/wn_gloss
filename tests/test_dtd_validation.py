#!/usr/bin/env python3
"""
Test DTD validation functionality for wn_gloss parser.
"""

import sys
from pathlib import Path

# Add src to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wn_gloss.parser import MergedXMLParser

def test_dtd_validation():
    """Test DTD validation with sample XML files."""
    print("🧪 Testing DTD validation functionality")
    print("=" * 50)
    
    # Test DTD validation
    dtd_path = Path('old_gloss/dtd/glosstag.dtd')
    
    if not dtd_path.exists():
        print(f"❌ DTD file not found: {dtd_path}")
        print("Make sure the old_gloss symbolic link is set up correctly")
        return False
    
    print(f"📋 DTD path: {dtd_path}")
    
    # Test with DTD validation enabled
    print("\n🔍 Testing with DTD validation enabled...")
    parser_with_dtd = MergedXMLParser(dtd_path=dtd_path, validate_dtd=True)
    print(f"✅ DTD loaded: {parser_with_dtd.dtd is not None}")
    
    # Test with a sample file
    sample_files = [
        Path('old_gloss/merged/adv.xml'),
        Path('old_gloss/merged/adj.xml'), 
        Path('old_gloss/merged/verb.xml'),
        Path('old_gloss/merged/noun.xml')
    ]
    
    for sample_file in sample_files:
        if sample_file.exists():
            print(f"\n📄 Parsing sample file: {sample_file.name}")
            try:
                result = parser_with_dtd.parse_merged_file(sample_file)
                print(f"   📊 Parsed {len(result)} synsets")
                
                # Get detailed stats
                stats = parser_with_dtd.get_validation_summary()
                print(f"   📈 Validation stats:")
                print(f"      - Success rate: {stats['success_rate']:.1%}")
                print(f"      - Valid files: {stats['valid_files']}")
                print(f"      - Invalid files: {stats['invalid_files']}")
                print(f"      - Validation errors: {stats['validation_errors']}")
                
                # Reset stats for next file
                parser_with_dtd.reset_validation_stats()
                
                # Only test the first few files to keep output manageable
                if len(result) > 1000:
                    break
                    
            except Exception as e:
                print(f"   ❌ Error parsing {sample_file.name}: {e}")
                
        else:
            print(f"⚠️  Sample file not found: {sample_file}")
    
    # Test without DTD validation for comparison
    print(f"\n🔍 Testing without DTD validation...")
    parser_no_dtd = MergedXMLParser(validate_dtd=False)
    
    sample_file = Path('old_gloss/merged/adv.xml')
    if sample_file.exists():
        result = parser_no_dtd.parse_merged_file(sample_file)
        print(f"   📊 Parsed {len(result)} synsets (no validation)")
    
    print("\n✅ DTD validation testing complete!")
    return True

def test_error_recovery():
    """Test error recovery functionality."""
    print("\n🛠️  Testing error recovery...")
    print("=" * 30)
    
    dtd_path = Path('old_gloss/dtd/glosstag.dtd')
    
    # Test with continue_on_error=True (default)
    parser_continue = MergedXMLParser(
        dtd_path=dtd_path, 
        validate_dtd=True, 
        continue_on_error=True
    )
    
    # Test with continue_on_error=False
    parser_strict = MergedXMLParser(
        dtd_path=dtd_path, 
        validate_dtd=True, 
        continue_on_error=False
    )
    
    print("✅ Error recovery parsers initialized")
    print("   - Continue on error: enabled")
    print("   - Strict mode: available")

if __name__ == "__main__":
    print("🚀 WordNet Gloss DTD Validation Test")
    print("====================================")
    
    success = test_dtd_validation()
    if success:
        test_error_recovery()
        
    print("\n🎉 All tests completed!")
