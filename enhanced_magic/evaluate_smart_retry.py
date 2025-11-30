"""
Evaluate Smart MAGIC + Execution-Guided Retry
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.smart_inference_retry import SmartMAGICWithRetry
from enhanced_magic.config import DB_PATH, MODEL_NAME
from shared.database import is_correct_sql, execute_sql


def evaluate_smart_magic_retry(
    test_file: str = None,
    max_queries: int = None,
    max_retries: int = 2,
    top_k_detailed: int = 3,
    verbose: bool = True,
    save_results: bool = True,
) -> Dict[str, Any]:
    """
    Evaluate Smart MAGIC + Retry on test set

    Args:
        test_file: Path to test queries JSON
        max_queries: Limit number of queries (None = all)
        max_retries: Maximum retry attempts per query
        top_k_detailed: Number of tables to show in full detail
        verbose: Print detailed results
        save_results: Save results to JSON file
    """

    # Use default test file if not specified
    if test_file is None:
        test_file = str(project_root / "data" / "test" / "queries.json")

    # Load test data
    with open(test_file, 'r') as f:
        test_data = json.load(f)

    if max_queries:
        test_data = test_data[:max_queries]

    print("="*80)
    print(f"SMART MAGIC + RETRY EVALUATION - {len(test_data)} queries")
    print("="*80)
    print(f"Approach: MAGIC + Smart Schema Linking + Execution-Guided Retry")
    print(f"Model: {MODEL_NAME}")
    print(f"Temperature: 0.3 (MAGIC baseline)")
    print(f"Max retries: {max_retries} (up to {1 + max_retries} attempts per query)")
    print(f"Schema: Top-{top_k_detailed} tables detailed, rest summary")
    print(f"Guidelines: Full MAGIC guideline")
    print("="*80)
    print()

    # Initialize Smart MAGIC with Retry
    print("Initializing Smart MAGIC + Retry...")
    smart_retry = SmartMAGICWithRetry(max_retries=max_retries, verbose=False)
    print("✓ Smart MAGIC + Retry initialized\n")

    # Results tracking
    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "approach": "MAGIC + Smart Schema Linking + Execution-Guided Retry",
            "model": MODEL_NAME,
            "temperature": 0.3,
            "max_retries": max_retries,
            "top_k_detailed": top_k_detailed,
            "test_file": test_file,
            "total_queries": len(test_data),
        },
        "queries": [],
        "summary": {
            "correct": 0,
            "total": 0,
            "accuracy": 0.0,
            "execution_errors": 0,
            "retries_used": 0,
            "first_attempt_correct": 0,
            "fixed_by_retry": 0,
            "by_difficulty": {},
            "by_category": {},
        }
    }

    # Process each query
    for idx, query_data in enumerate(test_data, 1):
        question = query_data["question"]
        ground_truth = query_data["ground_truth_sql"]
        difficulty = query_data.get("difficulty", "unknown")
        category = query_data.get("category", "unknown")

        if verbose:
            print(f"\n{'='*80}")
            print(f"Query {idx}/{len(test_data)} [{difficulty}] [{category}]")
            print(f"{'='*80}")
            print(f"Question: {question}")

        # Generate SQL with Smart MAGIC + Retry
        try:
            result = smart_retry.generate_with_retry(
                question,
                top_k_detailed=top_k_detailed
            )

            predicted_sql = result["sql"]
            num_attempts = result["num_attempts"]
            execution_success = result["success"]

            if verbose:
                print(f"\nFinal SQL (attempt {num_attempts}):")
                print(predicted_sql)
                print(f"\nRanked tables: {result['ranked_tables']}")
                print(f"Attempts: {num_attempts}")

            # Check correctness against ground truth
            is_correct = is_correct_sql(predicted_sql, ground_truth, str(DB_PATH))

            # Track retry statistics
            if num_attempts > 1:
                results["summary"]["retries_used"] += 1

            # Check if first attempt was correct (for ablation)
            first_attempt_sql = result["attempts"][0]["sql"]
            first_attempt_correct = is_correct_sql(first_attempt_sql, ground_truth, str(DB_PATH))

            if first_attempt_correct:
                results["summary"]["first_attempt_correct"] += 1

            # Check if retry fixed an initially broken query
            if not first_attempt_correct and is_correct:
                results["summary"]["fixed_by_retry"] += 1

            if verbose:
                if is_correct:
                    print(f"\n✓ CORRECT")
                    if num_attempts > 1:
                        print(f"  (Fixed by retry on attempt {num_attempts})")
                else:
                    print(f"\n✗ INCORRECT")
                    if not execution_success:
                        last_error = result["attempts"][-1]["execution_error"]
                        print(f"  Execution error (all attempts failed): {last_error}")
                    else:
                        print(f"  Query executes but produces different results")

            # Update results
            results["queries"].append({
                "id": query_data["id"],
                "question": question,
                "difficulty": difficulty,
                "category": category,
                "predicted_sql": predicted_sql,
                "ground_truth_sql": ground_truth,
                "is_correct": is_correct,
                "execution_success": execution_success,
                "num_attempts": num_attempts,
                "first_attempt_correct": first_attempt_correct,
                "fixed_by_retry": not first_attempt_correct and is_correct,
                "all_attempts": result["attempts"],
                "ranked_tables": result["ranked_tables"],
            })

            if is_correct:
                results["summary"]["correct"] += 1
            if not execution_success:
                results["summary"]["execution_errors"] += 1

            results["summary"]["total"] += 1

            # Track by difficulty
            if difficulty not in results["summary"]["by_difficulty"]:
                results["summary"]["by_difficulty"][difficulty] = {"correct": 0, "total": 0}
            results["summary"]["by_difficulty"][difficulty]["total"] += 1
            if is_correct:
                results["summary"]["by_difficulty"][difficulty]["correct"] += 1

            # Track by category
            if category not in results["summary"]["by_category"]:
                results["summary"]["by_category"][category] = {"correct": 0, "total": 0}
            results["summary"]["by_category"][category]["total"] += 1
            if is_correct:
                results["summary"]["by_category"][category]["correct"] += 1

        except Exception as e:
            if verbose:
                print(f"\n✗ ERROR: {str(e)}")

            results["queries"].append({
                "id": query_data["id"],
                "question": question,
                "difficulty": difficulty,
                "category": category,
                "predicted_sql": None,
                "ground_truth_sql": ground_truth,
                "is_correct": False,
                "execution_success": False,
                "num_attempts": 0,
                "first_attempt_correct": False,
                "fixed_by_retry": False,
                "all_attempts": [],
                "ranked_tables": None,
                "error": str(e),
            })

            results["summary"]["total"] += 1
            results["summary"]["execution_errors"] += 1

    # Calculate final accuracy
    if results["summary"]["total"] > 0:
        results["summary"]["accuracy"] = (
            results["summary"]["correct"] / results["summary"]["total"] * 100
        )

    # Calculate accuracy by difficulty
    for difficulty, stats in results["summary"]["by_difficulty"].items():
        if stats["total"] > 0:
            stats["accuracy"] = stats["correct"] / stats["total"] * 100

    # Calculate accuracy by category
    for category, stats in results["summary"]["by_category"].items():
        if stats["total"] > 0:
            stats["accuracy"] = stats["correct"] / stats["total"] * 100

    # Print final summary
    print(f"\n\n{'='*80}")
    print("EVALUATION SUMMARY")
    print(f"{'='*80}")
    print(f"\nOverall Accuracy: {results['summary']['correct']}/{results['summary']['total']} ({results['summary']['accuracy']:.1f}%)")
    print(f"Execution Errors: {results['summary']['execution_errors']}")
    print(f"\nRetry Statistics:")
    print(f"  Queries using retry: {results['summary']['retries_used']}/{results['summary']['total']}")
    print(f"  First attempt correct: {results['summary']['first_attempt_correct']}")
    print(f"  Fixed by retry: {results['summary']['fixed_by_retry']}")

    print(f"\nBy Difficulty:")
    for difficulty, stats in sorted(results["summary"]["by_difficulty"].items()):
        print(f"  {difficulty}: {stats['correct']}/{stats['total']} ({stats['accuracy']:.1f}%)")

    print(f"\nBy Category:")
    for category, stats in sorted(results["summary"]["by_category"].items()):
        print(f"  {category}: {stats['correct']}/{stats['total']} ({stats['accuracy']:.1f}%)")

    # Comparison (Ablation Study)
    print(f"\n{'='*80}")
    print("ABLATION STUDY - PROGRESSION")
    print(f"{'='*80}")
    print(f"FinSQL:                   10/21 (47.6%)")
    print(f"MAGIC:                    11/21 (52.4%)")
    print(f"Enhanced MAGIC:           10/21 (47.6%) [schema linking + voting hurt]")
    print(f"Smart MAGIC:              11/21 (52.4%) [smart schema restored]")
    print(f"Smart MAGIC + Retry:      {results['summary']['correct']}/21 ({results['summary']['accuracy']:.1f}%)")

    improvement_over_smart = results['summary']['accuracy'] - 52.4
    improvement_over_magic = results['summary']['accuracy'] - 52.4

    print(f"\nImprovement over Smart MAGIC: {improvement_over_smart:+.1f} pp")
    print(f"Improvement over MAGIC baseline: {improvement_over_magic:+.1f} pp")

    if results['summary']['fixed_by_retry'] > 0:
        print(f"\n✓ Retry mechanism fixed {results['summary']['fixed_by_retry']} queries!")

    print(f"{'='*80}\n")

    # Save results
    if save_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = project_root / "data" / "results" / "smart_magic_retry"
        results_dir.mkdir(parents=True, exist_ok=True)

        output_file = results_dir / f"evaluation_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to: {output_file}\n")

    return results


if __name__ == "__main__":
    # Run full evaluation
    results = evaluate_smart_magic_retry(
        verbose=True,
        save_results=True,
        max_retries=2,
        top_k_detailed=3,
    )
