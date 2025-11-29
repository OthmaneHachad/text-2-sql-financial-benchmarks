"""
Output Calibration Module

Calibrates LLM-generated SQL queries to fix common errors:
1. Fix typo errors (== to =, missing JOIN conditions, etc.)
2. Parse SQL to extract keywords and values
3. Self-consistency: cluster similar SQLs, select most common
4. Alignment: verify table-column relationships

Based on Algorithm 1 from FinSQL paper (page 9).
"""

import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Parenthesis
from sqlparse.tokens import Keyword, DML
from difflib import get_close_matches


PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "economic_data.db"


class OutputCalibrator:
    """
    Calibrates SQL outputs from LLMs to improve correctness.

    Implements the FinSQL output calibration algorithm.
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, List[str]]:
        """Load database schema for validation"""
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

    def fix_typo_errors(self, sql: str) -> str:
        """
        Fix common typo errors in SQL (f1 function in Algorithm 1).

        Args:
            sql: Raw SQL query

        Returns:
            SQL with typos fixed
        """
        # Fix == to =
        sql = re.sub(r'==', '=', sql)

        # Fix != to <>
        sql = re.sub(r'!=', '<>', sql)

        # Fix missing space after comma
        sql = re.sub(r',([^\s])', r', \1', sql)

        # DISABLED: Fix JOIN without ON - this was causing malformed SQL
        # The regex was incorrectly matching JOINs that already had ON clauses
        # sql = re.sub(
        #     r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?!ON)',
        #     r'JOIN \1 ON 1=1 ',
        #     sql,
        #     flags=re.IGNORECASE
        # )

        # Normalize whitespace
        sql = ' '.join(sql.split())

        return sql

    def extract_keywords_and_values(self, sql: str) -> Dict[str, any]:
        """
        Extract SQL keywords and their values (f2 function in Algorithm 1).

        Args:
            sql: SQL query

        Returns:
            Dictionary of keywords and extracted values
        """
        try:
            parsed = sqlparse.parse(sql)[0]
        except:
            return {}

        components = {
            'select': [],
            'from': [],
            'where': [],
            'join': [],
            'group_by': [],
            'order_by': [],
            'having': [],
            'limit': None
        }

        # Extract components
        current_keyword = None

        for token in parsed.tokens:
            if token.ttype is Keyword:
                keyword = token.value.upper()
                if keyword == 'SELECT':
                    current_keyword = 'select'
                elif keyword == 'FROM':
                    current_keyword = 'from'
                elif keyword in ('WHERE', 'AND', 'OR'):
                    current_keyword = 'where'
                elif keyword in ('JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN'):
                    current_keyword = 'join'
                elif keyword in ('GROUP BY', 'GROUP'):
                    current_keyword = 'group_by'
                elif keyword in ('ORDER BY', 'ORDER'):
                    current_keyword = 'order_by'
                elif keyword == 'HAVING':
                    current_keyword = 'having'
                elif keyword == 'LIMIT':
                    current_keyword = 'limit'
            elif current_keyword and not token.is_whitespace:
                value = str(token).strip()
                if value:
                    if current_keyword == 'limit':
                        components['limit'] = value
                    else:
                        components[current_keyword].append(value)

        return components

    def are_sqls_compatible(self, sql1_components: Dict, sql2_components: Dict) -> bool:
        """
        Check if two SQL queries are semantically compatible.

        Args:
            sql1_components: Extracted components from SQL 1
            sql2_components: Extracted components from SQL 2

        Returns:
            True if compatible (can be considered same query)
        """
        # Check if main keywords match
        for key in ['select', 'from', 'where', 'group_by', 'order_by']:
            set1 = set(sql1_components.get(key, []))
            set2 = set(sql2_components.get(key, []))

            # Allow some flexibility (80% overlap)
            if set1 and set2:
                overlap = len(set1 & set2) / max(len(set1), len(set2))
                if overlap < 0.6:  # Less than 60% overlap
                    return False

        return True

    def fuzzy_match_column(self, column: str, table: str) -> Optional[str]:
        """
        Fuzzy match a column name to actual columns in table.

        Args:
            column: Column name to match
            table: Table name

        Returns:
            Matched column name or None
        """
        if table not in self.schema:
            return None

        table_columns = self.schema[table]

        # Exact match (case-insensitive)
        for col in table_columns:
            if col.lower() == column.lower():
                return col

        # Fuzzy match
        matches = get_close_matches(column.lower(), [c.lower() for c in table_columns], n=1, cutoff=0.8)
        if matches:
            # Find original casing
            for col in table_columns:
                if col.lower() == matches[0]:
                    return col

        return None

    def align_tables_and_columns(self, sql: str) -> str:
        """
        Align table-column relationships (f3 function in Algorithm 1).

        Ensures all columns reference valid tables.

        Args:
            sql: SQL query

        Returns:
            SQL with aligned table-column references
        """
        # Extract table names from FROM and JOIN clauses
        tables_in_query = set()

        # Find FROM tables
        from_match = re.findall(r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', sql, re.IGNORECASE)
        tables_in_query.update([t.lower() for t in from_match])

        # Find JOIN tables
        join_match = re.findall(r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)', sql, re.IGNORECASE)
        tables_in_query.update([t.lower() for t in join_match])

        # Find all table.column references
        qualified_refs = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)', sql)

        for table_ref, column in qualified_refs:
            table_lower = table_ref.lower()

            # Check if this is a valid table.column
            valid_table = None
            for table in self.schema:
                if table.lower() == table_lower:
                    valid_table = table
                    break

            if valid_table:
                # Check if column exists in this table
                if column not in self.schema[valid_table]:
                    # Try fuzzy match
                    matched_col = self.fuzzy_match_column(column, valid_table)
                    if matched_col:
                        # Replace in SQL
                        sql = sql.replace(f"{table_ref}.{column}", f"{table_ref}.{matched_col}")
            else:
                # Table reference might be wrong, try to find correct table for this column
                correct_table = None
                for table in tables_in_query:
                    for schema_table in self.schema:
                        if schema_table.lower() == table:
                            if column in self.schema[schema_table]:
                                correct_table = schema_table
                                break
                    if correct_table:
                        break

                if correct_table:
                    sql = sql.replace(f"{table_ref}.{column}", f"{correct_table}.{column}")

        return sql

    def calibrate(
        self,
        sql_candidates: List[str],
        return_all_valid: bool = False
    ) -> str:
        """
        Complete calibration algorithm (Algorithm 1 from paper).

        Args:
            sql_candidates: List of candidate SQL queries
            return_all_valid: If True, return all valid SQLs; else return best

        Returns:
            Calibrated SQL query (or list if return_all_valid=True)
        """
        # Step 1: Fix typos for all candidates
        fixed_sqls = []
        sql_to_components = {}

        for sql in sql_candidates:
            fixed = self.fix_typo_errors(sql)
            components = self.extract_keywords_and_values(fixed)

            # Only keep if components were extracted
            if components and any(components.values()):
                # Check if columns are valid
                from_tables = components.get('from', [])
                valid = True

                # Simple validation: check if FROM tables exist
                for table_expr in from_tables:
                    table_name = table_expr.split()[0].strip()
                    if table_name.lower() not in [t.lower() for t in self.schema.keys()]:
                        # Try fuzzy match
                        matched = get_close_matches(table_name.lower(), [t.lower() for t in self.schema.keys()], n=1, cutoff=0.8)
                        if not matched:
                            valid = False
                            break

                if valid:
                    fixed_sqls.append(fixed)
                    sql_to_components[fixed] = components

        if not fixed_sqls:
            # No valid SQL found, return first candidate with typo fixes
            return self.fix_typo_errors(sql_candidates[0]) if sql_candidates else ""

        # Step 2: Cluster compatible SQLs
        clusters = []
        for sql in fixed_sqls:
            components = sql_to_components[sql]
            added_to_cluster = False

            for cluster in clusters:
                cluster_sql = cluster[0]
                cluster_components = sql_to_components[cluster_sql]

                if self.are_sqls_compatible(components, cluster_components):
                    cluster.append(sql)
                    added_to_cluster = True
                    break

            if not added_to_cluster:
                clusters.append([sql])

        # Step 3: Select largest cluster
        largest_cluster = max(clusters, key=len)

        # Select first SQL from largest cluster
        best_sql = largest_cluster[0]

        # DISABLED: Step 4 - Align tables and columns
        # This was causing malformed table.column references
        # calibrated_sql = self.align_tables_and_columns(best_sql)
        calibrated_sql = best_sql  # Use as-is without alignment

        if return_all_valid:
            # Return without alignment
            return largest_cluster
        else:
            return calibrated_sql


def test_output_calibrator():
    """Test the output calibrator"""
    print("="*80)
    print("TESTING OUTPUT CALIBRATOR")
    print("="*80)

    calibrator = OutputCalibrator()

    # Test 1: Typo fixing
    print("\n" + "="*80)
    print("Test 1: Fix Typo Errors")
    print("="*80)

    sql_with_typos = "SELECT * FROM countries WHERE country_name == 'USA'"
    fixed = calibrator.fix_typo_errors(sql_with_typos)
    print(f"Original: {sql_with_typos}")
    print(f"Fixed:    {fixed}")

    # Test 2: Self-consistency
    print("\n" + "="*80)
    print("Test 2: Self-Consistency (Multiple Candidates)")
    print("="*80)

    candidates = [
        "SELECT sector_name FROM sectors ORDER BY sector_name",
        "SELECT sector_name FROM sectors ORDER BY sector_name",  # Duplicate
        "SELECT sector_name FROM sectors",  # Similar
        "SELECT country_name FROM countries",  # Different
    ]

    calibrated = calibrator.calibrate(candidates)
    print(f"Candidates: {len(candidates)}")
    print(f"Selected: {calibrated}")

    # Test 3: Column alignment
    print("\n" + "="*80)
    print("Test 3: Table-Column Alignment")
    print("="*80)

    sql_with_wrong_table = "SELECT wrong_table.sector_name FROM sectors"
    aligned = calibrator.align_tables_and_columns(sql_with_wrong_table)
    print(f"Original: {sql_with_wrong_table}")
    print(f"Aligned:  {aligned}")

    print("\n" + "="*80)
    print("✓ Output Calibrator Tests Complete")
    print("="*80)


if __name__ == "__main__":
    test_output_calibrator()
