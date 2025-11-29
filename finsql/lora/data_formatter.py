"""
Format augmented data into TogetherAI JSONL training format
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import format_schema
from shared.config import DB_PATH
from finsql.config import (
    COT_DATA_PATH,
    SYNONYM_DATA_PATH,
    SKELETON_DATA_PATH,
    HARD_DATA_PATH,
    REPO_ROOT
)


class TrainingDataFormatter:
    """Convert augmented JSON data to TogetherAI JSONL format"""

    def __init__(self):
        # Load database schema once
        self.schema = format_schema(DB_PATH)

        # Training data output directory
        self.training_dir = REPO_ROOT / "data" / "finsql" / "training_data"
        self.training_dir.mkdir(parents=True, exist_ok=True)

    # =====================
    # System Prompts for Each Plugin
    # =====================

    SYSTEM_PROMPTS = {
        "cot": "You are an expert SQL generator. Always think step-by-step before generating queries, explaining your reasoning clearly.",

        "synonym": "You are an expert SQL generator. Handle different phrasings and terminology variations of the same question effectively.",

        "skeleton": "You are an expert SQL generator. Focus on recognizing query patterns and structures to generate accurate SQL.",

        "hard": "You are an expert SQL generator specializing in complex queries. Pay careful attention to edge cases, multi-table relationships, and advanced SQL operations."
    }

    # =====================
    # Format CoT Data
    # =====================

    def format_cot(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format CoT-augmented query for training

        Returns JSONL entry with reasoning + SQL in assistant response
        """
        # User prompt with schema and question
        user_content = f"""Database Schema:
{self.schema}

Question: {query['question']}

First explain your reasoning step-by-step, then generate the SQL query."""

        # Assistant response with reasoning + SQL
        assistant_content = f"""{query['reasoning']}

```sql
{query['ground_truth_sql']}
```"""

        return {
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPTS["cot"]},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content}
            ]
        }

    # =====================
    # Format Synonym Data
    # =====================

    def format_synonym(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Format synonym-augmented query for training"""

        user_content = f"""Database Schema:
{self.schema}

Question: {query['question']}"""

        assistant_content = f"""```sql
{query['ground_truth_sql']}
```"""

        return {
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPTS["synonym"]},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content}
            ]
        }

    # =====================
    # Format Skeleton Data
    # =====================

    def format_skeleton(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Format skeleton-augmented query for training (pattern-based, no placeholders)"""

        user_content = f"""Database Schema:
{self.schema}

Question: {query['question']}

Pattern Type: {query['pattern_type']}
Instructions: This query follows a {query['pattern_type']} pattern. Identify the required SQL components and generate accurate SQL."""

        assistant_content = f"""```sql
{query['ground_truth_sql']}
```"""

        return {
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPTS["skeleton"]},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content}
            ]
        }

    # =====================
    # Format Hard Examples Data
    # =====================

    def format_hard(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Format hard example query for training"""

        # Include hints if available
        hints = ""
        if 'hints' in query:
            hints = f"\n\nHint: {query['hints']}"
        elif 'common_errors' in query:
            errors = "\n".join(f"- {err}" for err in query['common_errors'])
            hints = f"\n\nCommon errors to avoid:\n{errors}"

        user_content = f"""Database Schema:
{self.schema}

Question: {query['question']}{hints}"""

        assistant_content = f"""```sql
{query['ground_truth_sql']}
```"""

        return {
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPTS["hard"]},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content}
            ]
        }

    # =====================
    # Convert Files
    # =====================

    def convert_to_jsonl(
        self,
        input_path: Path,
        output_path: Path,
        formatter_func
    ) -> int:
        """
        Convert augmented JSON to JSONL format

        Args:
            input_path: Path to augmented JSON file
            output_path: Path to output JSONL file
            formatter_func: Function to format each query

        Returns:
            Number of examples written
        """
        # Load augmented data
        with open(input_path, 'r') as f:
            data = json.load(f)

        # Convert each query to JSONL format
        with open(output_path, 'w') as f:
            for query in data:
                formatted = formatter_func(query)
                f.write(json.dumps(formatted) + '\n')

        return len(data)

    # =====================
    # Generate All Training Files
    # =====================

    def generate_all_training_files(self) -> Dict[str, int]:
        """
        Generate all 4 JSONL training files

        Returns:
            Dict mapping plugin name to number of examples
        """
        results = {}

        print(f"\n{'='*80}")
        print("GENERATING TOGETHERAI TRAINING DATA")
        print(f"{'='*80}\n")

        # CoT Plugin
        print("1. CoT Specialist Training Data...")
        cot_output = self.training_dir / "cot_training.jsonl"
        count = self.convert_to_jsonl(COT_DATA_PATH, cot_output, self.format_cot)
        results['cot'] = count
        print(f"   ✓ Generated {count} examples → {cot_output}")

        # Synonym Plugin
        print("\n2. Robustness Specialist Training Data...")
        synonym_output = self.training_dir / "synonym_training.jsonl"
        count = self.convert_to_jsonl(SYNONYM_DATA_PATH, synonym_output, self.format_synonym)
        results['synonym'] = count
        print(f"   ✓ Generated {count} examples → {synonym_output}")

        # Skeleton Plugin
        print("\n3. Structure Specialist Training Data...")
        skeleton_output = self.training_dir / "skeleton_training.jsonl"
        count = self.convert_to_jsonl(SKELETON_DATA_PATH, skeleton_output, self.format_skeleton)
        results['skeleton'] = count
        print(f"   ✓ Generated {count} examples → {skeleton_output}")

        # Hard Examples Plugin
        print("\n4. Hard Cases Specialist Training Data...")
        hard_output = self.training_dir / "hard_training.jsonl"
        count = self.convert_to_jsonl(HARD_DATA_PATH, hard_output, self.format_hard)
        results['hard'] = count
        print(f"   ✓ Generated {count} examples → {hard_output}")

        print(f"\n{'='*80}")
        print("TRAINING DATA GENERATION COMPLETE")
        print(f"{'='*80}")
        print(f"\nTotal examples: {sum(results.values())}")
        for plugin, count in results.items():
            print(f"  {plugin:12s}: {count:3d} examples")

        print(f"\nAll files saved to: {self.training_dir}/")
        print("\nReady for TogetherAI fine-tuning!")

        return results


# =====================
# Validation Functions
# =====================

def validate_jsonl(filepath: Path, num_samples: int = 3) -> bool:
    """
    Validate JSONL file format and show samples

    Args:
        filepath: Path to JSONL file
        num_samples: Number of samples to display

    Returns:
        True if valid, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"VALIDATING: {filepath.name}")
    print(f"{'='*80}\n")

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        print(f"Total examples: {len(lines)}")

        # Parse each line
        for i, line in enumerate(lines[:num_samples]):
            print(f"\n--- Example {i+1} ---")
            entry = json.loads(line)

            # Check structure
            assert "messages" in entry, "Missing 'messages' key"
            assert len(entry["messages"]) == 3, "Should have 3 messages (system, user, assistant)"

            # Display
            for msg in entry["messages"]:
                role = msg["role"]
                content = msg["content"][:200]  # First 200 chars
                print(f"\n{role.upper()}:")
                print(content)
                if len(msg["content"]) > 200:
                    print("...")

        print(f"\n✓ Validation passed for {filepath.name}")
        return True

    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        return False


# =====================
# Main Script
# =====================

def main():
    """Generate and validate all training files"""

    # Create formatter
    formatter = TrainingDataFormatter()

    # Generate all files
    results = formatter.generate_all_training_files()

    # Validate each file
    print(f"\n{'='*80}")
    print("VALIDATING GENERATED FILES")
    print(f"{'='*80}")

    training_files = [
        formatter.training_dir / "cot_training.jsonl",
        formatter.training_dir / "synonym_training.jsonl",
        formatter.training_dir / "skeleton_training.jsonl",
        formatter.training_dir / "hard_training.jsonl",
    ]

    all_valid = True
    for filepath in training_files:
        valid = validate_jsonl(filepath, num_samples=2)
        all_valid = all_valid and valid

    if all_valid:
        print(f"\n{'='*80}")
        print("✓ ALL FILES VALIDATED SUCCESSFULLY")
        print(f"{'='*80}")
        print("\nNext step: Upload to TogetherAI for fine-tuning")
    else:
        print(f"\n{'='*80}")
        print("✗ VALIDATION ERRORS - FIX BEFORE UPLOADING")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()
