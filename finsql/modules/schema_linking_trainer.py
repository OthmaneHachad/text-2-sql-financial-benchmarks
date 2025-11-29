"""
Schema Linking Training Data Preparation and Training Script

This module prepares training data for the Cross-Encoder model and trains it
to predict relevance scores between questions and schema items (tables/columns).
"""

import json
import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.model_selection import train_test_split

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TRAIN_DATA_PATH = DATA_DIR / "train" / "queries.json"
DB_PATH = PROJECT_ROOT / "database" / "economic_data.db"
SCHEMA_LINKING_DIR = PROJECT_ROOT / "finsql" / "schema_linking"
SCHEMA_LINKING_DIR.mkdir(exist_ok=True)


@dataclass
class SchemaItem:
    """Represents a table or column in the database"""
    item_type: str  # 'table' or 'column'
    table_name: str
    column_name: str = None  # None for tables

    def __str__(self):
        if self.item_type == 'table':
            return f"Table: {self.table_name}"
        else:
            return f"Column: {self.table_name}.{self.column_name}"


class SchemaExtractor:
    """Extract schema information from database"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.schema_cache = None

    def get_all_tables(self) -> List[str]:
        """Get all table names from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables

    def get_columns_for_table(self, table_name: str) -> List[str]:
        """Get all column names for a table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        return columns

    def get_full_schema(self) -> Dict[str, List[str]]:
        """Get complete schema as {table_name: [column_names]}"""
        if self.schema_cache:
            return self.schema_cache

        schema = {}
        tables = self.get_all_tables()
        for table in tables:
            schema[table] = self.get_columns_for_table(table)

        self.schema_cache = schema
        return schema


class SQLParser:
    """Parse SQL to extract referenced tables and columns"""

    @staticmethod
    def extract_tables_from_sql(sql: str) -> Set[str]:
        """Extract table names from SQL query"""
        sql = sql.upper()
        tables = set()

        # Extract from FROM clause
        from_pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        tables.update(re.findall(from_pattern, sql, re.IGNORECASE))

        # Extract from JOIN clauses
        join_pattern = r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        tables.update(re.findall(join_pattern, sql, re.IGNORECASE))

        return {t.lower() for t in tables}

    @staticmethod
    def extract_columns_from_sql(sql: str, schema: Dict[str, List[str]]) -> Set[Tuple[str, str]]:
        """Extract (table_name, column_name) pairs from SQL query"""
        columns = set()

        # Extract explicit table.column references
        qualified_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
        qualified_matches = re.findall(qualified_pattern, sql, re.IGNORECASE)

        for table, column in qualified_matches:
            table = table.lower()
            column = column.lower()
            # Verify it's a real table.column (not alias.column)
            if table in schema and column in [c.lower() for c in schema[table]]:
                columns.add((table, column))

        # Extract unqualified column references and match to tables
        # Get all words that might be columns
        words = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', sql)

        for word in words:
            word_lower = word.lower()
            # Check if this word is a column in any table
            for table, table_columns in schema.items():
                if word_lower in [c.lower() for c in table_columns]:
                    columns.add((table, word_lower))

        return columns


class CrossEncoderDataset(Dataset):
    """Dataset for training Cross-Encoder"""

    def __init__(self, examples: List[Dict], tokenizer, max_length=512):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        example = self.examples[idx]

        # Encode question and schema item together
        encoding = self.tokenizer(
            example['question'],
            example['schema_item'],
            padding='max_length',
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(example['label'], dtype=torch.long)
        }


class SchemaLinkingTrainer:
    """Prepare training data and train Cross-Encoder model"""

    def __init__(self, db_path: str, train_data_path: str):
        self.db_path = db_path
        self.train_data_path = train_data_path
        self.schema_extractor = SchemaExtractor(db_path)
        self.sql_parser = SQLParser()
        self.schema = self.schema_extractor.get_full_schema()

    def prepare_training_data(self) -> List[Dict]:
        """
        Prepare training examples from SQL queries.

        For each query:
        - Positive examples: tables/columns actually used in SQL (label=1)
        - Negative examples: tables/columns NOT used in SQL (label=0)
        """
        with open(self.train_data_path, 'r') as f:
            queries = json.load(f)

        training_examples = []

        for query in queries:
            question = query['question']
            sql = query['ground_truth_sql']

            # Extract ground truth tables and columns
            gt_tables = self.sql_parser.extract_tables_from_sql(sql)
            gt_columns = self.sql_parser.extract_columns_from_sql(sql, self.schema)

            # Filter out tables that don't exist in schema (aliases, etc.)
            gt_tables = {t for t in gt_tables if t in self.schema}

            # Create positive examples for tables
            for table in gt_tables:
                columns_desc = ", ".join(self.schema.get(table, [])[:10])  # First 10 columns
                schema_item = f"Table: {table} | Columns: {columns_desc}"
                training_examples.append({
                    'question': question,
                    'schema_item': schema_item,
                    'label': 1,  # Positive
                    'item_type': 'table',
                    'table_name': table
                })

            # Create negative examples for tables (randomly sample non-used tables)
            all_tables = set(self.schema.keys())
            negative_tables = all_tables - gt_tables

            # Sample up to len(gt_tables) * 2 negative examples
            num_negatives = min(len(gt_tables) * 2, len(negative_tables))
            sampled_negative_tables = list(negative_tables)[:num_negatives]

            for table in sampled_negative_tables:
                columns_desc = ", ".join(self.schema.get(table, [])[:10])
                schema_item = f"Table: {table} | Columns: {columns_desc}"
                training_examples.append({
                    'question': question,
                    'schema_item': schema_item,
                    'label': 0,  # Negative
                    'item_type': 'table',
                    'table_name': table
                })

            # Create positive examples for columns
            for table, column in gt_columns:
                schema_item = f"Column: {table}.{column}"
                training_examples.append({
                    'question': question,
                    'schema_item': schema_item,
                    'label': 1,  # Positive
                    'item_type': 'column',
                    'table_name': table,
                    'column_name': column
                })

            # Create negative examples for columns (from tables that ARE used)
            for table in gt_tables:
                # Skip if table not in schema (might be an alias)
                if table not in self.schema:
                    continue
                all_columns_in_table = set(self.schema[table])
                used_columns_in_table = {col for tbl, col in gt_columns if tbl == table}
                unused_columns = all_columns_in_table - used_columns_in_table

                # Sample negative columns
                num_col_negatives = min(len(used_columns_in_table) * 2, len(unused_columns))
                sampled_negative_columns = list(unused_columns)[:num_col_negatives]

                for column in sampled_negative_columns:
                    schema_item = f"Column: {table}.{column}"
                    training_examples.append({
                        'question': question,
                        'schema_item': schema_item,
                        'label': 0,  # Negative
                        'item_type': 'column',
                        'table_name': table,
                        'column_name': column
                    })

        return training_examples

    def train_model(self, model_name='roberta-base', output_dir=None, epochs=3, batch_size=16):
        """Train the Cross-Encoder model"""

        if output_dir is None:
            output_dir = SCHEMA_LINKING_DIR / "cross_encoder_model"

        print("Preparing training data...")
        training_examples = self.prepare_training_data()
        print(f"Created {len(training_examples)} training examples")

        # Split into train/validation
        train_examples, val_examples = train_test_split(
            training_examples, test_size=0.1, random_state=42
        )

        print(f"Train examples: {len(train_examples)}")
        print(f"Validation examples: {len(val_examples)}")

        # Count positive/negative
        train_pos = sum(1 for ex in train_examples if ex['label'] == 1)
        train_neg = len(train_examples) - train_pos
        print(f"Train: {train_pos} positive, {train_neg} negative")

        # Initialize tokenizer and model
        print(f"\nLoading model: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=2  # Binary classification
        )

        # Create datasets
        train_dataset = CrossEncoderDataset(train_examples, tokenizer)
        val_dataset = CrossEncoderDataset(val_examples, tokenizer)

        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir=str(output_dir / 'logs'),
            logging_steps=50,
            eval_strategy="steps",
            eval_steps=200,
            save_strategy="steps",
            save_steps=200,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
        )

        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
        )

        # Train
        print("\nStarting training...")
        trainer.train()

        # Save final model
        print(f"\nSaving model to {output_dir}")
        trainer.save_model(str(output_dir))
        tokenizer.save_pretrained(str(output_dir))

        print("Training complete!")

        return str(output_dir)


def main():
    """Main training script"""
    print("="*80)
    print("SCHEMA LINKING CROSS-ENCODER TRAINING")
    print("="*80)

    # Initialize trainer
    trainer = SchemaLinkingTrainer(
        db_path=str(DB_PATH),
        train_data_path=str(TRAIN_DATA_PATH)
    )

    # Train model
    model_path = trainer.train_model(
        model_name='roberta-base',  # Using base instead of large for faster training
        epochs=3,
        batch_size=16
    )

    print(f"\n✓ Model saved to: {model_path}")
    print("\nNext steps:")
    print("1. Test the model with schema_linker.py")
    print("2. Integrate with inference pipeline")


if __name__ == "__main__":
    main()
