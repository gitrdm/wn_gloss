# Environment Setup Guide

This guide explains how to set up the development environment for the wn_gloss project.

## Prerequisites

- **Anaconda** or **Miniconda** installed
- **Git** (for version control)
- Access to the WordNet data directory: `/mnt/p/datasets/wordnet/WordNet-3.0-glosstag/WordNet-3.0/glosstag/`

## Quick Setup (Recommended)

Run the automated setup script:

```bash
./setup_environment.sh
```

This script will:
1. Create the conda environment from `environment.yml`
2. Install all poetry dependencies
3. Set up development tools
4. Test the installation

## Manual Setup

If you prefer to set up manually:

### 1. Create Conda Environment

```bash
conda env create -f environment.yml
conda activate wn_gloss
```

### 2. Install Poetry Dependencies

```bash
poetry install
```

### 3. Verify Installation

```bash
python -c "import wn_gloss; print('Success!')"
wn-gloss --help
```

## Development Workflow

### Daily Development

After the initial setup, use the quick development script:

```bash
conda activate wn_gloss
./setup_dev.sh
```

### Common Commands

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run flake8 .

# Type checking
poetry run mypy src/

# Run CLI
wn-gloss --help
```

### Data Access

The project uses a symbolic link to access WordNet data:
- `old_gloss/` → `/mnt/p/datasets/wordnet/WordNet-3.0-glosstag/WordNet-3.0/glosstag/`

This should already be set up, but if needed:

```bash
ln -s /mnt/p/datasets/wordnet/WordNet-3.0-glosstag/WordNet-3.0/glosstag/ old_gloss
```

## Project Structure

```
wn_gloss/
├── src/wn_gloss/           # Main package
│   ├── __init__.py
│   ├── models.py           # Database models
│   ├── parser.py           # XML parsers with DTD validation
│   ├── database.py         # Database interface
│   └── cli.py              # Command-line interface
├── tests/                  # Test files
├── old_gloss/              # Symbolic link to WordNet data
├── environment.yml         # Conda environment
├── pyproject.toml          # Poetry dependencies
├── setup_environment.sh    # Full setup script
├── setup_dev.sh           # Quick dev setup
└── README.md              # This file
```

## Key Features

- **DTD Validation**: XML parser with comprehensive error logging
- **Database Support**: PostgreSQL with SQLAlchemy ORM
- **CLI Interface**: Full command-line interface with Click
- **Error Recovery**: Continues processing despite validation errors
- **Logging**: Detailed validation and error reporting

## Troubleshooting

### lxml Installation Issues

If you encounter lxml installation problems:

```bash
conda install lxml -c conda-forge
```

### Permission Issues

Make sure scripts are executable:

```bash
chmod +x setup_environment.sh setup_dev.sh
```

### Environment Issues

To recreate the environment:

```bash
conda env remove -n wn_gloss
./setup_environment.sh
```

## Next Steps

1. Run the setup script: `./setup_environment.sh`
2. Test the CLI: `wn-gloss --help`
3. Explore the data: `ls old_gloss/`
4. Start developing: `poetry run pytest`
