"""
FinSQL LoRA Inference
Generate SQL using fine-tuned LoRA plugins
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from together import Together
from shared.helpers import CostTracker, extract_sql
from shared.database import format_schema
from shared.config import TOGETHER_API_KEY, DB_PATH
from finsql.config import (
    PLUGIN_REGISTRY_PATH,
    FINSQL_TEMPERATURE,
    FINSQL_MAX_TOKENS,
    PLUGIN_CONFIG
)


class LoRAInference:
    """Generate SQL using fine-tuned LoRA plugins"""

    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.cost_tracker = CostTracker()
        self.schema = format_schema(DB_PATH)

        # Load plugin registry
        self.plugins = self._load_plugin_registry()

        print(f"✓ Loaded {len(self.plugins)} LoRA plugins:")
        for name in self.plugins.keys():
            print(f"  - {name}")

    def _load_plugin_registry(self) -> Dict[str, str]:
        """Load plugin model IDs from registry"""
        if not PLUGIN_REGISTRY_PATH.exists():
            raise FileNotFoundError(f"Plugin registry not found: {PLUGIN_REGISTRY_PATH}")

        with open(PLUGIN_REGISTRY_PATH, 'r') as f:
            return json.load(f)

    # =====================
    # Single Plugin Inference
    # =====================

    def generate_with_plugin(
        self,
        question: str,
        plugin_name: str,
        schema: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> tuple[str, int, int]:
        """
        Generate SQL using a specific LoRA plugin

        Args:
            question: Natural language question
            plugin_name: Plugin to use (cot_specialist, etc.)
            schema: Database schema (default: loaded schema)
            temperature: Generation temperature
            max_tokens: Max tokens to generate

        Returns:
            (sql, input_tokens, output_tokens)
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"Unknown plugin: {plugin_name}")

        model_id = self.plugins[plugin_name]
        schema = schema or self.schema
        temperature = temperature or FINSQL_TEMPERATURE["inference"]
        max_tokens = max_tokens or FINSQL_MAX_TOKENS["inference"]

        # Common instructions for all plugins
        no_placeholder_instruction = """
IMPORTANT: Generate executable SQL only. Use concrete values from the question (e.g., 2020, not [YEAR]). Never use placeholders like [METRIC], [STRING], [ID], [TABLE], or [COLUMN]."""

        # Build prompt based on plugin type
        if plugin_name == "cot_specialist":
            user_prompt = f"""Database Schema:
{schema}

Question: {question}

First explain your reasoning step-by-step, then generate the SQL query.{no_placeholder_instruction}"""

        elif plugin_name == "robustness_specialist":
            user_prompt = f"""Database Schema:
{schema}

Question: {question}{no_placeholder_instruction}"""

        elif plugin_name == "structure_specialist":
            user_prompt = f"""Database Schema:
{schema}

Question: {question}

Identify the SQL pattern needed and generate the query.{no_placeholder_instruction}"""

        elif plugin_name == "hard_cases_specialist":
            user_prompt = f"""Database Schema:
{schema}

Question: {question}

Pay careful attention to edge cases and complex operations.{no_placeholder_instruction}"""

        else:
            # Default prompt
            user_prompt = f"""Database Schema:
{schema}

Question: {question}{no_placeholder_instruction}"""

        # Call fine-tuned model
        response = self.client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Extract SQL from response
        content = response.choices[0].message.content
        sql = extract_sql(content)

        # Track usage
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        self.cost_tracker.add_usage(input_tokens, output_tokens)

        return sql, input_tokens, output_tokens

    # =====================
    # Ensemble Inference
    # =====================

    def generate_ensemble(
        self,
        question: str,
        plugins: Optional[List[str]] = None,
        schema: Optional[str] = None
    ) -> Dict[str, tuple[str, int, int]]:
        """
        Generate SQL using multiple plugins (ensemble)

        Args:
            question: Natural language question
            plugins: List of plugin names (default: all 4)
            schema: Database schema

        Returns:
            Dict mapping plugin names to (sql, input_tokens, output_tokens)
        """
        if plugins is None:
            plugins = list(self.plugins.keys())

        results = {}

        for plugin_name in plugins:
            sql, in_tok, out_tok = self.generate_with_plugin(
                question, plugin_name, schema
            )
            results[plugin_name] = (sql, in_tok, out_tok)

        return results

    # =====================
    # Strategy 1: Merged Only (Not implemented yet - needs API support)
    # =====================

    # Note: TogetherAI doesn't support runtime LoRA merging via API yet
    # This would require downloading adapters and merging locally
    # For now, we'll use Strategy 2 (Individual Ensemble)

    # =====================
    # Strategy 2: Individual Ensemble
    # =====================

    def strategy_individual_ensemble(
        self,
        question: str,
        select_best: bool = True,
        schema_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Strategy 2: Run all 4 plugins and optionally select best

        Args:
            question: Natural language question
            select_best: Whether to select best SQL (simple heuristic)
            schema_override: Custom schema text (from schema linking)

        Returns:
            Results dict with all SQLs and optionally the best one
        """
        # Generate from all plugins
        results = self.generate_ensemble(question, schema=schema_override)

        output = {
            "question": question,
            "candidates": {},
            "total_input_tokens": 0,
            "total_output_tokens": 0
        }

        for plugin_name, (sql, in_tok, out_tok) in results.items():
            output["candidates"][plugin_name] = {
                "sql": sql,
                "input_tokens": in_tok,
                "output_tokens": out_tok
            }
            output["total_input_tokens"] += in_tok
            output["total_output_tokens"] += out_tok

        # Simple selection: choose most common SQL or shortest
        if select_best:
            sqls = [r[0] for r in results.values()]

            # Count occurrences
            from collections import Counter
            sql_counts = Counter(sqls)

            # If multiple plugins agree, use that
            if sql_counts.most_common(1)[0][1] > 1:
                output["best_sql"] = sql_counts.most_common(1)[0][0]
                output["selection_method"] = "consensus"
            else:
                # Otherwise, prefer structure specialist
                output["best_sql"] = results["structure_specialist"][0]
                output["selection_method"] = "structure_specialist"

        return output

    # =====================
    # Strategy 3: Full Ensemble (4 individual + merged)
    # =====================

    # Would add merged LoRA here once API supports it
    # For now, same as Strategy 2

    # =====================
    # Utility Methods
    # =====================

    def get_cost_report(self):
        """Print cost report"""
        self.cost_tracker.report()


# =====================
# Test Function
# =====================

def test_inference(num_queries: int = None):
    """Test LoRA inference on sample queries"""
    from shared.data_loader import load_queries
    from shared.config import TEST_DATA_PATH
    from shared.database import is_correct_sql

    print("\n" + "="*80)
    print("TESTING FINSQL LORA INFERENCE")
    print("="*80 + "\n")

    # Load test queries
    all_queries = load_queries(TEST_DATA_PATH)
    queries = all_queries[:num_queries] if num_queries else all_queries

    print(f"Testing on {len(queries)} queries (out of {len(all_queries)} total)")
    print()

    # Initialize inference
    inference = LoRAInference()

    print("\n" + "-"*80)
    print("STRATEGY: Individual Ensemble (4 plugins)")
    print("-"*80 + "\n")

    correct = 0
    total = len(queries)

    for i, query in enumerate(queries):
        print(f"\n[{i+1}/{total}] {query['question'][:70]}...")

        # Run ensemble
        result = inference.strategy_individual_ensemble(
            query['question'],
            select_best=True
        )

        # Display candidates
        print("\nCandidates:")
        for plugin_name, candidate in result["candidates"].items():
            sql = candidate["sql"][:80]
            print(f"  {plugin_name:25s}: {sql}...")

        # Check if best is correct
        best_sql = result.get("best_sql", "")
        is_correct = is_correct_sql(best_sql, query["ground_truth_sql"], DB_PATH)

        if is_correct:
            print(f"\n✓ CORRECT (selected by {result['selection_method']})")
            correct += 1
        else:
            print(f"\n✗ INCORRECT")
            print(f"Expected: {query['ground_truth_sql'][:100]}...")
            print(f"Got:      {best_sql[:100]}...")

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\nAccuracy: {correct}/{total} ({correct/total*100:.1f}%)")

    inference.get_cost_report()


if __name__ == "__main__":
    test_inference()
