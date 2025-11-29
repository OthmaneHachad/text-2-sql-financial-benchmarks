"""
Data Augmentation Module for FinSQL
Implements 4 augmentation strategies: CoT, Synonym, Skeleton, Hard Examples
"""
import sys
import re
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from together import Together
from shared.helpers import CostTracker
from shared.config import TOGETHER_API_KEY, CURRENT_MODEL
from finsql.config import (
    AUGMENTATION_CONFIG,
    ECONOMIC_SYNONYMS,
    FINSQL_TEMPERATURE,
    FINSQL_MAX_TOKENS,
    AUGMENTED_DATA_DIR,
    COT_DATA_PATH,
    SYNONYM_DATA_PATH,
    SKELETON_DATA_PATH,
    HARD_DATA_PATH
)


class DataAugmenter:
    """Augment training data with CoT, synonyms, skeletons, and hard examples"""

    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.model = CURRENT_MODEL
        self.cost_tracker = CostTracker(model=self.model)
        self.synonyms = ECONOMIC_SYNONYMS
        self.config = AUGMENTATION_CONFIG

        # Ensure output directory exists
        AUGMENTED_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Import validation utilities
        from shared.database import execute_sql
        from shared.config import DB_PATH
        self.execute_sql = execute_sql
        self.db_path = DB_PATH

        # Validation stats
        self.validation_stats = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'placeholder': 0
        }

    # =====================
    # Validation Methods
    # =====================

    def has_placeholders(self, sql: str) -> bool:
        """Check if SQL contains placeholders"""
        placeholder_patterns = [
            r'\[YEAR\]', r'\[METRIC\]', r'\[STRING\]',
            r'\[ID\]', r'\[VALUE\]', r'\[NUMBER\]',
            r'\[TABLE\]', r'\[COLUMN\]', r'\[CODE\]'
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return True
        return False

    def validate_sql(self, sql: str) -> bool:
        """
        Validate SQL can execute without errors

        Returns:
            True if valid, False otherwise
        """
        self.validation_stats['total'] += 1

        # Check for placeholders
        if self.has_placeholders(sql):
            self.validation_stats['placeholder'] += 1
            self.validation_stats['invalid'] += 1
            return False

        # Check execution
        try:
            result = self.execute_sql(sql, self.db_path)
            if result is None:
                self.validation_stats['invalid'] += 1
                return False
            self.validation_stats['valid'] += 1
            return True
        except Exception:
            self.validation_stats['invalid'] += 1
            return False

    # =====================
    # CoT Augmentation
    # =====================

    def augment_cot(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add Chain-of-Thought reasoning to query

        Args:
            query: Original query dict with 'question' and 'ground_truth_sql'

        Returns:
            Augmented query with 'reasoning' field
        """
        prompt = f"""You are an expert SQL developer. For the following natural language question, explain step-by-step how to construct the SQL query to answer it.

Question: {query['question']}

Provide a clear, logical breakdown of the steps needed to answer this question with SQL. Focus on:
1. What data is needed
2. Which tables/columns to use
3. What filters or conditions to apply
4. What aggregations or calculations are needed

Format your response as numbered steps, being concise but thorough."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert at breaking down SQL problems into logical steps."},
                {"role": "user", "content": prompt}
            ],
            temperature=FINSQL_TEMPERATURE["augmentation"],
            max_tokens=FINSQL_MAX_TOKENS["augmentation"]
        )

        reasoning = response.choices[0].message.content.strip()

        # Track token usage
        self.cost_tracker.add_usage(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        # Create augmented query
        augmented = query.copy()
        augmented['reasoning'] = reasoning
        augmented['augmentation_type'] = 'cot'
        augmented['original_question'] = query['question']

        return augmented

    # =====================
    # Synonym Augmentation
    # =====================

    def augment_synonym(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace words with domain-specific synonyms

        Args:
            query: Original query dict

        Returns:
            Augmented query with replaced words
        """
        question = query['question']
        replacements = {}

        # For each term in synonym dictionary, check if it appears in question
        for original_term, synonym_list in self.synonyms.items():
            # Use word boundaries to match whole words only
            pattern = r'\b' + re.escape(original_term) + r'\b'

            if re.search(pattern, question, re.IGNORECASE):
                # Randomly select a synonym
                synonym = random.choice(synonym_list)

                # Replace (case-insensitive)
                question = re.sub(pattern, synonym, question, flags=re.IGNORECASE)
                replacements[original_term] = synonym

        # Create augmented query
        augmented = query.copy()
        augmented['question'] = question
        augmented['original_question'] = query['question']
        augmented['augmentation_type'] = 'synonym'
        augmented['replacements'] = replacements

        return augmented

    # =====================
    # Skeleton Augmentation
    # =====================

    def augment_skeleton(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create SQL skeleton and generalized question using LLM

        Args:
            query: Original query dict

        Returns:
            Augmented query with SQL skeleton and generic question
        """
        # First, create SQL skeleton programmatically
        sql = query['ground_truth_sql']
        skeleton = self._create_sql_skeleton(sql)

        # Then, use LLM to generate generic question
        prompt = f"""Given this specific SQL query question and the SQL pattern, generate a GENERIC version of the question that describes the query type without specific values.

Original Question: {query['question']}
Original SQL: {sql}
SQL Pattern: {skeleton}

Generate a generic question that describes what KIND of query this is, using placeholders like [metric], [country], [year], [table], etc. instead of specific values.

Examples:
- "Show Brazil's GDP in 2020" → "Retrieve specific metric for country in given year"
- "Compare revenue between USA and China" → "Compare metric between two countries"
- "What is the average expenditure by sector?" → "Calculate average of metric grouped by dimension"

Generic Question:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert at abstracting SQL queries into generic patterns."},
                {"role": "user", "content": prompt}
            ],
            temperature=FINSQL_TEMPERATURE["augmentation"],
            max_tokens=200
        )

        generic_question = response.choices[0].message.content.strip()

        # Track token usage
        self.cost_tracker.add_usage(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        # Classify pattern type
        pattern_type = self._classify_pattern(sql)

        # Create augmented query
        augmented = query.copy()
        augmented['question'] = generic_question
        augmented['original_question'] = query['question']
        augmented['sql_skeleton'] = skeleton
        augmented['pattern_type'] = pattern_type
        augmented['augmentation_type'] = 'skeleton'

        return augmented

    def _create_sql_skeleton(self, sql: str) -> str:
        """
        Create SQL skeleton by replacing specific values with placeholders

        Args:
            sql: Original SQL query

        Returns:
            SQL skeleton with placeholders
        """
        skeleton = sql

        # Replace string literals
        skeleton = re.sub(r"'[^']*'", "[STRING]", skeleton)

        # Replace numbers (but not in function names)
        skeleton = re.sub(r'\b\d+\b', "[NUMBER]", skeleton)

        # Replace specific column names with generic placeholders
        # This is a simple version - could be more sophisticated
        common_columns = {
            'revenue': '[METRIC]',
            'expenditure': '[METRIC]',
            'value': '[METRIC]',
            'country_id': '[ID]',
            'indicator_code': '[CODE]',
            'year': '[YEAR]',
        }

        for col, placeholder in common_columns.items():
            skeleton = re.sub(r'\b' + col + r'\b', placeholder, skeleton, flags=re.IGNORECASE)

        return skeleton

    def _classify_pattern(self, sql: str) -> str:
        """
        Classify SQL query pattern type

        Args:
            sql: SQL query

        Returns:
            Pattern type string
        """
        sql_upper = sql.upper()

        # Check for different patterns
        has_join = 'JOIN' in sql_upper
        has_group_by = 'GROUP BY' in sql_upper
        has_having = 'HAVING' in sql_upper
        has_subquery = sql_upper.count('SELECT') > 1
        has_aggregation = any(agg in sql_upper for agg in ['SUM(', 'AVG(', 'COUNT(', 'MAX(', 'MIN('])
        has_order_by = 'ORDER BY' in sql_upper

        # Classify based on patterns
        if has_subquery:
            return 'nested_query'
        elif has_join and has_group_by:
            return 'multi_table_aggregation'
        elif has_join:
            return 'multi_table_join'
        elif has_group_by and has_having:
            return 'filtered_aggregation'
        elif has_group_by:
            return 'grouped_aggregation'
        elif has_aggregation:
            return 'simple_aggregation'
        elif has_order_by:
            return 'sorted_retrieval'
        else:
            return 'simple_select'

    # =====================
    # Hard Examples Augmentation
    # =====================

    def augment_hard_examples(
        self,
        queries: List[Dict[str, Any]],
        magic_results_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract and augment hard examples (failed MAGIC queries)

        Args:
            queries: All training queries
            magic_results_path: Path to MAGIC results file (optional)

        Returns:
            List of hard example queries with metadata
        """
        hard_examples = []

        # Strategy 1: Use queries marked as "hard" difficulty
        for query in queries:
            if query.get('difficulty') == 'hard':
                augmented = query.copy()
                augmented['augmentation_type'] = 'hard_example'
                augmented['original_question'] = query['question']
                augmented['selection_reason'] = 'high_difficulty'
                hard_examples.append(augmented)

        # Strategy 2: Load MAGIC results if available (optional)
        if magic_results_path and Path(magic_results_path).exists():
            hard_examples.extend(self._load_magic_failures(magic_results_path, queries))

        return hard_examples

    def _load_magic_failures(
        self,
        results_path: str,
        all_queries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Load failed queries from MAGIC results

        Args:
            results_path: Path to MAGIC results JSON
            all_queries: All training queries

        Returns:
            List of failed queries with metadata
        """
        try:
            with open(results_path, 'r') as f:
                results = json.load(f)

            failed_examples = []

            # Find queries that failed in MAGIC
            for result in results.get('results', []):
                if not result.get('correction_success', False):
                    # Find matching query in training set
                    query_id = result.get('id')
                    matching_query = next(
                        (q for q in all_queries if q.get('id') == query_id),
                        None
                    )

                    if matching_query:
                        augmented = matching_query.copy()
                        augmented['augmentation_type'] = 'hard_example'
                        augmented['original_question'] = matching_query['question']
                        augmented['magic_failed'] = True
                        augmented['selection_reason'] = 'magic_failure'

                        # Add error context if available
                        if 'error' in result:
                            augmented['common_errors'] = [result['error']]

                        failed_examples.append(augmented)

            return failed_examples

        except Exception as e:
            print(f"Warning: Could not load MAGIC results: {e}")
            return []

    # =====================
    # Batch Processing
    # =====================

    def augment_all(
        self,
        queries: List[Dict[str, Any]],
        save: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run all augmentation types on queries

        Args:
            queries: List of training queries
            save: Whether to save results to files

        Returns:
            Dict with augmented datasets for each type
        """
        results = {}

        print(f"\n{'='*80}")
        print(f"DATA AUGMENTATION - {len(queries)} queries")
        print(f"{'='*80}\n")

        # CoT Augmentation
        if self.config['enable_cot']:
            print("1. Chain-of-Thought Augmentation...")
            cot_data = []
            for i, query in enumerate(queries):
                print(f"   [{i+1}/{len(queries)}] {query['question'][:60]}...")
                augmented = self.augment_cot(query)
                cot_data.append(augmented)

            results['cot'] = cot_data
            if save:
                self._save_data(cot_data, COT_DATA_PATH)
            print(f"   ✓ Generated {len(cot_data)} CoT examples\n")

        # Synonym Augmentation
        if self.config['enable_synonym']:
            print("2. Synonym Replacement Augmentation...")
            synonym_data = []
            for i, query in enumerate(queries):
                augmented = self.augment_synonym(query)
                if augmented.get('replacements'):
                    synonym_data.append(augmented)
                    print(f"   [{i+1}/{len(queries)}] Replaced: {augmented['replacements']}")
                else:
                    print(f"   [{i+1}/{len(queries)}] No synonyms found")

            results['synonym'] = synonym_data
            if save:
                self._save_data(synonym_data, SYNONYM_DATA_PATH)
            print(f"   ✓ Generated {len(synonym_data)} synonym examples\n")

        # Skeleton Augmentation
        if self.config['enable_skeleton']:
            print("3. Skeleton-based Augmentation...")
            skeleton_data = []
            for i, query in enumerate(queries):
                print(f"   [{i+1}/{len(queries)}] {query['question'][:60]}...")
                augmented = self.augment_skeleton(query)
                skeleton_data.append(augmented)

            results['skeleton'] = skeleton_data
            if save:
                self._save_data(skeleton_data, SKELETON_DATA_PATH)
            print(f"   ✓ Generated {len(skeleton_data)} skeleton examples\n")

        # Hard Examples Augmentation
        if self.config['enable_hard_examples']:
            print("4. Hard Examples Augmentation...")
            hard_data = self.augment_hard_examples(queries)
            results['hard'] = hard_data
            if save:
                self._save_data(hard_data, HARD_DATA_PATH)
            print(f"   ✓ Extracted {len(hard_data)} hard examples\n")

        # Validate all SQLs
        print(f"\n{'='*80}")
        print("VALIDATING GENERATED SQLs")
        print(f"{'='*80}\n")
        for aug_type, data in results.items():
            print(f"{aug_type.upper()} Validation:")
            for example in data:
                sql = example.get('ground_truth_sql', '')
                if not self.validate_sql(sql):
                    print(f"  ⚠️  Invalid SQL: {sql[:60]}...")

        # Print cost summary
        print(f"\n{'='*80}")
        print("AUGMENTATION COMPLETE")
        print(f"{'='*80}")
        self.cost_tracker.report()

        # Print validation summary
        if self.validation_stats['total'] > 0:
            print(f"\n{'='*80}")
            print("VALIDATION SUMMARY")
            print(f"{'='*80}")
            print(f"Total SQLs validated: {self.validation_stats['total']}")
            print(f"Valid: {self.validation_stats['valid']} ({self.validation_stats['valid']/self.validation_stats['total']*100:.1f}%)")
            print(f"Invalid: {self.validation_stats['invalid']}")
            print(f"  - With placeholders: {self.validation_stats['placeholder']}")
            print(f"  - Execution errors: {self.validation_stats['invalid'] - self.validation_stats['placeholder']}")

        # Summary
        total_examples = sum(len(data) for data in results.values())
        print(f"\nTotal augmented examples: {total_examples}")
        for aug_type, data in results.items():
            print(f"  - {aug_type}: {len(data)} examples")

        return results

    # =====================
    # Save/Load Utilities
    # =====================

    def _save_data(self, data: List[Dict[str, Any]], filepath: Path):
        """Save augmented data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"   Saved to: {filepath}")

    def load_augmented_data(self, aug_type: str) -> List[Dict[str, Any]]:
        """
        Load augmented data by type

        Args:
            aug_type: 'cot', 'synonym', 'skeleton', or 'hard'

        Returns:
            List of augmented queries
        """
        filepath_map = {
            'cot': COT_DATA_PATH,
            'synonym': SYNONYM_DATA_PATH,
            'skeleton': SKELETON_DATA_PATH,
            'hard': HARD_DATA_PATH
        }

        filepath = filepath_map.get(aug_type)
        if not filepath or not filepath.exists():
            raise FileNotFoundError(f"Augmented data not found: {aug_type}")

        with open(filepath, 'r') as f:
            return json.load(f)


# =====================
# Test Function
# =====================

def test_augmentation(num_queries: int = 5):
    """
    Test augmentation on a few sample queries

    Args:
        num_queries: Number of queries to test
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from shared.data_loader import load_queries
    from shared.config import TRAIN_DATA_PATH

    # Load training data
    queries = load_queries(TRAIN_DATA_PATH)[:num_queries]

    print(f"\n{'='*80}")
    print(f"TESTING AUGMENTATION ON {num_queries} QUERIES")
    print(f"{'='*80}\n")

    # Create augmenter
    augmenter = DataAugmenter()

    # Test each augmentation type
    print("\n--- Testing CoT Augmentation ---")
    cot_example = augmenter.augment_cot(queries[0])
    print(f"Original: {queries[0]['question']}")
    print(f"Reasoning:\n{cot_example['reasoning']}\n")

    print("\n--- Testing Synonym Augmentation ---")
    synonym_example = augmenter.augment_synonym(queries[1])
    print(f"Original: {queries[1]['question']}")
    print(f"Modified: {synonym_example['question']}")
    print(f"Replacements: {synonym_example.get('replacements', {})}\n")

    print("\n--- Testing Skeleton Augmentation ---")
    skeleton_example = augmenter.augment_skeleton(queries[2])
    print(f"Original: {queries[2]['question']}")
    print(f"Original SQL: {queries[2]['ground_truth_sql']}")
    print(f"Generic Question: {skeleton_example['question']}")
    print(f"SQL Skeleton: {skeleton_example['sql_skeleton']}")
    print(f"Pattern Type: {skeleton_example['pattern_type']}\n")

    print("\n--- Testing Hard Examples ---")
    hard_examples = augmenter.augment_hard_examples(queries)
    print(f"Found {len(hard_examples)} hard examples")
    if hard_examples:
        print(f"Example: {hard_examples[0]['question']}")
        print(f"Reason: {hard_examples[0].get('selection_reason')}\n")

    # Print cost
    augmenter.cost_tracker.report()


if __name__ == "__main__":
    test_augmentation(num_queries=5)
