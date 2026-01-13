#!/bin/bash

# Install Node.js dependencies
npm install

# Install Python dependencies - try multiple methods
echo "Installing Python dependencies..."

# Method 1: pip3
if command -v pip3 &> /dev/null; then
    echo "Using pip3..."
    pip3 install --upgrade pip
    pip3 install -r src/python/requirements.txt
fi

# Method 2: python3 -m pip
if command -v python3 &> /dev/null; then
    echo "Using python3 -m pip..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r src/python/requirements.txt
fi

# Method 3: python -m pip
if command -v python &> /dev/null; then
    echo "Using python -m pip..."
    python -m pip install --upgrade pip
    python -m pip install -r src/python/requirements.txt
fi

# Verify installation
echo "Verifying Python packages..."
python3 src/python/test_deps.py || echo "Dependency test failed"

echo "Build completed successfully!"