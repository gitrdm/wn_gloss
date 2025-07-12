"""
JSONL processor for WordNet Gloss data.

This module provides functionality for converting XML data to JSONL format
and querying JSONL data with DuckDB analytics.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Iterator
import duckdb
import pandas as pd
from tqdm import tqdm

from .parser import parse_wordnet_directory, GlossData


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of XML to JSONL conversion."""
    synsets_processed: int
    validation_errors: List[str]
    conversion_time: float
    output_file: str
    dtd_validated: bool


@dataclass
class JSONLRecord:
    """JSONL record structure for WordNet synset data."""
    synset_id: str
    pos: str
    terms: List[Dict[str, Any]]
    sense_keys: List[str]
    gloss: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class WordNetGlossProcessor:
    """Main processor for WordNet Gloss JSONL conversion and analysis."""

    def __init__(self, dtd_path: Optional[Union[str, Path]] = None):
        """Initialize processor with optional DTD validation."""
        self.dtd_path = Path(dtd_path) if dtd_path else None
        self.validation_errors = []

    def convert_to_jsonl(
        self,
        input_dir: Union[str, Path],
        output_file: Union[str, Path],
        validate_dtd: bool = True,
        batch_size: int = 1000
    ) -> ConversionResult:
        """Convert XML data to JSONL format with DTD validation."""
        import time
        start_time = time.time()
        
        input_path = Path(input_dir)
        output_path = Path(output_file)
        
        logger.info(f"Converting {input_path} to JSONL format: {output_path}")
        
        # Parse XML data with DTD validation
        gloss_data = parse_wordnet_directory(
            str(input_path),
            dtd_path=str(self.dtd_path) if self.dtd_path else None,
            validate_dtd=validate_dtd
        )
        
        synsets_processed = 0
        validation_errors = []
        
        # Convert to JSONL format
        with open(output_path, 'w', encoding='utf-8') as f:
            for gloss in tqdm(gloss_data, desc="Converting to JSONL"):
                try:
                    jsonl_record = self.convert_gloss_to_jsonl(gloss, validate_dtd)
                    f.write(json.dumps(jsonl_record.to_dict(), ensure_ascii=False) + '\n')
                    synsets_processed += 1
                except Exception as e:
                    error_msg = f"Error converting synset {gloss.synset_id}: {e}"
                    validation_errors.append(error_msg)
                    logger.warning(error_msg)
        
        conversion_time = time.time() - start_time
        
        logger.info(f"Conversion completed: {synsets_processed} synsets in {conversion_time:.2f}s")
        
        return ConversionResult(
            synsets_processed=synsets_processed,
            validation_errors=validation_errors,
            conversion_time=conversion_time,
            output_file=str(output_path),
            dtd_validated=validate_dtd
        )

    def convert_gloss_to_jsonl(self, gloss: GlossData, dtd_validated: bool) -> JSONLRecord:
        """Convert GlossData to JSONL record format."""
        # Convert terms to structured format
        terms = [{"term": term, "sense_number": i+1} for i, term in enumerate(gloss.terms)]
        
        # Convert tokens to structured format
        tokens = []
        for token in gloss.tokens:
            tokens.append({
                "text": token.text,
                "pos": token.pos,
                "lemma": token.lemma,
                "start": token.start_pos,
                "end": token.end_pos,
                "tag": token.tag,
                "type": token.token_type
            })
        
        # Convert annotations to structured format
        annotations = []
        for annotation in gloss.annotations:
            annotations.append({
                "id": annotation.id,
                "type": "wf",  # word form annotation
                "lemma": annotation.lemma,
                "sense_key": annotation.sense_key,
                "disambiguation_tag": annotation.disambiguation_tag
            })
        
        # Convert collocations to structured format
        collocations = []
        for collocation in gloss.collocations:
            collocations.append({
                "id": collocation.id,
                "text": collocation.text,
                "lemma": collocation.lemma,
                "sense_key": collocation.sense_key,
                "is_discontiguous": collocation.is_discontiguous,
                "token_ids": collocation.token_ids
            })
        
        # Create gloss structure
        gloss_data = {
            "original_text": gloss.original_text,
            "tokenized_text": gloss.tokenized_text,
            "tokens": tokens,
            "annotations": annotations,
            "collocations": collocations,
            "definitions": gloss.definitions,
            "examples": gloss.examples
        }
        
        # Create metadata
        metadata = {
            "conversion_timestamp": datetime.utcnow().isoformat() + "Z",
            "dtd_validated": dtd_validated,
            "offset": gloss.offset
        }
        
        return JSONLRecord(
            synset_id=gloss.synset_id,
            pos=gloss.pos,
            terms=terms,
            sense_keys=gloss.sense_keys,
            gloss=gloss_data,
            metadata=metadata
        )

    def load_jsonl(self, jsonl_file: Union[str, Path]) -> pd.DataFrame:
        """Load JSONL data into a pandas DataFrame."""
        jsonl_path = Path(jsonl_file)
        
        if not jsonl_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")
        
        records = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        return pd.DataFrame(records)

    def search_jsonl(
        self,
        jsonl_file: Union[str, Path],
        synset_id: Optional[str] = None,
        pos: Optional[str] = None,
        term: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search JSONL data for specific criteria."""
        results = []
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    
                    # Apply filters
                    if synset_id and record.get('synset_id') != synset_id:
                        continue
                    if pos and record.get('pos') != pos:
                        continue
                    if term:
                        # Check if term appears in any of the synset terms
                        terms_match = any(
                            term.lower() in t.get('term', '').lower() 
                            for t in record.get('terms', [])
                        )
                        if not terms_match:
                            continue
                    
                    results.append(record)
                    
                    if len(results) >= limit:
                        break
        
        return results

    def analyze_with_duckdb(
        self,
        jsonl_file: Union[str, Path],
        sql_query: str
    ) -> pd.DataFrame:
        """Execute SQL query on JSONL data using DuckDB."""
        conn = duckdb.connect(":memory:")
        
        # Use DuckDB's read_json_auto function for JSONL
        query = sql_query.replace('wordnet_glosses.jsonl', f"'{jsonl_file}'")
        
        try:
            result = conn.execute(query).fetchdf()
            return result
        except Exception as e:
            logger.error(f"DuckDB query failed: {e}")
            raise
        finally:
            conn.close()

    def get_statistics(self, jsonl_file: Union[str, Path]) -> Dict[str, Any]:
        """Get comprehensive statistics from JSONL data."""
        conn = duckdb.connect(":memory:")
        
        try:
            # Basic counts
            stats = {}
            
            # Count synsets by POS
            pos_counts = conn.execute(f"""
                SELECT pos, COUNT(*) as count 
                FROM read_json_auto('{jsonl_file}') 
                GROUP BY pos ORDER BY count DESC
            """).fetchall()
            
            stats['synsets_by_pos'] = {pos: count for pos, count in pos_counts}
            stats['total_synsets'] = sum(count for _, count in pos_counts)
            
            # Average gloss lengths
            avg_lengths = conn.execute(f"""
                SELECT 
                    pos,
                    AVG(LENGTH(gloss.original_text)) as avg_gloss_length,
                    AVG(ARRAY_LENGTH(gloss.tokens)) as avg_token_count
                FROM read_json_auto('{jsonl_file}')
                GROUP BY pos
            """).fetchall()
            
            stats['avg_gloss_lengths'] = {
                pos: {"gloss_length": gloss_len, "token_count": token_count}
                for pos, gloss_len, token_count in avg_lengths
            }
            
            # Count annotations
            annotation_count = conn.execute(f"""
                SELECT COUNT(*) 
                FROM read_json_auto('{jsonl_file}'), 
                     UNNEST(gloss.annotations) as annot
            """).fetchone()[0]
            
            stats['total_annotations'] = annotation_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Statistics query failed: {e}")
            raise
        finally:
            conn.close()

    def export_to_csv(
        self,
        jsonl_file: Union[str, Path],
        output_file: Union[str, Path],
        sql_query: Optional[str] = None
    ) -> None:
        """Export JSONL data to CSV format."""
        if sql_query is None:
            sql_query = f"SELECT * FROM read_json_auto('{jsonl_file}')"
        
        df = self.analyze_with_duckdb(jsonl_file, sql_query)
        df.to_csv(output_file, index=False)
        logger.info(f"Exported {len(df)} records to {output_file}")

    def validate_jsonl_schema(self, jsonl_file: Union[str, Path]) -> List[str]:
        """Validate JSONL file schema and return any errors."""
        errors = []
        required_fields = ['synset_id', 'pos', 'terms', 'sense_keys', 'gloss', 'metadata']
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        record = json.loads(line)
                        
                        # Check required fields
                        for field in required_fields:
                            if field not in record:
                                errors.append(f"Line {line_num}: Missing required field '{field}'")
                        
                        # Validate gloss structure
                        if 'gloss' in record:
                            gloss = record['gloss']
                            if not isinstance(gloss.get('tokens', []), list):
                                errors.append(f"Line {line_num}: 'gloss.tokens' must be a list")
                            if not isinstance(gloss.get('annotations', []), list):
                                errors.append(f"Line {line_num}: 'gloss.annotations' must be a list")
                    
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_num}: Invalid JSON - {e}")
        
        return errors
