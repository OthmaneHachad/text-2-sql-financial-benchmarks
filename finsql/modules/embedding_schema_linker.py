"""
Embedding-based Schema Linker

Uses sentence embeddings and cosine similarity to retrieve relevant tables and columns.
No training required - uses pre-trained SentenceTransformer model.
"""

import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "economic_data.db"


class EmbeddingSchemaLinker:
    """
    Embedding-based schema linker using SentenceTransformers.

    Fast, lightweight alternative to Cross-Encoder that requires no training.
    """

    def __init__(self, db_path: str = None, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedding-based schema linker.

        Args:
            db_path: Path to database file
            model_name: SentenceTransformer model name (default: all-MiniLM-L6-v2)
        """
        self.db_path = db_path or str(DB_PATH)

        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Load and cache schema
        self.schema = self._load_schema()
        print(f"Loaded schema: {len(self.schema)} tables")

        # Pre-compute embeddings for all schema items
        print("Pre-computing schema embeddings...")
        self._precompute_embeddings()
        print("✓ Schema embeddings ready")

    def _load_schema(self) -> Dict[str, List[str]]:
        """Load full database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            schema[table] = columns

        conn.close()
        return schema

    def _precompute_embeddings(self):
        """Pre-compute embeddings for all tables and columns"""
        # Table embeddings
        self.table_names = list(self.schema.keys())
        self.table_descriptions = []

        for table in self.table_names:
            # Create natural language description
            columns_sample = ", ".join(self.schema[table][:10])
            desc = f"Table {table} with columns: {columns_sample}"
            self.table_descriptions.append(desc)

        self.table_embeddings = self.model.encode(
            self.table_descriptions,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        # Column embeddings
        self.column_info = []  # List of (table, column) tuples
        self.column_descriptions = []

        for table, columns in self.schema.items():
            for column in columns:
                self.column_info.append((table, column))
                # Create natural language description
                desc = f"Column {column} in table {table}"
                self.column_descriptions.append(desc)

        self.column_embeddings = self.model.encode(
            self.column_descriptions,
            show_progress_bar=False,
            convert_to_numpy=True
        )

    def retrieve_tables(self, question: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Retrieve top-k most relevant tables for question.

        Args:
            question: Natural language question
            top_k: Number of tables to retrieve

        Returns:
            List of (table_name, similarity_score) tuples
        """
        # Encode question
        question_embedding = self.model.encode(
            [question],
            show_progress_bar=False,
            convert_to_numpy=True
        )

        # Compute similarities
        similarities = cosine_similarity(
            question_embedding,
            self.table_embeddings
        )[0]

        # Get top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = [
            (self.table_names[i], float(similarities[i]))
            for i in top_indices
        ]

        return results

    def retrieve_columns(
        self,
        question: str,
        tables: List[str],
        top_k_per_table: int = 5
    ) -> List[Tuple[str, str, float]]:
        """
        Retrieve top-k columns per table.

        Args:
            question: Natural language question
            tables: List of table names to retrieve columns from
            top_k_per_table: Number of columns to retrieve per table

        Returns:
            List of (table_name, column_name, similarity_score) tuples
        """
        # Encode question
        question_embedding = self.model.encode(
            [question],
            show_progress_bar=False,
            convert_to_numpy=True
        )

        all_results = []

        for table in tables:
            if table not in self.schema:
                continue

            # Find indices for this table's columns
            table_column_indices = [
                i for i, (t, c) in enumerate(self.column_info)
                if t == table
            ]

            if not table_column_indices:
                continue

            # Get embeddings for this table's columns
            table_column_embeddings = self.column_embeddings[table_column_indices]

            # Compute similarities
            similarities = cosine_similarity(
                question_embedding,
                table_column_embeddings
            )[0]

            # Get top-k for this table
            top_indices = np.argsort(similarities)[::-1][:top_k_per_table]

            for idx in top_indices:
                original_idx = table_column_indices[idx]
                _, column = self.column_info[original_idx]
                score = float(similarities[idx])
                all_results.append((table, column, score))

        # Sort all results by score
        all_results.sort(key=lambda x: x[2], reverse=True)

        return all_results

    def link_schema(
        self,
        question: str,
        top_k_tables: int = 5,
        top_k_columns_per_table: int = 5
    ) -> Dict[str, any]:
        """
        Complete schema linking: retrieve tables and columns.

        Args:
            question: Natural language question
            top_k_tables: Number of tables to retrieve
            top_k_columns_per_table: Number of columns per table

        Returns:
            Dictionary with linked schema information
        """
        # Retrieve tables
        table_results = self.retrieve_tables(question, top_k=top_k_tables)
        linked_tables = [table for table, _ in table_results]

        # Retrieve columns
        column_results = self.retrieve_columns(
            question,
            linked_tables,
            top_k_per_table=top_k_columns_per_table
        )

        # Organize columns by table
        columns_by_table = {}
        for table, column, score in column_results:
            if table not in columns_by_table:
                columns_by_table[table] = []
            columns_by_table[table].append((column, score))

        return {
            'question': question,
            'tables': table_results,
            'columns_by_table': columns_by_table,
            'linked_tables': linked_tables
        }

    def format_linked_schema(self, linked_schema: Dict) -> str:
        """
        Format linked schema for use in LLM prompts.

        Args:
            linked_schema: Output from link_schema()

        Returns:
            Formatted schema string
        """
        lines = []

        for table, score in linked_schema['tables']:
            lines.append(f"\nTable: {table} (relevance: {score:.3f})")

            if table in linked_schema['columns_by_table']:
                lines.append("Columns:")
                for column, col_score in linked_schema['columns_by_table'][table]:
                    lines.append(f"  - {column} (relevance: {col_score:.3f})")

        return "\n".join(lines)


def test_embedding_schema_linker():
    """Test the embedding-based schema linker on sample queries"""
    import json

    # Load test queries
    test_data_path = PROJECT_ROOT / "data" / "test" / "queries.json"
    with open(test_data_path, 'r') as f:
        queries = json.load(f)

    # Initialize linker
    print("="*80)
    print("INITIALIZING EMBEDDING-BASED SCHEMA LINKER")
    print("="*80)
    linker = EmbeddingSchemaLinker()

    print("\n" + "="*80)
    print("TESTING SCHEMA LINKER")
    print("="*80)

    # Test on first 5 queries
    for query in queries[:5]:
        print(f"\n{'='*80}")
        print(f"Question: {query['question']}")
        print(f"Ground Truth SQL: {query['ground_truth_sql']}")
        print(f"\n{'Linked Schema:':-^80}")

        # Link schema
        linked = linker.link_schema(
            query['question'],
            top_k_tables=3,
            top_k_columns_per_table=5
        )

        # Print results
        print(linker.format_linked_schema(linked))

        print(f"\n{'Tables Retrieved:':-^80}")
        for table, score in linked['tables']:
            print(f"  {table}: {score:.4f}")


if __name__ == "__main__":
    test_embedding_schema_linker()
