"""
Schema Linker - Reuses FinSQL's EmbeddingSchemaLinker

This module provides a wrapper around FinSQL's schema linking component.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import FinSQL's schema linker
from finsql.modules.embedding_schema_linker import EmbeddingSchemaLinker

__all__ = ['EmbeddingSchemaLinker']
