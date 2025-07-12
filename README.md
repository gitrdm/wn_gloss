# WN Gloss - WordNet Gloss Disambiguation Project Modernization

A modern Python 3.11 project for converting WordNet Gloss Disambiguation Project 3.0 data into JSONL format with DuckDB analytics support. The original data was obtained from https://wordnetcode.princeton.edu/glosstag.shtml in July 2025. The webpage of the original data retains copyright and includes the verbage "When using this freely available resource, we ask that you refer to it as the "Princeton WordNet Gloss Corpus.". I do not know of any licensing issues with converting and using the data. This project is released under an MIT license. 



## Overview

This project modernizes the WordNet Gloss Disambiguation Project data (originally released in 2008) by converting it from legacy XML formats into JSONL (JSON Lines) format optimized for modern NLP research and data science workflows. The original data contains 117,659 WordNet glosses with rich linguistic annotations including:

- Word sense disambiguation
- Part-of-speech tagging  
- Lemmatization
- Multi-word expressions (collocations)
- Discontiguous spans
- Definition and example boundaries

The modernized JSONL format preserves the natural hierarchical structure of synsets while enabling powerful analytics through analytic databases such as DuckDB.

## Features

- **JSONL Document Format**: Natural document-oriented storage preserving synset structure
- **DTD Validation**: Comprehensive XML validation during conversion using original DTD
- **DuckDB Analytics**: Powerful SQL analytics directly on JSONL files without ETL (for demonstration of post conversion use)
- **Dual Format Support**: Handles both merged XML and standoff XML formats
- **Command-Line Interface**: Easy-to-use CLI for data conversion and querying
- **Python API**: Programmatic access to all data and functionality
- **Research-Friendly**: Optimized for NLP research and data science workflows by using the JSONL format
- **Export Capabilities**: CSV export from JSONL data with custom SQL query support

### JSONL Data Format

The converted JSONL format preserves all WordNet data while providing flexible document-oriented storage. Each line contains a complete synset record with the following schema:

#### Complete Schema Example

```json
{
  "synset_id": "n00001740",
  "pos": "n",
  "terms": [
    {"term": "entity", "sense_number": 1}
  ],
  "sense_keys": [
    "entity%1:03:00::"
  ],
  "gloss": {
    "original_text": "that which is perceived or known or inferred to have its own distinct existence (living or nonliving)",
    "tokenized_text": "that which is perceived or known or inferred to have its own distinct existence ( living or nonliving )",
    "tokens": [
      {
        "text": "that",
        "pos": "PRP",
        "lemma": "that",
        "start": 0,
        "end": 0,
        "tag": "ignore",
        "type": "wf"
      },
      {
        "text": "existence",
        "pos": "NN",
        "lemma": "existence%1",
        "start": 0,
        "end": 0,
        "tag": "man",
        "type": "wf"
      }
    ],
    "annotations": [
      {
        "id": "n00001740_id.5",
        "type": "wf",
        "lemma": "existence",
        "sense_key": "existence%1:26:00::",
        "disambiguation_tag": null
      }
    ],
    "collocations": [],
    "definitions": [
      {
        "id": "n00001740_d",
        "tokens": [
          {
            "id": "n00001740_wf14",
            "text": "existence",
            "lemma": "existence%1",
            "pos": "NN",
            "tag": "man",
            "token_type": "wf",
            "start_pos": 0,
            "end_pos": 0,
            "separator": "",
            "coll_label": null
          }
        ]
      }
    ],
    "examples": [
      {
        "id": "n00001740_ex1",
        "tokens": [
          {
            "id": "n00001740_wf20",
            "text": "example text",
            "lemma": "example%1",
            "pos": "NN",
            "tag": "auto",
            "token_type": "wf",
            "start_pos": 0,
            "end_pos": 0,
            "separator": " ",
            "coll_label": null
          }
        ]
      }
    ]
  },
  "metadata": {
    "conversion_timestamp": "2025-07-12T17:30:35.131257Z",
    "dtd_validated": true,
    "offset": "00001740"
  }
}
```

#### Schema Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `synset_id` | string | Unique WordNet synset identifier (e.g., "n00001740") |
| `pos` | string | Part of speech: "n" (noun), "v" (verb), "a" (adjective), "r" (adverb) |
| `terms` | array | List of terms/words in the synset with sense numbers |
| `sense_keys` | array | WordNet sense keys for disambiguation |
| `gloss.original_text` | string | Original definition text from WordNet |
| `gloss.tokenized_text` | string | Tokenized version with normalized spacing |
| `gloss.tokens` | array | Detailed token information with POS tags and lemmas |
| `gloss.annotations` | array | Linguistic annotations for word sense disambiguation |
| `gloss.collocations` | array | Multi-word expressions and collocations |
| `gloss.definitions` | array | Structured definition tokens with detailed metadata |
| `gloss.examples` | array | Example sentences with token-level annotations |
| `metadata.conversion_timestamp` | string | ISO timestamp of conversion |
| `metadata.dtd_validated` | boolean | Whether the source XML passed DTD validation |
| `metadata.offset` | string | Internal offset identifier from source data |

#### Token Structure

Each token in `gloss.tokens`, `definitions[].tokens`, and `examples[].tokens` contains:

- `id`: Unique token identifier
- `text`: The actual text content
- `lemma`: Lemmatized form with sense information
- `pos`: Part-of-speech tag
- `tag`: Annotation tag ("man", "auto", "un", "ignore")
- `token_type`: Type classification ("wf" for word form, "cf" for collocation)
- `start_pos`/`end_pos`: Position information
- `separator`: Whitespace/punctuation following the token
- `coll_label`: Collocation label if part of multi-word expression

#### Annotation Structure

Annotations in `gloss.annotations` provide word sense disambiguation:

- `id`: Unique annotation identifier
- `type`: Annotation type (typically "wf" for word form)
- `lemma`: Base form of the word
- `sense_key`: WordNet sense key for disambiguation
- `disambiguation_tag`: Additional disambiguation information (often null)

## Installation

### Prerequisites

- Python 3.11+
- Conda
- Poetry
- DuckDB (automatically installed), used only for demonstration purposes.

### Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository-url>
   cd wn_gloss
   ```

2. The WordNet gloss data is linked via symbolic link in the project to a shared drive, the link was named old_gloss:
   ```bash
   # The old_gloss directory is a symbolic link to the shared drive
   ls -la old_gloss/  # Should show: merged/, standoff/, dtd/, etc.
   ```

3. Create and activate the conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate wn_gloss
   ```

3. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

## Quick Start

Once you have the setup complete, you can quickly convert the XML data to JSONL:

```bash
# Convert XML to JSONL with DTD validation
wn-gloss convert --input ./old_gloss \
                 --output ./wordnet_glosses.jsonl \
                 --validate-dtd \
                 --dtd ./old_gloss/dtd/glosstag.dtd \
                 --batch-size 1000

# Explore the data with DuckDB
wn-gloss query --jsonl ./wordnet_glosses.jsonl \
               --sql "SELECT pos, COUNT(*) FROM read_json_auto('wordnet_glosses.jsonl') GROUP BY pos"

# Search for specific synsets
wn-gloss search --jsonl ./wordnet_glosses.jsonl \
                --synset-id "n00003553"
```

### WordNet Data Structure

The converter automatically detects and processes the WordNet data structure:

1. **Merged Format** (`old_gloss/merged/`): Primary format with consolidated XML files
   - `noun.xml` - All noun synsets and glosses
   - `verb.xml` - All verb synsets and glosses  
   - `adj.xml` - All adjective synsets and glosses
   - `adv.xml` - All adverb synsets and glosses

2. **Standoff Format** (`old_gloss/standoff/`): Alternative format with separate annotation files
   - Used as fallback if merged format is not available

3. **DTD Validation** (`old_gloss/dtd/glosstag.dtd`): Schema validation for XML structure
   - Ensures data integrity during conversion
   - Validates XML structure against original WordNet specification

## Usage

### Command Line Interface

The project provides a command-line interface for converting XML to JSONL and querying the data:

```bash
# Basic conversion (merged format, auto-detected)
wn-gloss convert --input ./old_gloss \
                 --output ./wordnet_glosses.jsonl

# Conversion with DTD validation (recommended)
wn-gloss convert --input ./old_gloss \
                 --output ./wordnet_glosses.jsonl \
                 --validate-dtd \
                 --dtd ./old_gloss/dtd/glosstag.dtd \
                 --batch-size 1000

# Query the JSONL data using DuckDB
wn-gloss query --jsonl ./wordnet_glosses.jsonl \
               --sql "SELECT pos, COUNT(*) as count FROM read_json_auto('wordnet_glosses.jsonl') GROUP BY pos ORDER BY count DESC"

# Search for specific synsets
wn-gloss search --jsonl ./wordnet_glosses.jsonl \
                --synset-id "n00003553"

# Validate XML files against DTD (without conversion)
wn-gloss validate --input ./old_gloss \
                  --dtd ./old_gloss/dtd/glosstag.dtd \
                  --report-errors
```

### Data Format Detection

The converter automatically detects the available WordNet format:

1. **Merged Format** (preferred): Looks for `old_gloss/merged/` directory
   - Processes: `noun.xml`, `verb.xml`, `adj.xml`, `adv.xml`
   - Each file contains complete synsets with embedded glosses

2. **Standoff Format** (fallback): Uses `old_gloss/standoff/` directory  
   - Processes separate annotation files linked by synset IDs
   - More complex but handles discontiguous annotations

### DTD Validation Options

```bash
# Enable DTD validation with explicit DTD path
--validate-dtd --dtd ./old_gloss/dtd/glosstag.dtd

# DTD validation helps ensure:
# - XML structure conformance
# - Complete data preservation  
# - Early detection of parsing issues
# - Compliance with WordNet specification
```

### JSONL Data Analysis with DuckDB

```bash
# Load JSONL data into DuckDB for analysis
wn-gloss analyze --jsonl ./wordnet_glosses.jsonl \
                 --output analysis_results.json \
                 --include-stats

# Export specific queries to CSV
wn-gloss export --jsonl ./wordnet_glosses.jsonl \
                --sql "SELECT * FROM read_json_auto('wordnet_glosses.jsonl') WHERE pos = 'n' LIMIT 100" \
                --output nouns_sample.csv

# Advanced search examples
wn-gloss search --jsonl ./wordnet_glosses.jsonl \
                --term "entity" --limit 10

wn-gloss search --jsonl ./wordnet_glosses.jsonl \
                --pos "n" --term "computer" --limit 3 \
                --output-format json
```

### Python API

```python
from wn_gloss import WordNetGlossProcessor
import duckdb

# Initialize processor with DTD validation
processor = WordNetGlossProcessor(dtd_path="./old_gloss/dtd/glosstag.dtd")

# Convert XML to JSONL with DTD validation
result = processor.convert_to_jsonl(
    input_dir="./old_gloss",
    output_file="./wordnet_glosses.jsonl",
    validate_dtd=True,
    batch_size=1000
)

# Analyze conversion results
print(f"Converted {result.synsets_processed} synsets")
print(f"Validation errors: {len(result.validation_errors)}")

# Query JSONL data with DuckDB
conn = duckdb.connect(":memory:")
df = conn.execute("""
    SELECT pos, COUNT(*) as count 
    FROM read_json_auto('wordnet_glosses.jsonl') 
    GROUP BY pos 
    ORDER BY count DESC
""").fetchdf()

# Search for specific synsets
synsets = processor.search_jsonl(
    jsonl_file="./wordnet_glosses.jsonl",
    synset_id="n00003553"
)

# Example: Analyze word definitions and related concepts
# Find all definitions of "king" and synsets for words in those definitions
def analyze_word_semantics(word, jsonl_file):
    conn = duckdb.connect(":memory:")
    
    # Step 1: Find all synsets containing the target word
    king_synsets = conn.execute("""
        SELECT synset_id, pos, gloss.original_text as definition
        FROM read_json_auto(?) w
        WHERE list_contains(list_transform(w.terms, x -> x.term), ?)
        ORDER BY synset_id;
    """, [jsonl_file, word]).fetchall()
    
    print(f"=== DEFINITIONS OF '{word.upper()}' ===")
    for synset_id, pos, definition in king_synsets:
        print(f"{synset_id} ({pos}): {definition}")
    
    # Step 2: Find synsets for key words used in definitions
    key_words = ['sovereign', 'ruler', 'kingdom']  # words from king definitions
    
    for key_word in key_words:
        related_synsets = conn.execute("""
            SELECT synset_id, pos, gloss.original_text as definition
            FROM read_json_auto(?) w
            WHERE list_contains(list_transform(w.terms, x -> x.term), ?)
            LIMIT 3;
        """, [jsonl_file, key_word]).fetchall()
        
        print(f"\n=== SYNSETS FOR '{key_word.upper()}' ===")
        for synset_id, pos, definition in related_synsets:
            print(f"{synset_id} ({pos}): {definition}")

# Usage
analyze_word_semantics("king", "./wordnet_glosses.jsonl")

# Load into DuckDB for complex queries
conn.execute("""
    CREATE TABLE wordnet_data AS 
    SELECT * FROM read_json_auto('wordnet_glosses.jsonl')
""")

# Complex analysis
results = conn.execute("""
    SELECT 
        pos,
        AVG(LENGTH(gloss.original_text)) as avg_gloss_length,
        COUNT(*) as synset_count
    FROM wordnet_data 
    GROUP BY pos
""").fetchall()
```

## Data Analysis Examples

### DuckDB Query Examples

```sql
-- Count synsets by part of speech
SELECT pos, COUNT(*) as count 
FROM read_json_auto('wordnet_glosses.jsonl') 
GROUP BY pos ORDER BY count DESC;

-- Find longest glosses
SELECT synset_id, pos, LENGTH(gloss.original_text) as gloss_length,
       gloss.original_text
FROM read_json_auto('wordnet_glosses.jsonl')
ORDER BY gloss_length DESC LIMIT 10;

-- Analyze token distributions
SELECT 
    pos,
    AVG(LENGTH(gloss.original_text)) as avg_gloss_length,
    AVG(ARRAY_LENGTH(gloss.tokens)) as avg_token_count
FROM read_json_auto('wordnet_glosses.jsonl')
GROUP BY pos;

-- Search for specific annotations
SELECT synset_id, gloss.original_text
FROM read_json_auto('wordnet_glosses.jsonl')
WHERE ARRAY_LENGTH(gloss.annotations) > 0
  AND gloss.annotations[1].type = 'wf'
LIMIT 5;

-- Find all definitions of a specific word (e.g., "king")
SELECT synset_id, pos, gloss.original_text as definition
FROM read_json_auto('wordnet_glosses.jsonl') w
WHERE list_contains(list_transform(w.terms, x -> x.term), 'king')
ORDER BY synset_id;

-- Find synsets for words used in definitions (semantic network analysis)
-- Example: Find synsets for "sovereign" (a word used to define "king")
SELECT synset_id, pos, gloss.original_text as definition
FROM read_json_auto('wordnet_glosses.jsonl') w
WHERE list_contains(list_transform(w.terms, x -> x.term), 'sovereign')
LIMIT 5;

-- Combined query: Show a word's definition and related concept synsets
WITH target_word AS (
    SELECT synset_id, gloss.original_text as definition
    FROM read_json_auto('wordnet_glosses.jsonl') w
    WHERE list_contains(list_transform(w.terms, x -> x.term), 'king')
      AND synset_id = 'n10231515'  -- specific sense: "male sovereign"
)
SELECT 
    'TARGET' as type,
    t.synset_id,
    t.definition,
    NULL as related_term
FROM target_word t
UNION ALL
SELECT 
    'RELATED' as type,
    w.synset_id,
    w.gloss.original_text,
    list_transform(w.terms, x -> x.term)[1] as related_term
FROM target_word t
CROSS JOIN read_json_auto('wordnet_glosses.jsonl') w
WHERE list_contains(list_transform(w.terms, x -> x.term), 'sovereign')
   OR list_contains(list_transform(w.terms, x -> x.term), 'ruler')
   OR list_contains(list_transform(w.terms, x -> x.term), 'kingdom')
ORDER BY type, synset_id;
## Performance

The JSONL format with DuckDB provides significant performance improvements over XML parsing:

- **Query Speed**: ~100x faster than XML parsing for complex queries
- **Storage**: Document-oriented format optimized for modern analytics
- **Memory Usage**: Efficient querying without loading entire XML files
- **Analytics**: Native support for complex aggregations and joins

## Data Integrity

The package includes comprehensive data validation:

- DTD validation during XML-to-JSONL conversion
- JSONL schema validation
- Missing data identification  
- Cross-format consistency validation

## Development

### Running Tests
```bash
poetry run pytest
```

### Code Formatting
```bash
poetry run black .
poetry run isort .
```

### Type Checking
```bash
poetry run mypy src/
```

### Linting
```bash
poetry run flake8 src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.

The authors make no representations or warranties regarding the accuracy, completeness, or suitability of the converted WordNet data for any particular purpose. Users are solely responsible for verifying the data quality and suitability for their specific use cases. This project is provided for research and educational purposes, and users should exercise appropriate caution when using it in production environments or critical applications.

## Acknowledgments

This project builds upon the WordNet Gloss Disambiguation Project by Princeton University (2008). The original data and methodology are described in the included `wn_gloss_disambiguation.txt` file.

## Data Distribution

### Sharing Large JSONL Files

The converted WordNet JSONL files can be quite large (100MB+) and exceed GitHub's file size limits. Here are recommended approaches for sharing these files with the research community:

#### **Academic Repositories** (Recommended)
- **Zenodo** (zenodo.org): Free DOI assignment, 50GB limit, permanent archival
- **Figshare**: Academic-focused, good discoverability
- **Harvard Dataverse**: Research data repository with good metadata support

#### **Implementation Example**
```bash
# 1. Upload your JSONL file to Zenodo
# 2. Get the DOI and download URL
# 3. Update your README with download instructions

# Example download script for users:
wget "https://zenodo.org/record/[RECORD_ID]/files/wordnet_glosses.jsonl" \
     -O wordnet_glosses.jsonl

# Or using curl:
curl -L "https://zenodo.org/record/[RECORD_ID]/files/wordnet_glosses.jsonl" \
     -o wordnet_glosses.jsonl
```

#### **Git LFS Alternative**
If you prefer keeping data with code:
```bash
# Install Git LFS
git lfs install (git-lfs has to be installed first, if not already installed to run this command)

# Track large files
git lfs track "*.jsonl"
git add .gitattributes

# Add and commit as normal
git add wordnet_glosses.jsonl
git commit -m "Add WordNet JSONL data via LFS"
git push
```

#### **Cloud Storage Option**
For simple sharing:
```bash
# Upload to Google Drive/Dropbox and get sharing link
# Add download instructions to README:

# Download the pre-converted JSONL file:
# 1. Visit: [Your sharing link]
# 2. Download wordnet_glosses.jsonl
# 3. Place in project root directory
```

#### **Automated Data Pipeline**
Consider providing a script that downloads and processes the data:
```python
# download_data.py
import requests
import os

def download_wordnet_jsonl():
    """Download WordNet JSONL from external source."""
    url = "https://your-data-host.com/wordnet_glosses.jsonl"
    
    if not os.path.exists("wordnet_glosses.jsonl"):
        print("Downloading WordNet JSONL data...")
        response = requests.get(url, stream=True)
        
        with open("wordnet_glosses.jsonl", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("Download complete!")
    else:
        print("WordNet JSONL already exists.")

if __name__ == "__main__":
    download_wordnet_jsonl()
```

### Data Citation

When sharing via academic repositories, include proper citation information:
```
gitrdm. (2025). WordNet Gloss Disambiguation Project - JSONL Format. 
Zenodo. DOI: 10.5281/zenodo.[ID]

Based on: Princeton University WordNet Gloss Disambiguation Project (2008)
```

## Support

For issues, feature requests, or questions, please open an issue on the project repository.
