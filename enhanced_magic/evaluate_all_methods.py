"""
Universal Evaluation Script - Test All MAGIC Methods on Any Model

Runs all MAGIC-derived methods and generates concise results
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.database import is_correct_sql, execute_sql


def evaluate_all_methods(model_name: str, test_file: str = None):
    """
    Evaluate all MAGIC-derived methods on a specific model

    Args:
        model_name: TogetherAI model name
        test_file: Path to test queries JSON
    """
    # Use default test file
    if test_file is None:
        test_file = str(project_root / "data" / "test" / "queries.json")

    # Load test data
    with open(test_file, 'r') as f:
        test_data = json.load(f)

    print("="*80)
    print(f"EVALUATING MODEL: {model_name}")
    print(f"Test Queries: {len(test_data)}")
    print("="*80)

    results = {
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(test_data),
        "methods": {}
    }

    # Import methods dynamically to use specified model
    methods_to_test = [
        ("Smart MAGIC", "smart_inference", "SmartMAGIC"),
        ("Smart MAGIC + Guidelines", "smart_inference_guidelines", "SmartMAGICWithGuidelines"),
        ("Smart MAGIC + Retry", "smart_inference_retry", "SmartMAGICWithRetry"),
    ]

    for method_name, module_name, class_name in methods_to_test:
        print(f"\n{'='*80}")
        print(f"Testing: {method_name}")
        print(f"{'='*80}")

        try:
            # Import and patch model
            module = __import__(f"enhanced_magic.{module_name}", fromlist=[class_name])
            method_class = getattr(module, class_name)

            # Create instance
            if "Retry" in class_name:
                method = method_class(max_retries=2, verbose=False)
            else:
                method = method_class(verbose=False)

            # Patch model name
            method.model_name = model_name

            # Evaluate
            correct = 0
            execution_errors = 0
            results_list = []

            for idx, query_data in enumerate(test_data, 1):
                question = query_data["question"]
                ground_truth = query_data["ground_truth_sql"]

                try:
                    # Generate SQL
                    if "Retry" in class_name:
                        result = method.generate_with_retry(question, top_k_detailed=3)
                    else:
                        result = method.generate(question, top_k_detailed=3)

                    predicted_sql = result["sql"]

                    # Check correctness
                    is_correct = is_correct_sql(
                        predicted_sql,
                        ground_truth,
                        str(project_root / "database" / "economic_data.db")
                    )

                    # Check execution
                    exec_result = execute_sql(
                        predicted_sql,
                        str(project_root / "database" / "economic_data.db")
                    )
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

                    # Print progress
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

            results["methods"][method_name] = {
                "correct": correct,
                "total": len(test_data),
                "accuracy": accuracy,
                "execution_errors": execution_errors,
                "results": results_list
            }

            print(f"\n  Result: {correct}/{len(test_data)} ({accuracy:.1f}%)")
            print(f"  Execution errors: {execution_errors}")

        except Exception as e:
            print(f"\n  ERROR: Failed to test {method_name}: {str(e)}")
            results["methods"][method_name] = {
                "error": str(e)
            }

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_safe_name = model_name.replace("/", "_").replace("-", "_")
    results_dir = project_root / "data" / "results" / "model_comparison"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"{model_safe_name}_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}\n")

    return results


def generate_model_report(results: dict) -> str:
    """Generate concise model report"""

    model_name = results["model"]
    report = f"""# Model Evaluation: {model_name}

**Date:** {results["timestamp"][:10]}
**Test Set:** {results["total_queries"]} queries

## Results Summary

| Method | Accuracy | Execution Errors | Notes |
|--------|----------|------------------|-------|
"""

    for method_name, method_results in results["methods"].items():
        if "error" in method_results:
            report += f"| {method_name} | ERROR | - | {method_results['error'][:50]} |\n"
        else:
            acc = method_results["accuracy"]
            correct = method_results["correct"]
            total = method_results["total"]
            errors = method_results["execution_errors"]
            report += f"| {method_name} | {correct}/{total} ({acc:.1f}%) | {errors} | |\n"

    report += "\n## Comparison with Llama 3.1 8B\n\n"
    report += "| Method | Llama 3.1 8B | " + model_name.split("/")[-1] + " | Difference |\n"
    report += "|--------|--------------|" + "-" * len(model_name.split("/")[-1]) + "-|------------|\n"

    baseline = {
        "Smart MAGIC": 52.4,
        "Smart MAGIC + Guidelines": 57.1,
        "Smart MAGIC + Retry": 47.6,
    }

    for method_name, method_results in results["methods"].items():
        if "error" not in method_results and method_name in baseline:
            acc = method_results["accuracy"]
            base_acc = baseline[method_name]
            diff = acc - base_acc
            diff_str = f"{diff:+.1f}pp" if diff != 0 else "0.0pp"
            report += f"| {method_name} | {base_acc:.1f}% | {acc:.1f}% | {diff_str} |\n"

    report += "\n## FinSQL Results\n\n"
    report += "*To be evaluated*\n\n"

    return report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python evaluate_all_methods.py <model_name>")
        print("\nAvailable models:")
        print("  - Qwen/Qwen2.5-7B-Instruct-Turbo")
        print("  - mistralai/Mistral-7B-Instruct-v0.3")
        print("  - NousResearch/Nous-Hermes-2-Yi-34B")
        sys.exit(1)

    model_name = sys.argv[1]

    # Run evaluation
    results = evaluate_all_methods(model_name)

    # Generate report
    report = generate_model_report(results)

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_safe_name = model_name.replace("/", "_").replace("-", "_")
    results_dir = project_root / "data" / "results" / "model_comparison"

    report_file = results_dir / f"{model_safe_name}_report_{timestamp}.md"
    with open(report_file, 'w') as f:
        f.write(report)

    print(report)
    print(f"\nReport saved to: {report_file}")
