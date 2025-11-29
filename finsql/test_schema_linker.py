"""
Test Schema Linker

Run this script to test the trained Cross-Encoder model on sample queries.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from finsql.modules.schema_linker import test_schema_linker


if __name__ == "__main__":
    test_schema_linker()
