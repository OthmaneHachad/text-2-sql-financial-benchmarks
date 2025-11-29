"""
Schema Linker - Parallel Cross-Encoder for Schema Retrieval

This module uses a trained Cross-Encoder to retrieve relevant tables and columns
for a given question, reducing the schema from hundreds of items to a small set.
"""

import sqlite3
import torch
from pathlib import Path
from typing import List, Dict, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np


PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "economic_data.db"
MODEL_PATH = PROJECT_ROOT / "finsql" / "schema_linking" / "cross_encoder_model"


class SchemaLinker:
    """
    Parallel Cross-Encoder for schema linking.

    Retrieves top-k tables and columns relevant to a question.
    """

    def __init__(self, model_path: str = None, db_path: str = None):
        self.model_path = model_path or str(MODEL_PATH)
        self.db_path = db_path or str(DB_PATH)

        # Load model and tokenizer
        print(f"Loading schema linker model from {self.model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
        self.model.eval()

        # Cache schema
        self.schema = self._load_schema()
        print(f"Loaded schema: {len(self.schema)} tables")

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

    def score_items(self, question: str, schema_items: List[str]) -> np.ndarray:
        """
        Score relevance of schema items to question using Cross-Encoder.

        Args:
            question: Natural language question
            schema_items: List of schema item descriptions

        Returns:
            Array of scores (probabilities of relevance)
        """
        # Tokenize all pairs in batch
        inputs = self.tokenizer(
            [question] * len(schema_items),
            schema_items,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )

        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Get probabilities for positive class (label=1)
            probs = torch.softmax(outputs.logits, dim=1)[:, 1]

        return probs.numpy()

    def retrieve_tables(self, question: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Retrieve top-k most relevant tables for question.

        Args:
            question: Natural language question
            top_k: Number of tables to retrieve

        Returns:
            List of (table_name, score) tuples, sorted by score descending
        """
        # Prepare schema items for all tables
        table_items = []
        table_names = []

        for table_name, columns in self.schema.items():
            # Format: "Table: table_name | Columns: col1, col2, ..."
            columns_desc = ", ".join(columns[:10])  # First 10 columns
            schema_item = f"Table: {table_name} | Columns: {columns_desc}"
            table_items.append(schema_item)
            table_names.append(table_name)

        # Score all tables in parallel
        scores = self.score_items(question, table_items)

        # Get top-k
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [(table_names[i], float(scores[i])) for i in top_indices]

        return results

    def retrieve_columns(
        self,
        question: str,
        tables: List[str],
        top_k_per_table: int = 3
    ) -> List[Tuple[str, str, float]]:
        """
        Retrieve top-k columns per table.

        Args:
            question: Natural language question
            tables: List of table names to retrieve columns from
            top_k_per_table: Number of columns to retrieve per table

        Returns:
            List of (table_name, column_name, score) tuples
        """
        all_results = []

        for table in tables:
            if table not in self.schema:
                continue

            columns = self.schema[table]

            # Prepare schema items for all columns in this table
            column_items = [f"Column: {table}.{col}" for col in columns]

            # Score all columns
            scores = self.score_items(question, column_items)

            # Get top-k for this table
            top_indices = np.argsort(scores)[::-1][:top_k_per_table]

            for i in top_indices:
                all_results.append((table, columns[i], float(scores[i])))

        # Sort all columns by score
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


def test_schema_linker():
    """Test the schema linker on sample queries"""
    from pathlib import Path
    import json

    # Load test queries
    test_data_path = PROJECT_ROOT / "data" / "test" / "queries.json"
    with open(test_data_path, 'r') as f:
        queries = json.load(f)

    # Initialize linker
    linker = SchemaLinker()

    print("="*80)
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
    test_schema_linker()
