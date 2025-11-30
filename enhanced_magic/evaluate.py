"""
Enhanced MAGIC Evaluation on Full Test Set

Evaluates Enhanced MAGIC on all 21 test queries and compares with MAGIC/FinSQL baselines.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.enhanced_inference import EnhancedMAGIC
from enhanced_magic.config import DB_PATH, EVAL_CONFIG, MODEL_NAME, INFERENCE_CONFIG
from shared.database import is_correct_sql, execute_sql


def evaluate_enhanced_magic(
    test_file: str = None,
    max_queries: int = None,
    verbose: bool = True,
    save_results: bool = True,
) -> Dict[str, Any]:
    """
    Evaluate Enhanced MAGIC on test set

    Args:
        test_file: Path to test queries JSON
        max_queries: Limit number of queries (None = all)
        verbose: Print detailed results
        save_results: Save results to JSON file

    Returns:
        Dict with evaluation results
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
    print(f"ENHANCED MAGIC EVALUATION - {len(test_data)} queries")
    print("="*80)
    print(f"Model: {MODEL_NAME}")
    print(f"Samples per query: {INFERENCE_CONFIG['num_samples']}")
    print(f"Temperature: {INFERENCE_CONFIG['temperature']}")
    print(f"Database: {DB_PATH}")
    print("="*80)
    print()

    # Initialize Enhanced MAGIC
    print("Initializing Enhanced MAGIC...")
    enhanced = EnhancedMAGIC(
        num_samples=INFERENCE_CONFIG["num_samples"],
        use_full_guideline=False,  # Use filtered guidelines
        verbose=False,  # Don't show per-query verbose output
    )
    print("✓ Enhanced MAGIC initialized\n")

    # Results tracking
    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": MODEL_NAME,
            "num_samples": INFERENCE_CONFIG["num_samples"],
            "temperature": INFERENCE_CONFIG["temperature"],
            "test_file": test_file,
            "total_queries": len(test_data),
        },
        "queries": [],
        "summary": {
            "correct": 0,
            "total": 0,
            "accuracy": 0.0,
            "execution_errors": 0,
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

        # Generate SQL with Enhanced MAGIC
        try:
            result = enhanced.generate(
                question=question,
                return_candidates=EVAL_CONFIG["save_candidates"]
            )

            predicted_sql = result["sql"]

            if verbose:
                print(f"\nGenerated SQL:")
                print(predicted_sql)
                print(f"\nLinked tables: {result['linked_tables']}")
                print(f"Candidates: {result['num_candidates']}, Unique: {result['num_unique_candidates']}, Votes: {result['vote_count']}")

            # Check correctness
            is_correct = is_correct_sql(predicted_sql, ground_truth, str(DB_PATH))

            # Try to execute to check for errors
            exec_result = execute_sql(predicted_sql, str(DB_PATH))
            execution_success = exec_result["success"]
            execution_error = exec_result.get("error")

            if verbose:
                if is_correct:
                    print(f"\n✓ CORRECT")
                else:
                    print(f"\n✗ INCORRECT")
                    if not execution_success:
                        print(f"  Execution error: {execution_error}")
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
                "execution_error": execution_error,
                "linked_tables": result["linked_tables"],
                "num_candidates": result["num_candidates"],
                "num_unique_candidates": result["num_unique_candidates"],
                "vote_count": result["vote_count"],
                "candidates": result.get("candidates", []) if EVAL_CONFIG["save_candidates"] else None,
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
                "execution_error": str(e),
                "linked_tables": None,
                "num_candidates": 0,
                "num_unique_candidates": 0,
                "vote_count": 0,
                "candidates": None,
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

    print(f"\nBy Difficulty:")
    for difficulty, stats in sorted(results["summary"]["by_difficulty"].items()):
        print(f"  {difficulty}: {stats['correct']}/{stats['total']} ({stats['accuracy']:.1f}%)")

    print(f"\nBy Category:")
    for category, stats in sorted(results["summary"]["by_category"].items()):
        print(f"  {category}: {stats['correct']}/{stats['total']} ({stats['accuracy']:.1f}%)")

    print(f"\n{'='*80}\n")

    # Save results
    if save_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = project_root / "data" / "results" / "enhanced_magic"
        results_dir.mkdir(parents=True, exist_ok=True)

        output_file = results_dir / f"evaluation_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to: {output_file}")

        # Also save a summary markdown
        summary_file = results_dir / f"summary_{timestamp}.md"
        with open(summary_file, 'w') as f:
            f.write(f"# Enhanced MAGIC Evaluation Results\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Model:** {MODEL_NAME}\n\n")
            f.write(f"**Configuration:**\n")
            f.write(f"- Samples per query: {INFERENCE_CONFIG['num_samples']}\n")
            f.write(f"- Temperature: {INFERENCE_CONFIG['temperature']}\n")
            f.write(f"- Schema linking: Enabled (top-5 tables)\n")
            f.write(f"- Guideline filtering: Enabled (max 3 patterns)\n\n")
            f.write(f"## Overall Results\n\n")
            f.write(f"- **Accuracy:** {results['summary']['correct']}/{results['summary']['total']} ({results['summary']['accuracy']:.1f}%)\n")
            f.write(f"- **Execution Errors:** {results['summary']['execution_errors']}\n\n")
            f.write(f"## By Difficulty\n\n")
            for difficulty, stats in sorted(results["summary"]["by_difficulty"].items()):
                f.write(f"- **{difficulty}:** {stats['correct']}/{stats['total']} ({stats['accuracy']:.1f}%)\n")
            f.write(f"\n## By Category\n\n")
            for category, stats in sorted(results["summary"]["by_category"].items()):
                f.write(f"- **{category}:** {stats['correct']}/{stats['total']} ({stats['accuracy']:.1f}%)\n")
            f.write(f"\n## Comparison with Baselines\n\n")
            f.write(f"| Method | Accuracy |\n")
            f.write(f"|--------|----------|\n")
            f.write(f"| FinSQL | 47.6% |\n")
            f.write(f"| MAGIC | 52.4% |\n")
            f.write(f"| Enhanced MAGIC | {results['summary']['accuracy']:.1f}% |\n")
            f.write(f"\n**Improvement over MAGIC:** {results['summary']['accuracy'] - 52.4:+.1f} pp\n")
            f.write(f"\n**Improvement over FinSQL:** {results['summary']['accuracy'] - 47.6:+.1f} pp\n")

        print(f"Summary saved to: {summary_file}\n")

    return results


if __name__ == "__main__":
    # Run full evaluation
    results = evaluate_enhanced_magic(
        verbose=EVAL_CONFIG["verbose"],
        save_results=EVAL_CONFIG["save_results"],
    )
