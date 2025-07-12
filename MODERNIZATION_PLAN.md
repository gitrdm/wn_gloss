# WordNet Gloss Modernization Plan

## Current State Analysis

### Data Overview
- **Dataset**: WordNet Gloss Disambiguation Project (2008)
- **Size**: 117,659 glosses across 1,177 files
- **Format**: Legacy XML (merged + standoff XCES)
- **Structure**: Hierarchical directory organization (00/000/ to 11/117/)

### Current Challenges
1. **Fragmented Storage**: Data split across 1,177+ files
2. **Legacy XML**: Custom DTD with non-standard XCES extensions
3. **Complex Parsing**: Multiple annotation layers in separate files
4. **Character Encoding**: Mixed UTF-16 and UTF-8 encoding
5. **Limited Tooling**: No modern programmatic access

## Modernization Options

### Option 1: Relational Database (RECOMMENDED)
**Technology**: PostgreSQL with SQLAlchemy ORM

**Schema Design**:
```sql
-- Core tables
CREATE TABLE synsets (
    id VARCHAR(20) PRIMARY KEY,
    offset VARCHAR(10),
    pos VARCHAR(10),
    created_at TIMESTAMP
);

CREATE TABLE terms (
    id SERIAL PRIMARY KEY,
    synset_id VARCHAR(20) REFERENCES synsets(id),
    term VARCHAR(200),
    INDEX idx_synset_id (synset_id)
);

CREATE TABLE sense_keys (
    id SERIAL PRIMARY KEY,
    synset_id VARCHAR(20) REFERENCES synsets(id),
    sense_key VARCHAR(100),
    INDEX idx_synset_id (synset_id)
);

CREATE TABLE glosses (
    id SERIAL PRIMARY KEY,
    synset_id VARCHAR(20) REFERENCES synsets(id),
    original_text TEXT,
    tokenized_text TEXT,
    INDEX idx_synset_id (synset_id)
);

CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    gloss_id INTEGER REFERENCES glosses(id),
    token_id VARCHAR(50),
    position_start INTEGER,
    position_end INTEGER,
    text VARCHAR(200),
    lemma VARCHAR(200),
    pos VARCHAR(10),
    tag VARCHAR(20),
    token_type VARCHAR(20),
    INDEX idx_gloss_id (gloss_id),
    INDEX idx_token_id (token_id)
);

CREATE TABLE annotations (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id),
    annotation_type VARCHAR(50),
    sense_key VARCHAR(100),
    disambiguation_tag VARCHAR(20),
    INDEX idx_token_id (token_id)
);

CREATE TABLE collocations (
    id SERIAL PRIMARY KEY,
    gloss_id INTEGER REFERENCES glosses(id),
    collocation_id VARCHAR(50),
    text VARCHAR(500),
    sense_key VARCHAR(100),
    is_discontiguous BOOLEAN,
    INDEX idx_gloss_id (gloss_id)
);

CREATE TABLE collocation_tokens (
    id SERIAL PRIMARY KEY,
    collocation_id INTEGER REFERENCES collocations(id),
    token_id INTEGER REFERENCES tokens(id),
    sequence_order INTEGER,
    INDEX idx_collocation_id (collocation_id)
);
```

**Benefits**:
- ACID compliance and data integrity
- Efficient querying with complex joins
- Scalable indexing
- Standard SQL interface
- Good tooling ecosystem

### Option 2: Document Database
**Technology**: MongoDB or PostgreSQL JSONB

**Document Structure**:
```json
{
  "_id": "n00003553",
  "synset": {
    "id": "n00003553",
    "offset": "00003553",
    "pos": "noun",
    "terms": ["whole", "unit"],
    "sense_keys": ["whole%1:03:00::", "unit%1:03:00::"]
  },
  "gloss": {
    "original": "an assemblage of parts that is regarded as a single entity...",
    "tokenized": "an assemblage of parts that is regarded as a single entity ;...",
    "definition": {
      "id": "n00003553_d",
      "tokens": [
        {
          "id": "n00003553_wf1",
          "text": "an",
          "lemma": "an",
          "pos": "DT",
          "tag": "ignore",
          "start": 0,
          "end": 2
        },
        // ... more tokens
      ]
    },
    "examples": [
      {
        "id": "n00003553_ex1",
        "text": "how big is that part compared to the whole?",
        "tokens": [...]
      }
    ]
  },
  "annotations": {
    "collocations": [
      {
        "id": "n00003553_coll.a",
        "text": "regarded as",
        "sense_key": "regard_as%2:31:00::",
        "tokens": ["n00003553_wf7", "n00003553_wf8"],
        "is_discontiguous": false
      }
    ]
  }
}
```

**Benefits**:
- Flexible schema
- Natural hierarchical representation
- Good for read-heavy workloads
- JSON-native operations

### Option 3: Analytical Data Formats
**Technology**: Apache Parquet + Apache Arrow

**Benefits**:
- Columnar storage for analytics
- Excellent compression ratios
- Fast query performance
- Cross-language support (Python, R, Java, C++)
- Integration with modern data science tools

### Option 4: Graph Database
**Technology**: Neo4j or Amazon Neptune

**Use Case**: If focusing on semantic relationships and network analysis

## Implementation Plan

### Phase 1: Data Extraction and Parsing
1. **XML Parser Development**
   - Handle both merged and standoff formats
   - Support UTF-16 and UTF-8 encoding
   - Parse all annotation layers
   - Extract discontiguous collocations

2. **Data Validation**
   - Verify cross-references between files
   - Check data integrity across formats
   - Validate sense keys and synset IDs

### Phase 2: Schema Design and Database Setup
1. **Database Schema Creation**
   - Design normalized schema
   - Create appropriate indexes
   - Set up foreign key constraints

2. **Migration Scripts**
   - Batch processing for large dataset
   - Error handling and logging
   - Progress tracking

### Phase 3: API Development
1. **Modern Python Package**
   - SQLAlchemy models
   - Pydantic schemas for validation
   - Rich query interface
   - Caching layer

2. **REST API** (Optional)
   - FastAPI or Flask
   - OpenAPI documentation
   - Authentication if needed

### Phase 4: Testing and Optimization
1. **Data Quality Checks**
   - Compare against original XML
   - Validate all relationships
   - Performance benchmarking

2. **Query Optimization**
   - Index tuning
   - Query plan analysis
   - Caching strategies

## Python Package Architecture

```
wn_gloss/
├── src/
│   └── wn_gloss/
│       ├── __init__.py
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── xml_parser.py
│       │   └── standoff_parser.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   └── schemas.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── queries.py
│       │   └── client.py
│       ├── utils/
│       │   ├── __init__.py
│       │   └── helpers.py
│       └── cli/
│           ├── __init__.py
│           └── commands.py
├── tests/
├── scripts/
│   ├── migrate_data.py
│   └── validate_migration.py
└── docs/
```

## Usage Examples

```python
from wn_gloss import WordNetGlossDB

# Initialize database connection
db = WordNetGlossDB("postgresql://user:pass@localhost/wn_gloss")

# Query synsets
synsets = db.get_synsets_by_pos("noun")

# Find glosses with specific terms
glosses = db.find_glosses_containing("entity")

# Get all annotations for a synset
annotations = db.get_synset_annotations("n00003553")

# Search collocations
collocations = db.find_collocations("regard_as")

# Advanced queries
complex_query = db.query().join(
    db.Tokens, db.Annotations
).filter(
    db.Annotations.sense_key.contains("entity")
).all()
```

## Migration Tools

1. **Batch Processing Script**
   ```bash
   python scripts/migrate_data.py --source /path/to/wordnet --target postgresql://...
   ```

2. **Validation Script**
   ```bash
   python scripts/validate_migration.py --compare-with /path/to/original
   ```

3. **Performance Testing**
   ```bash
   python scripts/benchmark.py --queries queries.sql
   ```

## Expected Outcomes

1. **Performance**: 100x faster queries compared to XML parsing
2. **Storage**: 50-70% reduction in storage space
3. **Accessibility**: Simple Python API for researchers
4. **Maintainability**: Modern, well-documented codebase
5. **Extensibility**: Easy to add new annotation types

## Timeline Estimate

- **Phase 1**: 2-3 weeks
- **Phase 2**: 1-2 weeks  
- **Phase 3**: 2-3 weeks
- **Phase 4**: 1-2 weeks

**Total**: 6-10 weeks for full implementation

## Technology Stack

- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic 2.0+
- **CLI**: Click or Typer
- **Testing**: pytest
- **Documentation**: Sphinx
- **Packaging**: Poetry
- **CI/CD**: GitHub Actions
