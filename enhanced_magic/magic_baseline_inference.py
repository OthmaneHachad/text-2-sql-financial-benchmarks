"""
MAGIC Baseline Inference

Pure MAGIC implementation:
- Full database schema (all tables)
- 11 generic MAGIC guidelines
- Single-sample generation (no voting)
- No schema linking
"""
import sys
from pathlib import Path
from typing import Dict, Any
from together import Together
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.database import format_schema

# MAGIC's 11 Generic Guidelines (from MAGIC paper)
MAGIC_GUIDELINES = """
SQL Generation Guidelines (from MAGIC framework):

1. Use exact column names from schema (case-sensitive)
2. Verify table exists before writing JOIN clause
3. Always specify table name in column references when using JOINs
4. Use appropriate aggregation functions (COUNT, SUM, AVG) for summary queries
5. Include GROUP BY when using aggregations with non-aggregated columns
6. Use DISTINCT when counting unique values
7. Filter using WHERE before aggregating with HAVING
8. Use ORDER BY with LIMIT for "top N" queries
9. Check for NULL values when aggregating
10. Use proper date/time formats matching database schema
11. Verify foreign key relationships before joining tables
"""


class MAGICBaseline:
    """
    MAGIC Baseline: Original MAGIC framework without enhancements

    - Full schema presentation
    - Generic MAGIC guidelines
    - Single-sample generation
    - Temperature 0.3
    """

    def __init__(self, model_name: str = None, verbose: bool = False):
        """Initialize MAGIC Baseline with specified model"""
        self.verbose = verbose

        # Get API key
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            raise ValueError("TOGETHER_API_KEY environment variable not set")

        # Initialize client with 180 second timeout
        self.client = Together(api_key=api_key, timeout=180.0)
        self.model_name = model_name or "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"

        # Get full database schema
        db_path = project_root / "database" / "economic_data.db"
        self.full_schema = format_schema(str(db_path))

        if self.verbose:
            print(f"✓ MAGIC Baseline initialized")
            print(f"  Model: {self.model_name}")
            print(f"  Schema: {len(self.full_schema)} characters")

    def _build_prompt(self, question: str) -> str:
        """Build prompt with full schema and MAGIC guidelines"""

        prompt = f"""You are an expert SQL query generator for an economic database.

Database Schema:
{self.full_schema}

{MAGIC_GUIDELINES}

Question: {question}

Instructions:
1. Generate a valid SQL query that accurately answers the question
2. Use only tables and columns from the provided schema
3. Follow the SQL generation guidelines above
4. Return ONLY the SQL query, no explanations

SQL Query:"""

        return prompt

    def generate(self, question: str) -> Dict[str, Any]:
        """
        Generate SQL query using MAGIC Baseline

        Args:
            question: Natural language question

        Returns:
            Dict with 'sql', 'prompt_tokens', 'completion_tokens'
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Question: {question}")
            print(f"{'='*60}")

        # Build prompt
        prompt = self._build_prompt(question)

        if self.verbose:
            print(f"\nPrompt length: {len(prompt)} characters")

        # Generate SQL
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.3,
            )

            # Extract SQL from response
            sql = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if "```sql" in sql:
                sql = sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql:
                sql = sql.split("```")[1].split("```")[0].strip()

            # Remove trailing semicolons for consistency
            sql = sql.rstrip(';').strip()

            if self.verbose:
                print(f"\nGenerated SQL: {sql}")

            return {
                "sql": sql,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }

        except Exception as e:
            if self.verbose:
                print(f"\nERROR: {str(e)}")
            raise


if __name__ == "__main__":
    # Test with a sample question
    baseline = MAGICBaseline(verbose=True)

    question = "List all available sectors in the GFS data"
    result = baseline.generate(question)

    print(f"\n{'='*60}")
    print(f"Result: {result['sql']}")
    print(f"Tokens: {result['prompt_tokens']} input, {result['completion_tokens']} output")
    print(f"{'='*60}")
