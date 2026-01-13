#!/usr/bin/env python3
"""Test script to verify Python dependencies are installed."""

import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import openai
    print("✓ OpenAI package found")
    print(f"OpenAI version: {openai.__version__}")
except ImportError as e:
    print(f"✗ OpenAI package not found: {e}")

try:
    import moviepy
    print("✓ MoviePy package found")
except ImportError as e:
    print(f"✗ MoviePy package not found: {e}")

try:
    from dotenv import load_dotenv
    print("✓ python-dotenv package found")
except ImportError as e:
    print(f"✗ python-dotenv package not found: {e}")

print("Dependency check complete.")