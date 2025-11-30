"""
Evaluate Zero-Shot Baseline on All Models
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.zero_shot_baseline import ZeroShotBaseline
from shared.database import is_correct_sql, execute_sql

DB_PATH = project_root / "database" / "economic_data.db"


def evaluate_zero_shot(model_name: str, test_file: str = None):
    """Evaluate zero-shot baseline on a model"""

    if test_file is None:
        test_file = str(project_root / "data" / "test" / "queries.json")

    # Load test data
    with open(test_file, 'r') as f:
        test_data = json.load(f)

    print(f"{'='*80}")
    print(f"ZERO-SHOT BASELINE: {model_name}")
    print(f"{'='*80}")

    # Initialize baseline
    baseline = ZeroShotBaseline(model_name=model_name, verbose=False)

    # Results
    correct = 0
    execution_errors = 0
    results_list = []

    for idx, query_data in enumerate(test_data, 1):
        question = query_data["question"]
        ground_truth = query_data["ground_truth_sql"]

        try:
            # Generate SQL
            result = baseline.generate(question)
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
                "error": str(e)
            })

    accuracy = (correct / len(test_data)) * 100

    print(f"\n  Result: {correct}/{len(test_data)} ({accuracy:.1f}%)")
    print(f"  Execution errors: {execution_errors}")
    print(f"{'='*80}\n")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_safe_name = model_name.replace("/", "_").replace("-", "_")
    results_dir = project_root / "data" / "results" / "zero_shot"
    results_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "model": model_name,
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
    models = [
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "openai/gpt-oss-20b",
    ]

    all_results = {}

    for model in models:
        print(f"\n{'='*80}")
        print(f"Testing: {model}")
        print(f"{'='*80}\n")

        results = evaluate_zero_shot(model)
        all_results[model] = results

    # Print summary
    print(f"\n{'='*80}")
    print("ZERO-SHOT SUMMARY - ALL MODELS")
    print(f"{'='*80}\n")

    for model, results in all_results.items():
        model_short = model.split("/")[-1]
        print(f"{model_short:40s}: {results['correct']}/21 ({results['accuracy']:.1f}%) | Errors: {results['execution_errors']}")
