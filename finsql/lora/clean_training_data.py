"""
Clean and fix FinSQL training data:
1. Remove/fix examples with placeholders
2. Validate SQL execution
3. Fix common SQL errors
4. Report statistics
"""
import sys
import json
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import execute_sql
from shared.config import DB_PATH

# Placeholder patterns to detect
PLACEHOLDER_PATTERNS = [
    r'\[YEAR\]', r'\[METRIC\]', r'\[STRING\]',
    r'\[ID\]', r'\[VALUE\]', r'\[NUMBER\]',
    r'\[TABLE\]', r'\[COLUMN\]', r'\[CODE\]'
]


class TrainingDataCleaner:
    """Clean and validate training data"""

    def __init__(self):
        self.stats = {
            'total': 0,
            'kept': 0,
            'fixed': 0,
            'removed': 0,
            'placeholder_removed': 0,
            'sql_error_fixed': 0,
            'unfixable': 0
        }

    def has_placeholders(self, sql: str) -> bool:
        """Check if SQL contains placeholders"""
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return True
        return False

    def extract_sql_from_assistant(self, assistant_content: str) -> str:
        """Extract SQL from assistant message"""
        # Look for SQL in code blocks
        match = re.search(r'```sql\s+(.*?)\s+```', assistant_content, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Look for SQL without code blocks
        match = re.search(r'(SELECT\s+.*)', assistant_content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

        return assistant_content.strip()

    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL execution

        Returns:
            (is_valid, error_message)
        """
        try:
            result = execute_sql(sql, DB_PATH)
            if result is None:
                return False, "Execution returned None"
            return True, ""
        except Exception as e:
            return False, str(e)

    def fix_common_errors(self, sql: str) -> Tuple[str, bool]:
        """
        Fix common SQL errors

        Returns:
            (fixed_sql, was_fixed)
        """
        original = sql

        # Fix 1: Wrong column name 'observation_value' -> 'value'
        sql = re.sub(r'\bobservation_value\b', 'value', sql, flags=re.IGNORECASE)

        # Fix 2: Non-existent table 'observations' -> 'gfs_observations' or 'gem_observations'
        if re.search(r'\bFROM\s+observations\b', sql, re.IGNORECASE):
            # Try to infer correct table from context
            if 'sector' in sql.lower():
                sql = re.sub(r'\bobservations\b', 'gfs_observations', sql, flags=re.IGNORECASE)
            else:
                sql = re.sub(r'\bobservations\b', 'gem_observations', sql, flags=re.IGNORECASE)

        # Fix 3: Non-existent table 'tax_revenue' -> use gfs_observations with indicator filter
        sql = re.sub(r'\bFROM\s+tax_revenue\b', 'FROM gfs_observations', sql, flags=re.IGNORECASE)

        # Fix 4: Double quotes around strings (should be single quotes)
        sql = re.sub(r'(\w+)\s*=\s*"([^"]+)"', r"\1 = '\2'", sql)

        # Fix 5: Extra semicolon at end (acceptable but inconsistent)
        sql = sql.rstrip(';').strip()

        return sql, (sql != original)

    def process_example(self, example: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Process a single training example

        Returns:
            (cleaned_example or None, status)
            status: 'kept', 'fixed', 'removed'
        """
        self.stats['total'] += 1

        # Extract SQL from assistant message
        assistant_content = example['messages'][-1]['content']
        sql = self.extract_sql_from_assistant(assistant_content)

        # Check for placeholders
        if self.has_placeholders(sql):
            self.stats['placeholder_removed'] += 1
            self.stats['removed'] += 1
            return None, 'removed_placeholder'

        # Validate SQL
        is_valid, error = self.validate_sql(sql)

        if is_valid:
            self.stats['kept'] += 1
            return example, 'kept'

        # Try to fix
        fixed_sql, was_fixed = self.fix_common_errors(sql)

        if was_fixed:
            # Validate fixed SQL
            is_valid_fixed, _ = self.validate_sql(fixed_sql)

            if is_valid_fixed:
                # Update example with fixed SQL
                fixed_content = assistant_content.replace(sql, fixed_sql)
                example['messages'][-1]['content'] = fixed_content

                self.stats['fixed'] += 1
                self.stats['sql_error_fixed'] += 1
                return example, 'fixed'

        # Couldn't fix - remove
        self.stats['unfixable'] += 1
        self.stats['removed'] += 1
        return None, 'unfixable'

    def clean_jsonl_file(self, input_path: Path, output_path: Path):
        """Clean a JSONL training file"""
        print(f"\nCleaning: {input_path.name}")

        cleaned_examples = []

        with open(input_path, 'r') as f:
            for line in f:
                if line.strip():
                    example = json.loads(line)
                    cleaned, status = self.process_example(example)

                    if cleaned is not None:
                        cleaned_examples.append(cleaned)

        # Write cleaned data
        with open(output_path, 'w') as f:
            for example in cleaned_examples:
                f.write(json.dumps(example) + '\n')

        print(f"  Original: {self.stats['total']} examples")
        print(f"  Kept: {self.stats['kept']} examples")
        print(f"  Fixed: {self.stats['fixed']} examples")
        print(f"  Removed: {self.stats['removed']} examples")
        print(f"    - Placeholders: {self.stats['placeholder_removed']}")
        print(f"    - Unfixable: {self.stats['unfixable']}")

        # Reset stats for next file
        self.stats = {k: 0 for k in self.stats}

        return len(cleaned_examples)


def main():
    """Clean all training data files"""
    print("=" * 60)
    print("FINSQL TRAINING DATA CLEANING")
    print("=" * 60)

    cleaner = TrainingDataCleaner()

    training_dir = Path("/Users/othmane/University-Classes/Fall-2025/VIP-NLP/group-text-2-sql/data/finsql/training_data")

    files = [
        "cot_training.jsonl",
        "synonym_training.jsonl",
        "skeleton_training.jsonl",
        "hard_training.jsonl"
    ]

    total_original = 0
    total_cleaned = 0

    for filename in files:
        input_path = training_dir / filename
        output_path = training_dir / f"cleaned_{filename}"

        if input_path.exists():
            count = cleaner.clean_jsonl_file(input_path, output_path)
            total_cleaned += count

            # Count original
            with open(input_path, 'r') as f:
                total_original += sum(1 for line in f if line.strip())

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total original examples: {total_original}")
    print(f"Total cleaned examples: {total_cleaned}")
    print(f"Reduction: {total_original - total_cleaned} examples ({(total_original - total_cleaned) / total_original * 100:.1f}%)")
    print("\nCleaned files saved with 'cleaned_' prefix")
    print("\nNext step: Re-train all 4 plugins with cleaned data")


if __name__ == "__main__":
    main()
