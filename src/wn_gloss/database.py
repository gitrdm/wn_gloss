"""
Database interface for WordNet Gloss data.

This module provides a high-level interface for interacting with the
WordNet Gloss database, including querying, inserting, and updating data.
"""

from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import logging

from .models import (
    Base, Synset, Term, SenseKey, Gloss, Definition, Example, 
    Token, Annotation, Collocation, CollocationToken, DiscontiguousCollocation
)
from .parser import GlossData, parse_wordnet_directory


logger = logging.getLogger(__name__)


class WordNetGlossDB:
    """Main database interface for WordNet Gloss data."""
    
    def __init__(self, database_url: str):
        """Initialize database connection."""
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        
    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
        
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def migrate_from_wordnet(self, wordnet_dir: Union[str, Path], batch_size: int = 100):
        """Migrate data from WordNet directory to database."""
        logger.info(f"Starting migration from {wordnet_dir}")
        
        # Parse WordNet data
        gloss_data_list = parse_wordnet_directory(wordnet_dir)
        logger.info(f"Parsed {len(gloss_data_list)} glosses")
        
        # Insert data in batches
        with self.get_session() as session:
            for i in range(0, len(gloss_data_list), batch_size):
                batch = gloss_data_list[i:i + batch_size]
                self._insert_batch(session, batch)
                session.commit()
                logger.info(f"Inserted batch {i//batch_size + 1}/{(len(gloss_data_list) + batch_size - 1)//batch_size}")
    
    def _insert_batch(self, session: Session, gloss_data_list: List[GlossData]):
        """Insert a batch of gloss data into the database."""
        for gloss_data in gloss_data_list:
            try:
                self._insert_gloss_data(session, gloss_data)
            except IntegrityError as e:
                logger.warning(f"Integrity error inserting {gloss_data.synset_id}: {e}")
                session.rollback()
                continue
    
    def _insert_gloss_data(self, session: Session, gloss_data: GlossData):
        """Insert a single GlossData object into the database."""
        # Create synset
        synset = Synset(
            id=gloss_data.synset_id,
            offset=gloss_data.offset,
            pos=gloss_data.pos
        )
        session.add(synset)
        
        # Add terms
        for term_text in gloss_data.terms:
            term = Term(synset_id=gloss_data.synset_id, term=term_text)
            session.add(term)
        
        # Add sense keys
        for sk_text in gloss_data.sense_keys:
            sense_key = SenseKey(synset_id=gloss_data.synset_id, sense_key=sk_text)
            session.add(sense_key)
        
        # Create gloss
        gloss = Gloss(
            synset_id=gloss_data.synset_id,
            original_text=gloss_data.original_text,
            tokenized_text=gloss_data.tokenized_text
        )
        session.add(gloss)
        session.flush()  # Get gloss.id
        
        # Add definitions
        for def_data in gloss_data.definitions:
            definition = Definition(
                gloss_id=gloss.id,
                definition_id=def_data['id'],
                start_position=def_data.get('start_pos', 0),
                end_position=def_data.get('end_pos', 0)
            )
            session.add(definition)
        
        # Add examples
        for ex_data in gloss_data.examples:
            example = Example(
                gloss_id=gloss.id,
                example_id=ex_data['id'],
                text=ex_data.get('text', ''),
                start_position=ex_data.get('start_pos', 0),
                end_position=ex_data.get('end_pos', 0)
            )
            session.add(example)
        
        # Add tokens
        token_map = {}
        for token_data in gloss_data.tokens:
            token = Token(
                gloss_id=gloss.id,
                token_id=token_data.id,
                text=token_data.text,
                lemma=token_data.lemma,
                pos=token_data.pos,
                tag=token_data.tag,
                token_type=token_data.token_type,
                start_position=token_data.start_pos,
                end_position=token_data.end_pos,
                separator=token_data.separator
            )
            session.add(token)
            session.flush()  # Get token.id
            token_map[token_data.id] = token.id
        
        # Add annotations
        for ann_data in gloss_data.annotations:
            # Find corresponding token
            matching_tokens = [t for t in gloss_data.tokens if t.id == ann_data.id]
            if matching_tokens:
                token_db_id = token_map.get(matching_tokens[0].id)
                if token_db_id:
                    annotation = Annotation(
                        token_id=token_db_id,
                        annotation_id=ann_data.id,
                        lemma=ann_data.lemma,
                        sense_key=ann_data.sense_key,
                        disambiguation_tag=ann_data.disambiguation_tag
                    )
                    session.add(annotation)
        
        # Add collocations
        for coll_data in gloss_data.collocations:
            collocation = Collocation(
                gloss_id=gloss.id,
                collocation_id=coll_data.id,
                text=coll_data.text,
                lemma=coll_data.lemma,
                sense_key=coll_data.sense_key,
                disambiguation_tag=coll_data.disambiguation_tag,
                is_discontiguous=coll_data.is_discontiguous,
                glob_type=coll_data.glob_type
            )
            session.add(collocation)
            session.flush()  # Get collocation.id
            
            # Add collocation tokens
            for i, token_id in enumerate(coll_data.token_ids):
                token_db_id = token_map.get(token_id)
                if token_db_id:
                    coll_token = CollocationToken(
                        collocation_id=collocation.id,
                        token_id=token_db_id,
                        sequence_order=i
                    )
                    session.add(coll_token)
    
    # Query methods
    def get_synsets_by_pos(self, pos: str) -> List[Synset]:
        """Get all synsets for a given part of speech."""
        with self.get_session() as session:
            return session.query(Synset).filter(Synset.pos == pos).all()
    
    def get_synset_by_id(self, synset_id: str) -> Optional[Synset]:
        """Get a synset by its ID."""
        with self.get_session() as session:
            return session.query(Synset).filter(Synset.id == synset_id).first()
    
    def find_synsets_by_term(self, term: str) -> List[Synset]:
        """Find synsets containing a specific term."""
        with self.get_session() as session:
            return session.query(Synset).join(Term).filter(Term.term == term).all()
    
    def find_glosses_containing(self, text: str) -> List[Gloss]:
        """Find glosses containing specific text."""
        with self.get_session() as session:
            return session.query(Gloss).filter(
                or_(
                    Gloss.original_text.contains(text),
                    Gloss.tokenized_text.contains(text)
                )
            ).all()
    
    def get_synset_annotations(self, synset_id: str) -> List[Annotation]:
        """Get all annotations for a synset."""
        with self.get_session() as session:
            return session.query(Annotation).join(Token).join(Gloss).filter(
                Gloss.synset_id == synset_id
            ).all()
    
    def find_collocations_by_sense_key(self, sense_key: str) -> List[Collocation]:
        """Find collocations with a specific sense key."""
        with self.get_session() as session:
            return session.query(Collocation).filter(
                Collocation.sense_key == sense_key
            ).all()
    
    def get_tokens_by_pos(self, pos: str) -> List[Token]:
        """Get all tokens with a specific part of speech."""
        with self.get_session() as session:
            return session.query(Token).filter(Token.pos == pos).all()
    
    def get_disambiguated_tokens(self) -> List[Token]:
        """Get all tokens that have been disambiguated."""
        with self.get_session() as session:
            return session.query(Token).join(Annotation).filter(
                Annotation.sense_key.isnot(None)
            ).all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_session() as session:
            stats = {
                'total_synsets': session.query(Synset).count(),
                'total_glosses': session.query(Gloss).count(),
                'total_tokens': session.query(Token).count(),
                'total_annotations': session.query(Annotation).count(),
                'total_collocations': session.query(Collocation).count(),
                'synsets_by_pos': {},
                'tokens_by_pos': {},
                'disambiguated_tokens': session.query(Token).join(Annotation).filter(
                    Annotation.sense_key.isnot(None)
                ).count()
            }
            
            # Count by part of speech
            for pos in ['n', 'v', 'a', 'r']:
                stats['synsets_by_pos'][pos] = session.query(Synset).filter(
                    Synset.pos == pos
                ).count()
                
                stats['tokens_by_pos'][pos] = session.query(Token).filter(
                    Token.pos.like(f"{pos.upper()}%")
                ).count()
            
            return stats
    
    def search_complex(self, 
                      synset_id: Optional[str] = None,
                      pos: Optional[str] = None,
                      term: Optional[str] = None,
                      sense_key: Optional[str] = None,
                      text_contains: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Perform complex search across multiple criteria."""
        with self.get_session() as session:
            query = session.query(Synset, Gloss).join(Gloss)
            
            if synset_id:
                query = query.filter(Synset.id == synset_id)
            
            if pos:
                query = query.filter(Synset.pos == pos)
            
            if term:
                query = query.join(Term).filter(Term.term.contains(term))
            
            if sense_key:
                query = query.join(SenseKey).filter(SenseKey.sense_key.contains(sense_key))
            
            if text_contains:
                query = query.filter(
                    or_(
                        Gloss.original_text.contains(text_contains),
                        Gloss.tokenized_text.contains(text_contains)
                    )
                )
            
            results = query.limit(limit).all()
            
            # Format results
            formatted_results = []
            for synset, gloss in results:
                formatted_results.append({
                    'synset_id': synset.id,
                    'pos': synset.pos,
                    'offset': synset.offset,
                    'original_text': gloss.original_text,
                    'tokenized_text': gloss.tokenized_text
                })
            
            return formatted_results
    
    def export_to_json(self, output_file: Union[str, Path], synset_ids: Optional[List[str]] = None):
        """Export data to JSON format."""
        import json
        
        with self.get_session() as session:
            query = session.query(Synset)
            
            if synset_ids:
                query = query.filter(Synset.id.in_(synset_ids))
            
            synsets = query.all()
            
            export_data = []
            for synset in synsets:
                synset_data = {
                    'synset_id': synset.id,
                    'pos': synset.pos,
                    'offset': synset.offset,
                    'terms': [term.term for term in synset.terms],
                    'sense_keys': [sk.sense_key for sk in synset.sense_keys],
                    'glosses': []
                }
                
                for gloss in synset.glosses:
                    gloss_data = {
                        'original_text': gloss.original_text,
                        'tokenized_text': gloss.tokenized_text,
                        'tokens': [],
                        'annotations': [],
                        'collocations': []
                    }
                    
                    for token in gloss.tokens:
                        token_data = {
                            'token_id': token.token_id,
                            'text': token.text,
                            'lemma': token.lemma,
                            'pos': token.pos,
                            'tag': token.tag,
                            'token_type': token.token_type,
                            'start_position': token.start_position,
                            'end_position': token.end_position
                        }
                        gloss_data['tokens'].append(token_data)
                    
                    for annotation in gloss.annotations:
                        ann_data = {
                            'annotation_id': annotation.annotation_id,
                            'lemma': annotation.lemma,
                            'sense_key': annotation.sense_key,
                            'disambiguation_tag': annotation.disambiguation_tag
                        }
                        gloss_data['annotations'].append(ann_data)
                    
                    for collocation in gloss.collocations:
                        coll_data = {
                            'collocation_id': collocation.collocation_id,
                            'text': collocation.text,
                            'lemma': collocation.lemma,
                            'sense_key': collocation.sense_key,
                            'is_discontiguous': collocation.is_discontiguous,
                            'glob_type': collocation.glob_type
                        }
                        gloss_data['collocations'].append(coll_data)
                    
                    synset_data['glosses'].append(gloss_data)
                
                export_data.append(synset_data)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported {len(export_data)} synsets to {output_file}")
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity and return report."""
        with self.get_session() as session:
            report = {
                'total_synsets': session.query(Synset).count(),
                'orphaned_glosses': session.query(Gloss).filter(
                    ~Gloss.synset_id.in_(session.query(Synset.id))
                ).count(),
                'orphaned_tokens': session.query(Token).filter(
                    ~Token.gloss_id.in_(session.query(Gloss.id))
                ).count(),
                'orphaned_annotations': session.query(Annotation).filter(
                    ~Annotation.token_id.in_(session.query(Token.id))
                ).count(),
                'orphaned_collocations': session.query(Collocation).filter(
                    ~Collocation.gloss_id.in_(session.query(Gloss.id))
                ).count(),
                'synsets_without_glosses': session.query(Synset).filter(
                    ~Synset.id.in_(session.query(Gloss.synset_id))
                ).count(),
                'tokens_without_text': session.query(Token).filter(
                    or_(Token.text.is_(None), Token.text == '')
                ).count(),
                'annotations_without_sense_keys': session.query(Annotation).filter(
                    or_(Annotation.sense_key.is_(None), Annotation.sense_key == '')
                ).count()
            }
            
            return report
