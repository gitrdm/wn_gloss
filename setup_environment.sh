#!/bin/bash
# Setup script for wn_gloss project
# This script creates the conda environment and installs poetry dependencies

set -e  # Exit on any error

echo "🚀 Setting up wn_gloss project environment..."
echo "============================================="

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda is not installed or not in PATH"
    echo "Please install Anaconda or Miniconda first"
    exit 1
fi

# Check if environment.yml exists
if [[ ! -f "environment.yml" ]]; then
    echo "❌ Error: environment.yml not found"
    echo "Make sure you're running this script from the project root directory"
    exit 1
fi

# Check if pyproject.toml exists
if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ Error: pyproject.toml not found"
    echo "Make sure you're running this script from the project root directory"
    exit 1
fi

echo "📋 Checking existing conda environment..."

# Check if environment already exists
if conda env list | grep -q "^wn_gloss "; then
    echo "⚠️  Conda environment 'wn_gloss' already exists"
    read -p "Do you want to remove it and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing environment..."
        conda env remove -n wn_gloss -y
    else
        echo "ℹ️  Using existing environment..."
    fi
fi

# Create conda environment if it doesn't exist
if ! conda env list | grep -q "^wn_gloss "; then
    echo "🐍 Creating conda environment from environment.yml..."
    conda env create -f environment.yml
    echo "✅ Conda environment 'wn_gloss' created successfully"
else
    echo "✅ Using existing conda environment 'wn_gloss'"
fi

echo ""
echo "📦 Installing poetry dependencies..."

# Activate environment and install poetry dependencies
eval "$(conda shell.bash hook)"
conda activate wn_gloss

# Verify poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Error: poetry is not available in the environment"
    echo "Installing poetry via conda..."
    conda install poetry -y
fi

# Install poetry dependencies
echo "📥 Installing project dependencies with poetry..."
poetry install

echo ""
echo "🔧 Setting up development tools..."

# Install pre-commit hooks if available
if poetry show pre-commit &> /dev/null; then
    echo "📋 Setting up pre-commit hooks..."
    poetry run pre-commit install
fi

echo ""
echo "✅ Setup completed successfully!"
echo "================================================"
echo ""
echo "🎉 Your wn_gloss environment is ready!"
echo ""
echo "To activate the environment and start working:"
echo "  conda activate wn_gloss"
echo ""
echo "Available commands:"
echo "  wn-gloss --help              # Show CLI help"
echo "  poetry run pytest            # Run tests"
echo "  poetry run black .           # Format code"
echo "  poetry run flake8 .          # Lint code"
echo "  poetry run mypy src/         # Type check"
echo ""
echo "To deactivate the environment when done:"
echo "  conda deactivate"
echo ""

# Test basic functionality
echo "🧪 Testing basic installation..."
if python -c "import wn_gloss; print('wn_gloss package imported successfully')" 2>/dev/null; then
    echo "✅ Package import test passed"
else
    echo "⚠️  Package import test failed - you may need to run 'poetry install' again"
fi

echo ""
echo "🔗 Quick links:"
echo "  Project structure: src/wn_gloss/"
echo "  Tests: tests/"
echo "  Data link: old_gloss/ -> /mnt/p/datasets/wordnet/WordNet-3.0-glosstag/WordNet-3.0/glosstag/"
echo ""
echo "Happy coding! 🚀"
