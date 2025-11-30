"""
Smart MAGIC + Execution-Guided Retry

Extends Smart MAGIC with iterative refinement:
- Generate SQL
- Execute it
- If error → provide error feedback → retry
- Max 3 attempts

Inspired by FinSQL's execution validation, extended with retry loop.
"""
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.smart_inference import SmartMAGIC
from enhanced_magic.config import DB_PATH
from shared.database import execute_sql


class SmartMAGICWithRetry(SmartMAGIC):
    """
    Smart MAGIC + Execution-Guided Retry

    Extends Smart MAGIC with error-based refinement loop
    """

    def __init__(self, max_retries: int = 2, verbose: bool = False):
        """
        Initialize Smart MAGIC with retry

        Args:
            max_retries: Maximum number of retry attempts (total attempts = 1 + max_retries)
            verbose: Print debug information
        """
        super().__init__(verbose=verbose)
        self.max_retries = max_retries

        if self.verbose:
            print(f"✓ Retry mechanism enabled (max {max_retries} retries)\n")

    def generate_with_retry(
        self,
        question: str,
        top_k_detailed: int = 3
    ) -> Dict[str, Any]:
        """
        Generate SQL with execution-guided retry

        Args:
            question: Natural language question
            top_k_detailed: Number of tables to show in full detail

        Returns:
            Dict with 'sql', 'attempts', 'execution_errors', 'success'
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Question: {question}")
            print(f"{'='*60}")

        # Build smart schema once (same for all attempts)
        smart_schema, ranked_tables = self._build_smart_schema(question, top_k_detailed)

        if self.verbose:
            print(f"\nRanked tables: {ranked_tables}")
            print(f"Detailed: {ranked_tables[:top_k_detailed]}")

        attempts = []
        last_error = None

        for attempt_num in range(1 + self.max_retries):
            if self.verbose:
                print(f"\n--- Attempt {attempt_num + 1}/{1 + self.max_retries} ---")

            # Build prompt (include error feedback if retry)
            if attempt_num == 0:
                # First attempt: standard prompt
                prompt = self._build_prompt(question, smart_schema)
            else:
                # Retry: include previous error
                prompt = self._build_retry_prompt(
                    question,
                    smart_schema,
                    attempts[-1]['sql'],
                    last_error
                )

            # Generate SQL
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.3,  # MAGIC baseline
                top_p=0.9,
            )

            raw_output = response.choices[0].message.content.strip()
            sql = self._extract_sql(raw_output)

            if self.verbose:
                print(f"Generated SQL ({len(sql)} chars)")

            # Execute SQL to validate
            exec_result = execute_sql(sql, str(DB_PATH))
            execution_success = exec_result["success"]
            execution_error = exec_result.get("error")

            attempts.append({
                'attempt_num': attempt_num + 1,
                'sql': sql,
                'raw_output': raw_output,
                'execution_success': execution_success,
                'execution_error': execution_error,
            })

            if execution_success:
                if self.verbose:
                    print(f"✓ SQL executes successfully")
                    print(f"\n{'='*60}")
                    print(f"Final SQL (attempt {attempt_num + 1}):\n{sql}")
                    print(f"{'='*60}\n")

                return {
                    'sql': sql,
                    'ranked_tables': ranked_tables,
                    'detailed_tables': ranked_tables[:top_k_detailed],
                    'summary_tables': ranked_tables[top_k_detailed:],
                    'smart_schema': smart_schema,
                    'attempts': attempts,
                    'num_attempts': attempt_num + 1,
                    'success': True,
                }
            else:
                # Execution failed
                last_error = execution_error
                if self.verbose:
                    print(f"✗ Execution failed: {execution_error}")

                if attempt_num < self.max_retries:
                    if self.verbose:
                        print(f"  → Retrying with error feedback...")

        # All attempts failed
        if self.verbose:
            print(f"\n✗ All {1 + self.max_retries} attempts failed")
            print(f"\n{'='*60}")
            print(f"Final SQL (last attempt):\n{attempts[-1]['sql']}")
            print(f"{'='*60}\n")

        return {
            'sql': attempts[-1]['sql'],  # Return last attempt
            'ranked_tables': ranked_tables,
            'detailed_tables': ranked_tables[:top_k_detailed],
            'summary_tables': ranked_tables[top_k_detailed:],
            'smart_schema': smart_schema,
            'attempts': attempts,
            'num_attempts': len(attempts),
            'success': False,
        }

    def _build_retry_prompt(
        self,
        question: str,
        smart_schema: str,
        previous_sql: str,
        error_message: str
    ) -> str:
        """Build retry prompt with error feedback"""

        prompt = f"""You are an expert SQL query generator for an economic database.

Database Schema:
{smart_schema}

Question: {question}

PREVIOUS ATTEMPT FAILED:
You previously generated this SQL:
{previous_sql}

This query failed with the following error:
{error_message}

IMPORTANT GUIDELINES - Common Mistakes to Avoid:

{self.guideline}

Instructions:
1. Analyze the error message carefully
2. Fix the issue in your SQL query
3. Common fixes:
   - "no such column" → check column names exist in schema
   - "no such table" → use tables from PRIMARY TABLES or OTHER AVAILABLE TABLES
   - "ambiguous column" → add table aliases (e.g., t1.column_name)
4. Use tables from PRIMARY TABLES first (most relevant)
5. You can also use OTHER AVAILABLE TABLES if needed for JOINs
6. Follow the guidelines above to avoid common mistakes
7. Return ONLY the corrected SQL query, no explanations

Corrected SQL Query:"""

        return prompt


if __name__ == "__main__":
    # Quick test
    smart_retry = SmartMAGICWithRetry(max_retries=2, verbose=True)

    # Test with a query that might fail initially
    test_question = "List all countries with tax revenue data for 2020"

    result = smart_retry.generate_with_retry(test_question, top_k_detailed=3)

    print("\n=== RESULT ===")
    print(f"Question: {test_question}")
    print(f"Success: {result['success']}")
    print(f"Attempts: {result['num_attempts']}")
    print(f"Final SQL: {result['sql']}")
