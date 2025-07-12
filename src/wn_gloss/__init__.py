"""WN Gloss - A Python project for WordNet glosses."""

__version__ = "0.1.0"

from .database import WordNetGlossDB
from .parser import parse_wordnet_directory, MergedXMLParser, StandoffXMLParser
from .models import Synset, Term, SenseKey, Gloss, Token, Annotation, Collocation

__all__ = [
    "WordNetGlossDB",
    "parse_wordnet_directory",
    "MergedXMLParser", 
    "StandoffXMLParser",
    "Synset",
    "Term",
    "SenseKey",
    "Gloss",
    "Token",
    "Annotation",
    "Collocation"
]
