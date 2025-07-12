# WN Gloss

A Python 3.11 project for WordNet glosses.

## Setup

### Prerequisites

- Python 3.11
- Conda
- Poetry

### Installation

1. Create and activate the conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate wn_gloss
   ```

2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

### Development

#### Running Tests
```bash
poetry run pytest
```

#### Code Formatting
```bash
poetry run black .
poetry run isort .
```

#### Type Checking
```bash
poetry run mypy src/
```

#### Linting
```bash
poetry run flake8 src/
```

## Project Structure

```
wn_gloss/
├── src/
│   └── wn_gloss/
│       └── __init__.py
├── tests/
│   └── __init__.py
├── environment.yml
├── pyproject.toml
├── README.md
└── .gitignore
```

## License

This project is licensed under the MIT License.
