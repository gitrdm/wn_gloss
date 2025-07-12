#!/bin/bash
# Quick development setup script
# Use this if you already have the conda environment created

set -e

echo "🔧 Quick development setup for wn_gloss..."

# Check if we're in a conda environment
if [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "⚠️  No conda environment detected"
    echo "Please activate the wn_gloss environment first:"
    echo "  conda activate wn_gloss"
    exit 1
fi

if [[ "$CONDA_DEFAULT_ENV" != "wn_gloss" ]]; then
    echo "⚠️  Wrong conda environment: $CONDA_DEFAULT_ENV"
    echo "Please activate the wn_gloss environment:"
    echo "  conda activate wn_gloss"
    exit 1
fi

echo "✅ Using conda environment: $CONDA_DEFAULT_ENV"

# Install/update poetry dependencies
echo "📦 Installing poetry dependencies..."
poetry install

echo "🧪 Running quick tests..."
poetry run pytest tests/test_basic.py -v

echo "🧪 Testing DTD validation..."
python test_dtd_validation.py

echo "✅ Development environment ready!"
echo ""
echo "Available commands:"
echo "  wn-gloss --help              # Show CLI help"
echo "  poetry run pytest            # Run all tests"
echo "  poetry run black .           # Format code"
echo "  poetry run flake8 .          # Lint code"
echo "  poetry run mypy src/         # Type check"
