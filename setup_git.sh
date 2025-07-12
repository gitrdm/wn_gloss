#!/bin/bash
# Git initialization script for wn_gloss project

echo "Setting up git repository..."

# Remove any incomplete git directory
rm -rf .git

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Python 3.11 project with conda and poetry setup

- Added environment.yml for conda virtual environment
- Added pyproject.toml for poetry package management
- Created basic project structure with src/wn_gloss package
- Added tests directory with basic test
- Added comprehensive .gitignore for Python projects
- Added README.md with setup instructions"

echo "Git repository initialized successfully!"
echo "To create the conda environment, run:"
echo "  conda env create -f environment.yml"
echo "  conda activate wn_gloss"
echo "  poetry install"
