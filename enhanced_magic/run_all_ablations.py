"""
Run MAGIC Baseline and Enhanced MAGIC Evaluations Across All Models

This script evaluates:
1. MAGIC Baseline (full schema + 11 guidelines, no voting)
2. Enhanced MAGIC (schema linking + top-3 guidelines + voting)

Across all 5 models:
- meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
- meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
- openai/gpt-oss-20b
- mistralai/Mistral-7B-Instruct-v0.3
- Qwen/Qwen2.5-7B-Instruct-Turbo
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.evaluate_magic_baseline import evaluate_magic_baseline
from enhanced_magic.evaluate_enhanced_magic import evaluate_enhanced_magic


# All models to evaluate
MODELS = [
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "openai/gpt-oss-20b",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct-Turbo",
]


def run_all_ablations():
    """Run MAGIC Baseline and Enhanced MAGIC on all models"""

    print("="*80)
    print("ABLATION STUDY: MAGIC Baseline + Enhanced MAGIC")
    print(f"Models: {len(MODELS)}")
    print(f"Methods: 2 (MAGIC Baseline, Enhanced MAGIC)")
    print(f"Total Evaluations: {len(MODELS) * 2} = {len(MODELS) * 2 * 21} queries")
    print("="*80)
    print()

    results_summary = {
        "timestamp": datetime.now().isoformat(),
        "models_evaluated": len(MODELS),
        "methods": ["MAGIC Baseline", "Enhanced MAGIC"],
        "results": {}
    }

    for model_idx, model_name in enumerate(MODELS, 1):
        print(f"\n{'#'*80}")
        print(f"MODEL {model_idx}/{len(MODELS)}: {model_name}")
        print(f"{'#'*80}\n")

        model_results = {}

        # 1. Evaluate MAGIC Baseline
        print(f"\n[1/2] Running MAGIC Baseline...")
        try:
            baseline_result = evaluate_magic_baseline(model_name)
            model_results["MAGIC Baseline"] = {
                "accuracy": baseline_result["accuracy"],
                "correct": baseline_result["correct"],
                "total": baseline_result["total"],
                "execution_errors": baseline_result["execution_errors"],
            }
            print(f"✓ MAGIC Baseline: {baseline_result['correct']}/{baseline_result['total']} ({baseline_result['accuracy']:.1f}%)")
        except Exception as e:
            print(f"✗ MAGIC Baseline FAILED: {str(e)}")
            model_results["MAGIC Baseline"] = {"error": str(e)}

        # 2. Evaluate Enhanced MAGIC
        print(f"\n[2/2] Running Enhanced MAGIC...")
        try:
            enhanced_result = evaluate_enhanced_magic(model_name)
            model_results["Enhanced MAGIC"] = {
                "accuracy": enhanced_result["accuracy"],
                "correct": enhanced_result["correct"],
                "total": enhanced_result["total"],
                "execution_errors": enhanced_result["execution_errors"],
            }
            print(f"✓ Enhanced MAGIC: {enhanced_result['correct']}/{enhanced_result['total']} ({enhanced_result['accuracy']:.1f}%)")
        except Exception as e:
            print(f"✗ Enhanced MAGIC FAILED: {str(e)}")
            model_results["Enhanced MAGIC"] = {"error": str(e)}

        results_summary["results"][model_name] = model_results

        print(f"\n{'-'*80}")
        print(f"MODEL {model_idx} SUMMARY: {model_name}")
        print(f"{'-'*80}")
        if "error" not in model_results["MAGIC Baseline"]:
            print(f"  MAGIC Baseline:   {model_results['MAGIC Baseline']['accuracy']:.1f}% ({model_results['MAGIC Baseline']['correct']}/21)")
        else:
            print(f"  MAGIC Baseline:   ERROR")

        if "error" not in model_results["Enhanced MAGIC"]:
            print(f"  Enhanced MAGIC:   {model_results['Enhanced MAGIC']['accuracy']:.1f}% ({model_results['Enhanced MAGIC']['correct']}/21)")
        else:
            print(f"  Enhanced MAGIC:   ERROR")
        print()

    # Final Summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY: ALL MODELS")
    print(f"{'='*80}\n")

    print(f"{'Model':<50} | {'MAGIC Baseline':<20} | {'Enhanced MAGIC':<20}")
    print(f"{'-'*50}-+-{'-'*20}-+-{'-'*20}")

    for model_name in MODELS:
        model_short = model_name.split("/")[-1][:45]

        baseline = results_summary["results"][model_name]["MAGIC Baseline"]
        enhanced = results_summary["results"][model_name]["Enhanced MAGIC"]

        if "error" not in baseline:
            baseline_str = f"{baseline['correct']}/21 ({baseline['accuracy']:.1f}%)"
        else:
            baseline_str = "ERROR"

        if "error" not in enhanced:
            enhanced_str = f"{enhanced['correct']}/21 ({enhanced['accuracy']:.1f}%)"
        else:
            enhanced_str = "ERROR"

        print(f"{model_short:<50} | {baseline_str:<20} | {enhanced_str:<20}")

    print(f"\n{'='*80}\n")

    # Save summary
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = project_root / "data" / "results" / f"ablation_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(results_summary, f, indent=2)

    print(f"Summary saved to: {summary_file}\n")

    return results_summary


if __name__ == "__main__":
    run_all_ablations()
