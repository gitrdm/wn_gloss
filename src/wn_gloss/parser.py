"""
XML parser for WordNet Gloss Disambiguation Project data.

This module provides parsers for both merged and standoff XML formats
used in the WordNet Gloss Disambiguation Project.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union, Dict, Tuple, Any
import xml.etree.ElementTree as ET
from xml.parsers import expat

import chardet
try:
    from lxml import etree
except ImportError:
    logger.warning("lxml not installed. Install with: pip install lxml")
    etree = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationError:
    """Container for XML validation errors."""
    file_path: str
    line: Optional[int] = None
    column: Optional[int] = None
    error_type: str = "validation"
    message: str = ""
    severity: str = "error"  # error, warning, info

@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    file_path: str
    validation_time: float = 0.0


@dataclass
class TokenData:
    """Represents a token with its attributes."""
    id: str
    text: str
    lemma: Optional[str] = None
    pos: Optional[str] = None
    tag: Optional[str] = None
    token_type: str = "wf"
    start_pos: int = 0
    end_pos: int = 0
    separator: str = " "
    coll_label: Optional[str] = None


@dataclass
class AnnotationData:
    """Represents sense annotation data."""
    id: str
    lemma: Optional[str] = None
    sense_key: Optional[str] = None
    disambiguation_tag: Optional[str] = None


@dataclass
class CollocationData:
    """Represents a collocation with its components."""
    id: str
    text: str
    lemma: Optional[str] = None
    sense_key: Optional[str] = None
    disambiguation_tag: Optional[str] = None
    is_discontiguous: bool = False
    glob_type: Optional[str] = None
    token_ids: List[str] = field(default_factory=list)


@dataclass
class GlossData:
    """Represents a complete gloss with all its components."""
    synset_id: str
    offset: str
    pos: str
    terms: List[str] = field(default_factory=list)
    sense_keys: List[str] = field(default_factory=list)
    original_text: str = ""
    tokenized_text: str = ""
    tokens: List[TokenData] = field(default_factory=list)
    annotations: List[AnnotationData] = field(default_factory=list)
    collocations: List[CollocationData] = field(default_factory=list)
    definitions: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)


class XMLParser:
    """Base class for XML parsing utilities."""
    
    def __init__(self, dtd_path: Optional[Union[str, Path]] = None, 
                 validate_dtd: bool = True, 
                 continue_on_error: bool = True):
        """Initialize parser with optional DTD validation."""
        self.namespaces = {
            'xml': 'http://www.w3.org/XML/1998/namespace',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        self.dtd_path = Path(dtd_path) if dtd_path else None
        self.validate_dtd = validate_dtd
        self.continue_on_error = continue_on_error
        self.dtd = None
        self.validation_stats = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'parsing_errors': 0,
            'validation_errors': 0
        }
        
        # Load DTD if provided
        if self.dtd_path and self.validate_dtd:
            self._load_dtd()
    
    def _load_dtd(self) -> bool:
        """Load DTD for validation."""
        try:
            if not self.dtd_path.exists():
                logger.warning(f"DTD file not found: {self.dtd_path}")
                return False
            
            with open(self.dtd_path, 'r', encoding='utf-8') as f:
                dtd_content = f.read()
            
            self.dtd = etree.DTD(self.dtd_path)
            logger.info(f"Successfully loaded DTD from {self.dtd_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load DTD from {self.dtd_path}: {e}")
            return False
    
    def validate_xml_against_dtd(self, xml_content: str, file_path: str) -> ValidationResult:
        """Validate XML content against DTD."""
        import time
        start_time = time.time()
        
        errors = []
        warnings = []
        is_valid = True
        
        try:
            # Create a custom DTD resolver to handle relative DTD paths
            if self.dtd_path:
                # Replace relative DTD reference with absolute path
                dtd_dir = self.dtd_path.parent
                xml_content = xml_content.replace(
                    'SYSTEM "glosstag.dtd"', 
                    f'SYSTEM "{self.dtd_path}"'
                )
            
            # Parse XML for validation with better error handling
            parser = etree.XMLParser(
                dtd_validation=False,  # We'll validate manually with our DTD
                recover=True,
                resolve_entities=False,  # Prevent external entity loading
                no_network=True         # Disable network access
            )
            doc = etree.fromstring(xml_content.encode('utf-8'), parser)
            
            # Validate against DTD if loaded
            if self.dtd:
                if not self.dtd.validate(doc):
                    is_valid = False
                    # Extract DTD validation errors
                    for error in self.dtd.error_log:
                        # Filter out the common DTD path warnings since we handle them
                        if "failed to load external entity" in error.message and "glosstag.dtd" in error.message:
                            continue
                        if "no DTD found" in error.message:
                            continue
                            
                        severity = "error" if error.level >= 3 else "warning"
                        validation_error = ValidationError(
                            file_path=file_path,
                            line=error.line,
                            column=error.column,
                            error_type="dtd_validation",
                            message=error.message,
                            severity=severity
                        )
                        if severity == "error":
                            errors.append(validation_error)
                        else:
                            warnings.append(validation_error)
            
            # Check parser errors/warnings but filter DTD-related ones
            if parser.error_log:
                for error in parser.error_log:
                    # Filter out expected DTD path warnings
                    if "failed to load external entity" in error.message and "glosstag.dtd" in error.message:
                        continue
                    if "no DTD found" in error.message:
                        continue
                        
                    severity = "error" if error.level >= 3 else "warning"
                    validation_error = ValidationError(
                        file_path=file_path,
                        line=error.line,
                        column=error.column,
                        error_type="parsing",
                        message=error.message,
                        severity=severity
                    )
                    if severity == "error":
                        errors.append(validation_error)
                        if error.level >= 3:  # Fatal errors
                            is_valid = False
                    else:
                        warnings.append(validation_error)
                        
        except etree.XMLSyntaxError as e:
            is_valid = False
            errors.append(ValidationError(
                file_path=file_path,
                line=e.lineno,
                column=e.offset,
                error_type="syntax",
                message=str(e),
                severity="error"
            ))
        except Exception as e:
            is_valid = False
            errors.append(ValidationError(
                file_path=file_path,
                error_type="general",
                message=f"Unexpected validation error: {str(e)}",
                severity="error"
            ))
        
        validation_time = time.time() - start_time
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            file_path=file_path,
            validation_time=validation_time
        )
    
    def log_validation_result(self, result: ValidationResult) -> None:
        """Log validation results with appropriate detail."""
        file_name = Path(result.file_path).name
        
        if result.is_valid:
            logger.info(f"✓ {file_name} - Valid (took {result.validation_time:.3f}s)")
            if result.warnings:
                logger.warning(f"  └─ {len(result.warnings)} warnings")
                for warning in result.warnings:
                    self._log_validation_error(warning)
        else:
            logger.error(f"✗ {file_name} - Invalid (took {result.validation_time:.3f}s)")
            logger.error(f"  └─ {len(result.errors)} errors, {len(result.warnings)} warnings")
            
            # Log errors
            for error in result.errors:
                self._log_validation_error(error)
            
            # Log warnings
            for warning in result.warnings:
                self._log_validation_error(warning)
    
    def _log_validation_error(self, error: ValidationError) -> None:
        """Log individual validation error with context."""
        location = ""
        if error.line and error.column:
            location = f" at line {error.line}, column {error.column}"
        elif error.line:
            location = f" at line {error.line}"
        
        message = f"    {error.error_type.upper()}{location}: {error.message}"
        
        if error.severity == "error":
            logger.error(message)
        elif error.severity == "warning":
            logger.warning(message)
        else:
            logger.info(message)

    def detect_encoding(self, file_path: Union[str, Path]) -> str:
        """Detect file encoding, handling both UTF-8 and UTF-16."""
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            
            # Handle specific cases mentioned in documentation
            if encoding.lower().startswith('utf-16'):
                return 'utf-16'
            return encoding
    
    def safe_parse_xml(self, file_path: Union[str, Path]) -> Optional[ET.Element]:
        """Safely parse XML file with proper encoding detection and DTD validation."""
        file_path = Path(file_path)
        self.validation_stats['total_files'] += 1
        
        try:
            encoding = self.detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Perform DTD validation if enabled
            validation_result = None
            if self.validate_dtd:
                validation_result = self.validate_xml_against_dtd(content, str(file_path))
                self.log_validation_result(validation_result)
                
                # Update statistics
                if validation_result.is_valid:
                    self.validation_stats['valid_files'] += 1
                else:
                    self.validation_stats['invalid_files'] += 1
                    self.validation_stats['validation_errors'] += len(validation_result.errors)
                    
                    # Stop processing if not configured to continue on error
                    if not self.continue_on_error:
                        logger.error(f"Stopping processing due to validation errors in {file_path}")
                        return None
                
            # Parse with lxml for better error handling
            parser = etree.XMLParser(encoding=encoding, recover=True)
            root = etree.fromstring(content.encode(encoding), parser)
            
            # Convert to ElementTree for consistency
            return ET.fromstring(etree.tostring(root, encoding='unicode'))
            
        except Exception as e:
            self.validation_stats['parsing_errors'] += 1
            logger.error(f"Error parsing XML file {file_path}: {e}")
            
            if self.continue_on_error:
                logger.info(f"Continuing processing despite error in {file_path}")
                return None
            else:
                raise
    
    def get_validation_summary(self) -> Dict:
        """Get summary of validation statistics."""
        stats = self.validation_stats.copy()
        if stats['total_files'] > 0:
            stats['success_rate'] = stats['valid_files'] / stats['total_files']
        else:
            stats['success_rate'] = 0.0
        return stats
    
    def reset_validation_stats(self) -> None:
        """Reset validation statistics."""
        self.validation_stats = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'parsing_errors': 0,
            'validation_errors': 0
        }


class MergedXMLParser(XMLParser):
    """Parser for merged XML format glosses."""
    
    def parse_merged_file(self, file_path: Union[str, Path]) -> List[GlossData]:
        """Parse a merged XML file and return list of GlossData objects."""
        root = self.safe_parse_xml(file_path)
        if root is None:
            return []
        
        glosses = []
        
        # Find all synset elements
        synsets = root.findall('.//synset')
        
        for synset in synsets:
            gloss_data = self._parse_synset(synset)
            if gloss_data:
                glosses.append(gloss_data)
        
        return glosses
    
    def _parse_synset(self, synset: ET.Element) -> Optional[GlossData]:
        """Parse a single synset element."""
        synset_id = synset.get('id')
        offset = synset.get('ofs')
        pos = synset.get('pos')
        
        if not synset_id or not offset or not pos:
            return None
        
        gloss_data = GlossData(
            synset_id=synset_id,
            offset=offset,
            pos=pos
        )
        
        # Parse terms
        terms_elem = synset.find('terms')
        if terms_elem is not None:
            for term in terms_elem.findall('term'):
                if term.text:
                    gloss_data.terms.append(term.text)
        
        # Parse sense keys
        keys_elem = synset.find('keys')
        if keys_elem is not None:
            for sk in keys_elem.findall('sk'):
                if sk.text:
                    gloss_data.sense_keys.append(sk.text)
        
        # Parse glosses
        for gloss in synset.findall('gloss'):
            desc = gloss.get('desc')
            if desc == 'orig':
                orig_elem = gloss.find('orig')
                if orig_elem is not None and orig_elem.text:
                    gloss_data.original_text = orig_elem.text
            elif desc == 'text':
                text_elem = gloss.find('text')
                if text_elem is not None and text_elem.text:
                    gloss_data.tokenized_text = text_elem.text
            elif desc == 'wsd':
                self._parse_wsd_gloss(gloss, gloss_data)
        
        return gloss_data
    
    def _parse_wsd_gloss(self, wsd_gloss: ET.Element, gloss_data: GlossData):
        """Parse the word sense disambiguated gloss content."""
        # Parse definitions
        for def_elem in wsd_gloss.findall('def'):
            def_id = def_elem.get('id')
            if def_id:
                def_data = {'id': def_id, 'tokens': []}
                tokens = self._parse_tokens(def_elem)
                def_data['tokens'] = tokens
                gloss_data.definitions.append(def_data)
                gloss_data.tokens.extend(tokens)
        
        # Parse examples
        for ex_elem in wsd_gloss.findall('ex'):
            ex_id = ex_elem.get('id')
            if ex_id:
                ex_data = {'id': ex_id, 'tokens': []}
                tokens = self._parse_tokens(ex_elem)
                ex_data['tokens'] = tokens
                gloss_data.examples.append(ex_data)
                gloss_data.tokens.extend(tokens)
        
        # Parse annotations and collocations
        self._extract_annotations_and_collocations(wsd_gloss, gloss_data)
    
    def _parse_tokens(self, element: ET.Element) -> List[TokenData]:
        """Parse tokens from an element (definition or example)."""
        tokens = []
        
        # Find all wf (word form) and cf (collocation form) elements
        for token_elem in element.findall('.//wf') + element.findall('.//cf'):
            token_data = self._parse_token_element(token_elem)
            if token_data:
                tokens.append(token_data)
        
        return tokens
    
    def _parse_token_element(self, token_elem: ET.Element) -> Optional[TokenData]:
        """Parse a single token element."""
        token_id = token_elem.get('id')
        if not token_id:
            return None
        
        token_data = TokenData(
            id=token_id,
            text=token_elem.text or "",
            lemma=token_elem.get('lemma'),
            pos=token_elem.get('pos'),
            tag=token_elem.get('tag'),
            token_type=token_elem.tag,  # wf or cf
            separator=token_elem.get('sep', ' '),
            coll_label=token_elem.get('coll')
        )
        
        return token_data
    
    def _extract_annotations_and_collocations(self, element: ET.Element, gloss_data: GlossData):
        """Extract annotations and collocations from parsed elements."""
        # Find all <id> elements for annotations
        for id_elem in element.findall('.//id'):
            ann_id = id_elem.get('id')
            if ann_id:
                annotation = AnnotationData(
                    id=ann_id,
                    lemma=id_elem.get('lemma'),
                    sense_key=id_elem.get('sk'),
                    disambiguation_tag=id_elem.get('tag')
                )
                gloss_data.annotations.append(annotation)
        
        # Find all <glob> elements for collocations
        for glob_elem in element.findall('.//glob'):
            coll_id = glob_elem.get('id')
            if coll_id:
                collocation = CollocationData(
                    id=coll_id,
                    text="",  # Will be filled from nested elements
                    lemma=glob_elem.get('lemma'),
                    sense_key=None,  # Will be extracted from nested <id>
                    disambiguation_tag=glob_elem.get('tag'),
                    glob_type=glob_elem.get('glob')
                )
                
                # Extract sense key from nested <id> element
                id_elem = glob_elem.find('id')
                if id_elem is not None:
                    collocation.sense_key = id_elem.get('sk')
                    collocation.text = id_elem.get('lemma', '')
                
                gloss_data.collocations.append(collocation)


class StandoffXMLParser(XMLParser):
    """Parser for standoff XML format glosses."""
    
    def parse_standoff_files(self, base_path: Union[str, Path], prefix: str) -> Optional[GlossData]:
        """Parse all standoff files for a given prefix."""
        base_path = Path(base_path)
        
        # Read the main text file
        text_file = base_path / f"{prefix}.txt"
        if not text_file.exists():
            return None
        
        try:
            encoding = self.detect_encoding(text_file)
            with open(text_file, 'r', encoding=encoding) as f:
                text_content = f.read()
        except Exception as e:
            logger.error(f"Error reading text file {text_file}: {e}")
            return None
        
        # Parse each annotation file
        gloss_data = GlossData(
            synset_id="",  # Will be filled from annotations
            offset="",
            pos="",
            original_text=text_content,
            tokenized_text=text_content
        )
        
        # Parse gloss structure
        gloss_file = base_path / f"{prefix}-wngloss.xml"
        if gloss_file.exists():
            self._parse_gloss_structure(gloss_file, gloss_data)
        
        # Parse token annotations
        ann_file = base_path / f"{prefix}-wnann.xml"
        if ann_file.exists():
            self._parse_token_annotations(ann_file, gloss_data)
        
        # Parse word annotations
        word_file = base_path / f"{prefix}-wnword.xml"
        if word_file.exists():
            self._parse_word_annotations(word_file, gloss_data)
        
        # Parse collocation annotations
        coll_file = base_path / f"{prefix}-wncoll.xml"
        if coll_file.exists():
            self._parse_collocation_annotations(coll_file, gloss_data)
        
        # Parse discontiguous collocation annotations
        dc_file = base_path / f"{prefix}-wndc.xml"
        if dc_file.exists():
            self._parse_discontiguous_annotations(dc_file, gloss_data)
        
        return gloss_data
    
    def _parse_gloss_structure(self, file_path: Path, gloss_data: GlossData):
        """Parse gloss structure annotations."""
        root = self.safe_parse_xml(file_path)
        if root is None:
            return
        
        # Find definition and example structures
        for struct in root.findall('.//struct'):
            struct_type = struct.get('type')
            struct_id = struct.get('id')
            start_pos = int(struct.get('from', 0))
            end_pos = int(struct.get('to', 0))
            
            if struct_type == 'def':
                gloss_data.definitions.append({
                    'id': struct_id,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'tokens': []
                })
            elif struct_type == 'ex':
                gloss_data.examples.append({
                    'id': struct_id,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'tokens': []
                })
    
    def _parse_token_annotations(self, file_path: Path, gloss_data: GlossData):
        """Parse token-level annotations."""
        root = self.safe_parse_xml(file_path)
        if root is None:
            return
        
        for struct in root.findall('.//struct'):
            token_id = struct.get('id')
            if not token_id:
                continue
            
            start_pos = int(struct.get('from', 0))
            end_pos = int(struct.get('to', 0))
            token_type = struct.get('type')
            
            # Extract features
            features = {}
            for feat in struct.findall('feat'):
                feat_name = feat.get('name')
                feat_value = feat.get('value')
                if feat_name and feat_value:
                    features[feat_name] = feat_value
            
            token_data = TokenData(
                id=token_id,
                text=features.get('text', ''),
                lemma=features.get('lemma'),
                pos=features.get('pos'),
                tag=features.get('tag'),
                token_type=token_type,
                start_pos=start_pos,
                end_pos=end_pos,
                separator=features.get('sep', ' '),
                coll_label=features.get('coll')
            )
            
            gloss_data.tokens.append(token_data)
    
    def _parse_word_annotations(self, file_path: Path, gloss_data: GlossData):
        """Parse single-word form annotations."""
        root = self.safe_parse_xml(file_path)
        if root is None:
            return
        
        for struct in root.findall('.//struct'):
            ann_id = struct.get('id')
            if not ann_id:
                continue
            
            # Extract features
            features = {}
            for feat in struct.findall('feat'):
                feat_name = feat.get('name')
                feat_value = feat.get('value')
                if feat_name and feat_value:
                    features[feat_name] = feat_value
            
            annotation = AnnotationData(
                id=ann_id,
                sense_key=features.get('wnsk'),
                disambiguation_tag=struct.get('type')
            )
            
            gloss_data.annotations.append(annotation)
    
    def _parse_collocation_annotations(self, file_path: Path, gloss_data: GlossData):
        """Parse collocation annotations."""
        root = self.safe_parse_xml(file_path)
        if root is None:
            return
        
        for struct in root.findall('.//struct'):
            coll_id = struct.get('id')
            if not coll_id:
                continue
            
            # Extract features
            features = {}
            for feat in struct.findall('feat'):
                feat_name = feat.get('name')
                feat_value = feat.get('value')
                if feat_name and feat_value:
                    features[feat_name] = feat_value
            
            collocation = CollocationData(
                id=coll_id,
                text=features.get('text', ''),
                sense_key=features.get('wnsk'),
                disambiguation_tag=struct.get('type'),
                is_discontiguous=False
            )
            
            gloss_data.collocations.append(collocation)
    
    def _parse_discontiguous_annotations(self, file_path: Path, gloss_data: GlossData):
        """Parse discontiguous collocation annotations."""
        root = self.safe_parse_xml(file_path)
        if root is None:
            return
        
        # This is more complex due to the node-edge structure
        # For now, mark existing collocations as potentially discontiguous
        for struct in root.findall('.//struct'):
            struct_type = struct.get('type')
            if struct_type == 'auto':
                coll_id = struct.get('id')
                
                # Find matching collocation and mark as discontiguous
                for coll in gloss_data.collocations:
                    if coll.id == coll_id:
                        coll.is_discontiguous = True
                        break


class IndexParser:
    """Parser for WordNet index files."""
    
    def __init__(self, index_dir: Union[str, Path]):
        self.index_dir = Path(index_dir)
    
    def parse_index_file(self, index_type: str) -> Dict[str, List[str]]:
        """Parse an index file and return mapping dictionary."""
        index_file = self.index_dir / f"index.{index_type}.tab"
        
        if not index_file.exists():
            return {}
        
        index_data = {}
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        key = parts[0]
                        paths = parts[1:]
                        index_data[key] = paths
        
        except Exception as e:
            logger.error(f"Error parsing index file {index_file}: {e}")
        
        return index_data
    
    def get_synset_mapping(self) -> Dict[str, str]:
        """Get synset ID to path mapping."""
        return {k: v[0] if v else "" for k, v in self.parse_index_file("byid").items()}
    
    def get_sense_key_mapping(self) -> Dict[str, str]:
        """Get sense key to path mapping."""
        return {k: v[0] if v else "" for k, v in self.parse_index_file("bysk").items()}
    
    def get_lemma_mapping(self) -> Dict[str, List[str]]:
        """Get lemma to paths mapping."""
        return self.parse_index_file("bylem")


def parse_wordnet_directory(wordnet_dir: Union[str, Path]) -> List[GlossData]:
    """Parse entire WordNet directory structure."""
    wordnet_dir = Path(wordnet_dir)
    
    # Try merged format first
    merged_dir = wordnet_dir / "merged"
    if merged_dir.exists():
        parser = MergedXMLParser()
        all_glosses = []
        
        for pos_file in ["noun.xml", "verb.xml", "adj.xml", "adv.xml"]:
            file_path = merged_dir / pos_file
            if file_path.exists():
                glosses = parser.parse_merged_file(file_path)
                all_glosses.extend(glosses)
        
        return all_glosses
    
    # Fall back to standoff format
    standoff_dir = wordnet_dir / "standoff"
    if standoff_dir.exists():
        parser = StandoffXMLParser()
        index_parser = IndexParser(standoff_dir)
        
        all_glosses = []
        synset_mapping = index_parser.get_synset_mapping()
        
        for synset_id, path in synset_mapping.items():
            file_path = standoff_dir / path
            if file_path.exists():
                prefix = file_path.name
                gloss_data = parser.parse_standoff_files(file_path.parent, prefix)
                if gloss_data:
                    gloss_data.synset_id = synset_id
                    all_glosses.append(gloss_data)
        
        return all_glosses
    
    return []
