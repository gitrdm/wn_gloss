"""WN Gloss - A Python project for WordNet glosses."""

__version__ = "1.0.0"

from .jsonl_processor import WordNetGlossProcessor, ConversionResult, JSONLRecord
from .parser import parse_wordnet_directory, MergedXMLParser, StandoffXMLParser, GlossData

__all__ = [
    "WordNetGlossProcessor",
    "ConversionResult", 
    "JSONLRecord",
    "parse_wordnet_directory",
    "MergedXMLParser", 
    "StandoffXMLParser",
    "GlossData"
]
