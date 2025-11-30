"""
MAGIC + Smart Schema Linking

Combines:
- MAGIC's proven approach (full guidelines, single sample, temp 0.3)
- Smart schema ranking: Top-3 tables in detail, others in summary
"""
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.config import (
    MODEL_NAME,
    API_KEY,
    GUIDELINE_PATH,
    DB_PATH,
    SCHEMA_LINKING_CONFIG,
)
from enhanced_magic.modules.schema_linker import EmbeddingSchemaLinker
from shared.database import format_schema
from together import Together


class SmartMAGIC:
    """
    MAGIC + Smart Schema Linking

    Architecture:
    1. Rank tables by relevance (embedding similarity)
    2. Top-3 tables: Show full details (all columns)
    3. Remaining tables: Show summary only (name + description)
    4. Use full MAGIC guideline
    5. Single-sample generation (temp 0.3)
    """

    def __init__(self, verbose: bool = False):
        """Initialize Smart MAGIC"""
        self.verbose = verbose

        if self.verbose:
            print("Initializing Smart MAGIC...")

        # 1. Schema Linker (for ranking only)
        if self.verbose:
            print("  Loading schema linker...")
        self.schema_linker = EmbeddingSchemaLinker(
            db_path=str(DB_PATH),
            model_name=SCHEMA_LINKING_CONFIG["model_name"],
        )

        # 2. Load full MAGIC guideline
        if self.verbose:
            print("  Loading full MAGIC guideline...")
        self.guideline = Path(GUIDELINE_PATH).read_text()

        # 3. TogetherAI client
        if self.verbose:
            print("  Connecting to TogetherAI...")

        if not API_KEY:
            raise ValueError("TOGETHER_API_KEY not found")

        self.client = Together(api_key=API_KEY)
        self.model_name = MODEL_NAME

        # Get full schema for fallback
        self.full_schema = format_schema(str(DB_PATH))

        if self.verbose:
            print("✓ Smart MAGIC initialized\n")

    def _build_smart_schema(self, question: str, top_k: int = 3) -> tuple[str, list]:
        """
        Build smart schema: top-K in detail, others in summary

        Returns:
            (smart_schema_text, ranked_table_names)
        """
        # Get ranked tables
        linked_result = self.schema_linker.link_schema(
            question=question,
            top_k_tables=7,  # Get all tables ranked
            top_k_columns_per_table=20,  # Get all columns for top tables
        )

        ranked_tables = linked_result['linked_tables']

        # Split into detailed vs summary
        detailed_tables = ranked_tables[:top_k]
        summary_tables = ranked_tables[top_k:]

        schema_parts = []

        # Section 1: Detailed tables (top-K)
        if detailed_tables:
            schema_parts.append("=== PRIMARY TABLES (most relevant) ===\n")
            for table_name in detailed_tables:
                # Get full table info from linked schema
                table_info = self._get_table_info(table_name, linked_result)
                schema_parts.append(table_info)

        # Section 2: Summary tables (remaining)
        if summary_tables:
            schema_parts.append("\n=== OTHER AVAILABLE TABLES ===")
            for table_name in summary_tables:
                # Just name and sample columns
                table_summary = self._get_table_summary(table_name)
                schema_parts.append(f"- {table_summary}")

        smart_schema = "\n".join(schema_parts)
        return smart_schema, ranked_tables

    def _get_table_info(self, table_name: str, linked_result: dict) -> str:
        """Get full table info from linked result"""
        if table_name in linked_result['columns_by_table']:
            columns = linked_result['columns_by_table'][table_name]
            info = f"\nTable: {table_name}\nColumns:\n"
            # columns is list of (column_name, score) tuples
            for col_name, score in columns:
                # Get column type from schema linker
                col_type = self._get_column_type(table_name, col_name)
                info += f"  - {col_name} ({col_type})\n"
            return info
        return f"\nTable: {table_name}\n(No column info)\n"

    def _get_column_type(self, table_name: str, column_name: str) -> str:
        """Get column type from database"""
        import sqlite3
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            conn.close()

            for col in columns:
                if col[1] == column_name:  # col[1] is column name, col[2] is type
                    return col[2]
        except:
            pass
        return "TEXT"

    def _get_table_summary(self, table_name: str) -> str:
        """Get brief table summary"""
        # Map table names to descriptions
        descriptions = {
            'countries': 'Country names and IDs',
            'sectors': 'Government sectors (e.g., General, Central, Local)',
            'indicators': 'Economic indicators with names, units, sources',
            'gfs_observations': 'Government Finance Statistics observations',
            'gem_observations': 'Global Economic Monitor observations',
            'time_periods': 'Time period metadata',
            'sqlite_sequence': 'Internal SQLite metadata (ignore)',
        }

        desc = descriptions.get(table_name, 'Data table')
        return f"{table_name}: {desc}"

    def _build_prompt(self, question: str, smart_schema: str) -> str:
        """Build prompt with smart schema and full guideline"""

        prompt = f"""You are an expert SQL query generator for an economic database.

Database Schema:
{smart_schema}

Question: {question}

IMPORTANT GUIDELINES - Common Mistakes to Avoid:

{self.guideline}

Instructions:
1. Generate a valid SQL query that accurately answers the question
2. Use tables from PRIMARY TABLES first (most relevant)
3. You can also use OTHER AVAILABLE TABLES if needed for JOINs
4. Follow the guidelines above to avoid common mistakes
5. For time-series questions, include year column in SELECT and ORDER BY year
6. Use exact matches for indicator/sector names, not LIKE patterns
7. For "per X" or "by X" questions, use GROUP BY not DISTINCT
8. Return ONLY the SQL query, no explanations

SQL Query:"""

        return prompt

    def generate(self, question: str, top_k_detailed: int = 3) -> Dict[str, Any]:
        """
        Generate SQL query using smart schema linking

        Args:
            question: Natural language question
            top_k_detailed: Number of tables to show in full detail

        Returns:
            Dict with 'sql', 'ranked_tables', 'smart_schema'
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Question: {question}")
            print(f"{'='*60}")

        # Step 1: Build smart schema
        if self.verbose:
            print("\n[1/2] Building smart schema...")

        smart_schema, ranked_tables = self._build_smart_schema(question, top_k_detailed)

        if self.verbose:
            print(f"  Ranked tables: {ranked_tables}")
            print(f"  Detailed (top-{top_k_detailed}): {ranked_tables[:top_k_detailed]}")
            print(f"  Summary: {ranked_tables[top_k_detailed:]}")
            print(f"  Schema length: {len(smart_schema)} chars")

        # Step 2: Generate SQL (single sample, MAGIC style)
        if self.verbose:
            print(f"\n[2/2] Generating SQL (temp=0.3, single sample)...")

        prompt = self._build_prompt(question, smart_schema)

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
            print(f"✓ Generated SQL ({len(sql)} chars)")
            print(f"\n{'='*60}")
            print(f"SQL:\n{sql}")
            print(f"{'='*60}\n")

        return {
            "sql": sql,
            "ranked_tables": ranked_tables,
            "detailed_tables": ranked_tables[:top_k_detailed],
            "summary_tables": ranked_tables[top_k_detailed:],
            "smart_schema": smart_schema,
            "raw_output": raw_output,
        }

    def _extract_sql(self, text: str) -> str:
        """Extract SQL query from model output"""
        import re

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
    smart = SmartMAGIC(verbose=True)

    test_question = "Show government revenue (percent of GDP) for Australia from 2010 to 2020"

    result = smart.generate(test_question, top_k_detailed=3)

    print("\n=== RESULT ===")
    print(f"Question: {test_question}")
    print(f"Final SQL: {result['sql']}")
    print(f"Ranked tables: {result['ranked_tables']}")
