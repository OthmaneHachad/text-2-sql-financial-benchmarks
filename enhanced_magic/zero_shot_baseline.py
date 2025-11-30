"""
Zero-Shot Baseline - No techniques, just question → SQL

Pure baseline with:
- Full database schema (no filtering/ranking)
- No guidelines
- No voting
- Single sample, temp 0.3
"""
import sys
from pathlib import Path
from typing import Dict, Any
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.database import format_schema
from together import Together
import os
from dotenv import load_dotenv

load_dotenv()

# Import shared config
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config import TOGETHER_API_KEY

DB_PATH = project_root / "database" / "economic_data.db"


class ZeroShotBaseline:
    """Pure zero-shot baseline - no techniques"""

    def __init__(self, model_name: str, verbose: bool = False):
        """Initialize zero-shot baseline"""
        self.model_name = model_name
        self.verbose = verbose

        if not TOGETHER_API_KEY:
            raise ValueError("TOGETHER_API_KEY not found")

        self.client = Together(api_key=TOGETHER_API_KEY)
        self.full_schema = format_schema(str(DB_PATH))

        if self.verbose:
            print(f"✓ Zero-shot baseline initialized")
            print(f"  Model: {model_name}")
            print(f"  Schema length: {len(self.full_schema)} chars\n")

    def generate(self, question: str) -> Dict[str, Any]:
        """Generate SQL with pure zero-shot prompting"""

        prompt = f"""You are an expert SQL query generator for an economic database.

Database Schema:
{self.full_schema}

Question: {question}

Generate a SQL query that accurately answers the question. Return ONLY the SQL query, no explanations.

SQL Query:"""

        if self.verbose:
            print(f"\nQuestion: {question}")

        # Generate SQL
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3,
            top_p=0.9,
        )

        raw_output = response.choices[0].message.content.strip()
        sql = self._extract_sql(raw_output)

        if self.verbose:
            print(f"Generated SQL: {sql}\n")

        return {
            "sql": sql,
            "raw_output": raw_output,
        }

    def _extract_sql(self, text: str) -> str:
        """Extract SQL query from model output"""
        # Remove markdown code blocks
        text = re.sub(r'```sql\s*', '', text)
        text = re.sub(r'```\s*', '', text)

        # Look for SELECT statement
        match = re.search(r'(SELECT\s+.*?)(;|\Z)', text, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(1).strip()
            return sql

        # If no SELECT found, return cleaned text
        return text.strip()


if __name__ == "__main__":
    # Quick test
    baseline = ZeroShotBaseline(
        model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        verbose=True
    )

    test_question = "How many GEM observations are in the database?"
    result = baseline.generate(test_question)

    print(f"Result: {result['sql']}")
