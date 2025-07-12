"""
Core data models for the WordNet Gloss database.

This module defines SQLAlchemy models for storing WordNet gloss data
in a normalized relational database schema.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import ARRAY

Base = declarative_base()


class Synset(Base):
    """WordNet synset with basic information."""
    
    __tablename__ = "synsets"
    
    id = Column(String(20), primary_key=True)  # e.g., "n00003553"
    offset = Column(String(10), nullable=False)  # e.g., "00003553"
    pos = Column(String(10), nullable=False)  # n, v, a, r
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    terms = relationship("Term", back_populates="synset", cascade="all, delete-orphan")
    sense_keys = relationship("SenseKey", back_populates="synset", cascade="all, delete-orphan")
    glosses = relationship("Gloss", back_populates="synset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Synset(id='{self.id}', pos='{self.pos}')>"


class Term(Base):
    """Terms (words) that belong to a synset."""
    
    __tablename__ = "terms"
    
    id = Column(Integer, primary_key=True)
    synset_id = Column(String(20), ForeignKey("synsets.id"), nullable=False)
    term = Column(String(200), nullable=False)
    
    # Relationships
    synset = relationship("Synset", back_populates="terms")
    
    __table_args__ = (
        Index("idx_synset_id", "synset_id"),
        Index("idx_term", "term"),
    )


class SenseKey(Base):
    """WordNet sense keys for synsets."""
    
    __tablename__ = "sense_keys"
    
    id = Column(Integer, primary_key=True)
    synset_id = Column(String(20), ForeignKey("synsets.id"), nullable=False)
    sense_key = Column(String(100), nullable=False)
    
    # Relationships
    synset = relationship("Synset", back_populates="sense_keys")
    
    __table_args__ = (
        Index("idx_synset_id", "synset_id"),
        Index("idx_sense_key", "sense_key"),
    )


class Gloss(Base):
    """Gloss text and metadata for a synset."""
    
    __tablename__ = "glosses"
    
    id = Column(Integer, primary_key=True)
    synset_id = Column(String(20), ForeignKey("synsets.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    tokenized_text = Column(Text, nullable=False)
    
    # Relationships
    synset = relationship("Synset", back_populates="glosses")
    definitions = relationship("Definition", back_populates="gloss", cascade="all, delete-orphan")
    examples = relationship("Example", back_populates="gloss", cascade="all, delete-orphan")
    tokens = relationship("Token", back_populates="gloss", cascade="all, delete-orphan")
    collocations = relationship("Collocation", back_populates="gloss", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_synset_id", "synset_id"),
    )


class Definition(Base):
    """Definition portion of a gloss."""
    
    __tablename__ = "definitions"
    
    id = Column(Integer, primary_key=True)
    gloss_id = Column(Integer, ForeignKey("glosses.id"), nullable=False)
    definition_id = Column(String(50), nullable=False)  # e.g., "n00003553_d"
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)
    
    # Relationships
    gloss = relationship("Gloss", back_populates="definitions")
    
    __table_args__ = (
        Index("idx_gloss_id", "gloss_id"),
    )


class Example(Base):
    """Example sentence within a gloss."""
    
    __tablename__ = "examples"
    
    id = Column(Integer, primary_key=True)
    gloss_id = Column(Integer, ForeignKey("glosses.id"), nullable=False)
    example_id = Column(String(50), nullable=False)  # e.g., "n00003553_ex1"
    text = Column(Text, nullable=False)
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)
    
    # Relationships
    gloss = relationship("Gloss", back_populates="examples")
    
    __table_args__ = (
        Index("idx_gloss_id", "gloss_id"),
    )


class Token(Base):
    """Individual word tokens within glosses."""
    
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True)
    gloss_id = Column(Integer, ForeignKey("glosses.id"), nullable=False)
    token_id = Column(String(50), nullable=False)  # e.g., "n00003553_wf1"
    text = Column(String(200), nullable=False)
    lemma = Column(String(200))
    pos = Column(String(10))  # Part of speech
    tag = Column(String(20))  # ignore, man, auto, un
    token_type = Column(String(20))  # wf, cf, punc, ignore
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)
    separator = Column(String(10))  # Usually empty or space
    
    # Relationships
    gloss = relationship("Gloss", back_populates="tokens")
    annotations = relationship("Annotation", back_populates="token", cascade="all, delete-orphan")
    collocation_memberships = relationship("CollocationToken", back_populates="token")
    
    __table_args__ = (
        Index("idx_gloss_id", "gloss_id"),
        Index("idx_token_id", "token_id"),
        Index("idx_text", "text"),
    )


class Annotation(Base):
    """Sense annotations for tokens."""
    
    __tablename__ = "annotations"
    
    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    annotation_id = Column(String(50), nullable=False)  # e.g., "n00003553_id.1"
    lemma = Column(String(200))
    sense_key = Column(String(100))
    disambiguation_tag = Column(String(20))
    
    # Relationships
    token = relationship("Token", back_populates="annotations")
    
    __table_args__ = (
        Index("idx_token_id", "token_id"),
        Index("idx_sense_key", "sense_key"),
    )


class Collocation(Base):
    """Multi-word expressions (collocations) within glosses."""
    
    __tablename__ = "collocations"
    
    id = Column(Integer, primary_key=True)
    gloss_id = Column(Integer, ForeignKey("glosses.id"), nullable=False)
    collocation_id = Column(String(50), nullable=False)  # e.g., "n00003553_coll.a"
    text = Column(String(500), nullable=False)
    lemma = Column(String(500))
    sense_key = Column(String(100))
    disambiguation_tag = Column(String(20))
    is_discontiguous = Column(Boolean, default=False)
    glob_type = Column(String(20))  # man, auto
    
    # Relationships
    gloss = relationship("Gloss", back_populates="collocations")
    tokens = relationship("CollocationToken", back_populates="collocation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_gloss_id", "gloss_id"),
        Index("idx_collocation_id", "collocation_id"),
        Index("idx_sense_key", "sense_key"),
    )


class CollocationToken(Base):
    """Many-to-many relationship between collocations and tokens."""
    
    __tablename__ = "collocation_tokens"
    
    id = Column(Integer, primary_key=True)
    collocation_id = Column(Integer, ForeignKey("collocations.id"), nullable=False)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    coll_label = Column(String(10))  # e.g., "a", "b" for different collocations
    
    # Relationships
    collocation = relationship("Collocation", back_populates="tokens")
    token = relationship("Token", back_populates="collocation_memberships")
    
    __table_args__ = (
        Index("idx_collocation_id", "collocation_id"),
        Index("idx_token_id", "token_id"),
    )


class DiscontiguousCollocation(Base):
    """Special handling for discontiguous collocations using node references."""
    
    __tablename__ = "discontiguous_collocations"
    
    id = Column(Integer, primary_key=True)
    collocation_id = Column(Integer, ForeignKey("collocations.id"), nullable=False)
    node_id = Column(String(50), nullable=False)  # e.g., "n00337605_coll.b.1"
    referenced_token_id = Column(String(50), nullable=False)  # e.g., "n00337605_wf18"
    node_type = Column(String(20), default="node")
    
    # Relationships
    collocation = relationship("Collocation")
    
    __table_args__ = (
        Index("idx_collocation_id", "collocation_id"),
        Index("idx_node_id", "node_id"),
    )


# Database utility functions
def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """Drop all tables from the database."""
    Base.metadata.drop_all(engine)


def get_table_names():
    """Get list of all table names."""
    return [table.name for table in Base.metadata.tables.values()]
