"""
Evaluate Enhanced MAGIC on Any Model

Enhanced MAGIC combines:
- Schema linking (top-5 tables)
- Filtered guidelines (top-3 patterns)
- Self-consistency voting (10 samples)
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.enhanced_inference import EnhancedMAGIC
from shared.database import is_correct_sql, execute_sql

DB_PATH = project_root / "database" / "economic_data.db"


def evaluate_enhanced_magic(model_name: str, test_file: str = None):
    """Evaluate Enhanced MAGIC on a model"""

    if test_file is None:
        test_file = str(project_root / "data" / "test" / "queries.json")

    # Load test data
    with open(test_file, 'r') as f:
        test_data = json.load(f)

    print(f"{'='*80}")
    print(f"ENHANCED MAGIC: {model_name}")
    print(f"{'='*80}")

    # Initialize Enhanced MAGIC
    enhanced = EnhancedMAGIC(
        num_samples=10,  # Self-consistency voting with 10 samples
        use_full_guideline=False,  # Filter to top-3 patterns
        verbose=False
    )

    # Patch model name
    enhanced.model_name = model_name

    # Results
    correct = 0
    execution_errors = 0
    results_list = []

    for idx, query_data in enumerate(test_data, 1):
        question = query_data["question"]
        ground_truth = query_data["ground_truth_sql"]

        try:
            # Generate SQL with Enhanced MAGIC
            result = enhanced.generate(question)
            predicted_sql = result["sql"]

            # Check correctness
            is_correct = is_correct_sql(predicted_sql, ground_truth, str(DB_PATH))

            # Check execution
            exec_result = execute_sql(predicted_sql, str(DB_PATH))
            execution_success = exec_result["success"]

            if is_correct:
                correct += 1
            if not execution_success:
                execution_errors += 1

            results_list.append({
                "id": query_data["id"],
                "correct": is_correct,
                "execution_success": execution_success,
                "predicted_sql": predicted_sql,
                "ground_truth_sql": ground_truth,
                "num_candidates": len(result.get("candidates", [])),
                "voting_winner_count": result.get("voting_details", {}).get("winner_count", 1),
            })

            status = "✓" if is_correct else "✗"
            print(f"  Query {idx}/21: {status}")

        except Exception as e:
            print(f"  Query {idx}/21: ✗ ERROR: {str(e)[:50]}")
            execution_errors += 1
            results_list.append({
                "id": query_data["id"],
                "correct": False,
                "execution_success": False,
                "error": str(e),
                "ground_truth_sql": ground_truth,
            })

    accuracy = (correct / len(test_data)) * 100

    print(f"\n  Result: {correct}/{len(test_data)} ({accuracy:.1f}%)")
    print(f"  Execution errors: {execution_errors}")
    print(f"{'='*80}\n")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_safe_name = model_name.replace("/", "_").replace("-", "_")
    results_dir = project_root / "data" / "results" / "enhanced_magic"
    results_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "model": model_name,
        "method": "Enhanced MAGIC",
        "timestamp": timestamp,
        "correct": correct,
        "total": len(test_data),
        "accuracy": accuracy,
        "execution_errors": execution_errors,
        "results": results_list
    }

    output_file = results_dir / f"{model_safe_name}_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_file}\n")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python evaluate_enhanced_magic.py <model_name>")
        print("\nAvailable models:")
        print("  - meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
        print("  - meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo")
        print("  - openai/gpt-oss-20b")
        print("  - mistralai/Mistral-7B-Instruct-v0.3")
        print("  - Qwen/Qwen2.5-7B-Instruct-Turbo")
        sys.exit(1)

    model_name = sys.argv[1]
    evaluate_enhanced_magic(model_name)
