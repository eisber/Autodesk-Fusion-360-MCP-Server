"""Pytest configuration for Server tests."""

import os
import sys

# Add the Server directory to the path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
