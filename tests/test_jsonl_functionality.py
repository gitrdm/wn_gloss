"""
Test script for JSONL conversion functionality.

This script tests the core JSONL conversion and querying functionality
without requiring the full WordNet dataset.
"""

import json
import tempfile
from pathlib import Path
import sys

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from wn_gloss import WordNetGlossProcessor
    from wn_gloss.parser import GlossData, TokenData
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)


def create_sample_gloss_data():
    """Create sample GlossData for testing."""
    token1 = TokenData(
        id="t1",
        text="sample",
        lemma="sample",
        pos="NN",
        tag="NN",
        start_pos=0,
        end_pos=6
    )
    
    token2 = TokenData(
        id="t2", 
        text="gloss",
        lemma="gloss",
        pos="NN", 
        tag="NN",
        start_pos=7,
        end_pos=12
    )
    
    return GlossData(
        synset_id="n00000001",
        offset="00000001",
        pos="n",
        terms=["sample", "test"],
        sense_keys=["sample%1:03:00::", "test%1:03:00::"],
        original_text="sample gloss text for testing",
        tokenized_text="sample gloss text for testing",
        tokens=[token1, token2]
    )


def test_jsonl_conversion():
    """Test JSONL conversion functionality."""
    print("🧪 Testing JSONL Conversion")
    
    # Create processor
    processor = WordNetGlossProcessor()
    
    # Create sample data
    sample_gloss = create_sample_gloss_data()
    
    # Test conversion to JSONL record
    try:
        jsonl_record = processor.convert_gloss_to_jsonl(sample_gloss, dtd_validated=False)
        
        print("   ✅ JSONL record creation successful")
        print(f"   📝 Synset ID: {jsonl_record.synset_id}")
        print(f"   📝 POS: {jsonl_record.pos}")
        print(f"   📝 Terms: {len(jsonl_record.terms)}")
        print(f"   📝 Tokens: {len(jsonl_record.gloss['tokens'])}")
        
        # Test JSON serialization
        json_str = json.dumps(jsonl_record.to_dict(), ensure_ascii=False)
        print(f"   📝 JSON size: {len(json_str)} chars")
        
        # Test deserialization
        parsed = json.loads(json_str)
        assert parsed['synset_id'] == "n00000001"
        assert parsed['pos'] == "n"
        assert len(parsed['terms']) == 2
        print("   ✅ JSON serialization/deserialization successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ JSONL conversion failed: {e}")
        return False


def test_search_functionality():
    """Test search functionality with temporary JSONL file."""
    print("\n🔍 Testing Search Functionality")
    
    processor = WordNetGlossProcessor()
    
    # Create temporary JSONL file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)
        
        # Write sample data
        sample_records = [
            {
                "synset_id": "n00000001",
                "pos": "n",
                "terms": [{"term": "sample", "sense_number": 1}],
                "sense_keys": ["sample%1:03:00::"],
                "gloss": {"original_text": "a sample for testing"},
                "metadata": {"dtd_validated": False}
            },
            {
                "synset_id": "v00000001", 
                "pos": "v",
                "terms": [{"term": "test", "sense_number": 1}],
                "sense_keys": ["test%2:31:00::"],
                "gloss": {"original_text": "to perform a test"},
                "metadata": {"dtd_validated": False}
            }
        ]
        
        for record in sample_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    try:
        # Test search by synset ID
        results = processor.search_jsonl(temp_path, synset_id="n00000001")
        assert len(results) == 1
        assert results[0]['synset_id'] == "n00000001"
        print("   ✅ Search by synset ID successful")
        
        # Test search by POS
        results = processor.search_jsonl(temp_path, pos="v")
        assert len(results) == 1
        assert results[0]['pos'] == "v"
        print("   ✅ Search by POS successful")
        
        # Test search by term
        results = processor.search_jsonl(temp_path, term="sample")
        assert len(results) == 1
        assert results[0]['terms'][0]['term'] == "sample"
        print("   ✅ Search by term successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Search functionality failed: {e}")
        return False
        
    finally:
        # Clean up
        temp_path.unlink()


def test_schema_validation():
    """Test JSONL schema validation."""
    print("\n✅ Testing Schema Validation")
    
    processor = WordNetGlossProcessor()
    
    # Create temporary JSONL file with both valid and invalid records
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)
        
        # Valid record
        valid_record = {
            "synset_id": "n00000001",
            "pos": "n", 
            "terms": [{"term": "sample", "sense_number": 1}],
            "sense_keys": ["sample%1:03:00::"],
            "gloss": {
                "original_text": "a sample",
                "tokens": [],
                "annotations": []
            },
            "metadata": {"dtd_validated": False}
        }
        
        # Invalid record (missing required field)
        invalid_record = {
            "synset_id": "n00000002",
            "pos": "n",
            # Missing terms, sense_keys, gloss, metadata
        }
        
        f.write(json.dumps(valid_record, ensure_ascii=False) + '\n')
        f.write(json.dumps(invalid_record, ensure_ascii=False) + '\n')
    
    try:
        errors = processor.validate_jsonl_schema(temp_path)
        
        # Should find errors for the invalid record
        assert len(errors) > 0
        print(f"   ✅ Schema validation found {len(errors)} errors as expected")
        
        for error in errors:
            print(f"      - {error}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Schema validation failed: {e}")
        return False
        
    finally:
        # Clean up
        temp_path.unlink()


def main():
    """Run all tests."""
    print("🧪 WordNet Gloss JSONL Processor Tests")
    print("=" * 50)
    
    tests = [
        test_jsonl_conversion,
        test_search_functionality, 
        test_schema_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
