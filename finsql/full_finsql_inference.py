"""
Full FinSQL Inference Pipeline

Integrates all three FinSQL components:
1. Schema Linking (Embedding-based)
2. LoRA Inference (4 specialized plugins)
3. Output Calibration (typo fixing, self-consistency, alignment)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from finsql.modules.embedding_schema_linker import EmbeddingSchemaLinker
from finsql.lora.inference import LoRAInference
from finsql.modules.output_calibrator import OutputCalibrator
from shared.database import is_correct_sql


PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "economic_data.db"
TEST_DATA_PATH = PROJECT_ROOT / "data" / "test" / "queries.json"
RESULTS_DIR = PROJECT_ROOT / "data" / "results" / "finsql"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class FullFinSQLInference:
    """Complete FinSQL inference pipeline"""

    def __init__(self):
        print("="*80)
        print("INITIALIZING FULL FINSQL PIPELINE")
        print("="*80)

        # Initialize components
        print("\n[1/3] Loading Schema Linker...")
        self.schema_linker = EmbeddingSchemaLinker(db_path=str(DB_PATH))

        print("\n[2/3] Loading LoRA Models...")
        self.lora_inference = LoRAInference()

        print("\n[3/3] Loading Output Calibrator...")
        self.calibrator = OutputCalibrator(db_path=str(DB_PATH))

        print("\n✓ FinSQL Pipeline Ready!")

    def generate_sql(
        self,
        question: str,
        num_candidates: int = 5,
        top_k_tables: int = 3,
        top_k_columns: int = 5
    ) -> Dict:
        """
        Generate SQL using full FinSQL pipeline.

        Args:
            question: Natural language question
            num_candidates: Number of SQL candidates to generate
            top_k_tables: Number of tables to retrieve via schema linking
            top_k_columns: Number of columns to retrieve per table

        Returns:
            Dictionary with generated SQL and metadata
        """
        # Step 1: Schema Linking
        linked_schema = self.schema_linker.link_schema(
            question,
            top_k_tables=top_k_tables,
            top_k_columns_per_table=top_k_columns
        )

        # Format schema for prompt
        schema_text = self.schema_linker.format_linked_schema(linked_schema)

        # Step 2: Generate multiple SQL candidates using ensemble
        candidates = []

        for i in range(num_candidates):
            result = self.lora_inference.strategy_individual_ensemble(
                question,
                schema_override=schema_text,
                select_best=False  # Get all 4 plugin outputs
            )

            # Extract SQL from all plugins
            for plugin_name, plugin_result in result['candidates'].items():
                sql = plugin_result.get('sql', '')
                if sql:
                    candidates.append(sql)

            # Cost is tracked automatically by LoRA inference

        # Step 3: Output Calibration
        if candidates:
            calibrated_sql = self.calibrator.calibrate(candidates)
        else:
            calibrated_sql = ""

        return {
            'question': question,
            'linked_schema': linked_schema,
            'candidates': candidates,
            'final_sql': calibrated_sql,
            'num_candidates': len(candidates)
        }

    def evaluate(self, num_queries: int = None) -> Dict:
        """
        Evaluate FinSQL on test queries.

        Args:
            num_queries: Number of queries to evaluate (None = all)

        Returns:
            Evaluation results
        """
        # Load test data
        with open(TEST_DATA_PATH, 'r') as f:
            all_queries = json.load(f)

        queries = all_queries[:num_queries] if num_queries else all_queries

        print("\n" + "="*80)
        print(f"EVALUATING FULL FINSQL ON {len(queries)} QUERIES")
        print("="*80)

        results = []
        correct = 0

        for i, query in enumerate(queries, 1):
            question = query['question']
            ground_truth_sql = query['ground_truth_sql']

            print(f"\n[{i}/{len(queries)}] {question[:60]}...")

            # Generate SQL
            result = self.generate_sql(question)
            predicted_sql = result['final_sql']

            # Check correctness
            is_correct = is_correct_sql(predicted_sql, ground_truth_sql, str(DB_PATH))

            if is_correct:
                correct += 1
                status = "✓ CORRECT"
            else:
                status = "✗ INCORRECT"

            print(f"  {status}")
            print(f"  Candidates: {result['num_candidates']}")
            print(f"  Predicted: {predicted_sql[:80]}...")

            results.append({
                'id': query['id'],
                'question': question,
                'ground_truth_sql': ground_truth_sql,
                'predicted_sql': predicted_sql,
                'is_correct': is_correct,
                'num_candidates': result['num_candidates'],
                'linked_tables': result['linked_schema']['linked_tables']
            })

        accuracy = correct / len(queries) if queries else 0

        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)
        print(f"Accuracy: {correct}/{len(queries)} ({accuracy*100:.1f}%)")
        print("\nCost Report:")
        self.lora_inference.get_cost_report()

        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': len(queries),
            'results': results
        }


def main():
    """Run full FinSQL evaluation"""
    import argparse

    parser = argparse.ArgumentParser(description='Full FinSQL Inference')
    parser.add_argument('--num-queries', type=int, default=None,
                        help='Number of queries to evaluate (default: all)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file for results')

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = FullFinSQLInference()

    # Run evaluation
    eval_results = pipeline.evaluate(num_queries=args.num_queries)

    # Save results
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = RESULTS_DIR / f"full_finsql_eval_{timestamp}.json"

    with open(output_path, 'w') as f:
        json.dump(eval_results, f, indent=2)

    print(f"\n✓ Results saved to: {output_path}")


if __name__ == "__main__":
    main()
