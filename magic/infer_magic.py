"""
MAGIC Inference - Test guideline effectiveness
Compares baseline vs guideline-enhanced SQL generation
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from magic.baseline.simple_text2sql import BaselineText2SQL
from magic.agents.guideline_generator import GuidelineGenerator
from shared.database import format_schema, is_correct_sql
from magic.config import TEST_DATA_PATH, REPO_ROOT, DB_PATH, GUIDELINE_PATH

class MagicInference:
    def __init__(self, guideline_path: str = None):
        """Initialize inference with optional guideline"""
        self.baseline = BaselineText2SQL()

        # Load guideline if provided
        self.guideline = ""
        if guideline_path:
            guideline_file = Path(guideline_path)
            if guideline_file.exists():
                self.guideline = guideline_file.read_text()
                print(f"Loaded guideline from {guideline_path}")
                print(f"Guideline length: {len(self.guideline)} characters\n")
            else:
                print(f"Warning: Guideline file not found at {guideline_path}")

        self.generator = GuidelineGenerator()

    def generate_with_guideline(self, question: str, schema: str, evidence: str = None):
        """Generate SQL with guideline-enhanced prompt"""

        # Build evidence section if provided
        evidence_section = f"\n- Evidence/Hint: {evidence}" if evidence else ""

        # Enhanced system prompt with guideline
        system_prompt = f"""You are an expert in converting natural language to SQL queries.

IMPORTANT: Before generating SQL, review these common mistakes to avoid:

{self.guideline}

Now generate an accurate SQL query following the guidelines above."""

        # User prompt
        user_prompt = f"""Database Schema:
{schema}

Question: {question}{evidence_section}

Generate only the SQL query in the following format: ```sql YOUR_SQL_HERE ```"""

        response = self.baseline.client.chat.completions.create(
            model=self.baseline.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=512,
            temperature=0.3
        )

        from shared.helpers import extract_sql
        sql = extract_sql(response.choices[0].message.content)
        usage = response.usage

        return sql, usage.prompt_tokens, usage.completion_tokens

def run_inference(test_file: str = None, guideline_file: str = None,
                  max_queries: int = None, verbose: bool = True):
    """
    Run inference on test set with and without guideline

    Args:
        test_file: Path to test queries JSON (defaults to TEST_DATA_PATH)
        guideline_file: Path to guideline file (defaults to data/final_guideline.txt)
        max_queries: Limit number of queries to test (None = all)
        verbose: Print detailed results
    """

    # Use defaults if not specified
    if test_file is None:
        test_file = TEST_DATA_PATH
    if guideline_file is None:
        guideline_file = GUIDELINE_PATH

    # Load test data
    with open(test_file, 'r') as f:
        test_data = json.load(f)

    if max_queries:
        test_data = test_data[:max_queries]
        print(f"[TEST MODE] Limited to {max_queries} queries\n")

    # Initialize models
    baseline = BaselineText2SQL()
    magic = MagicInference(guideline_file)

    # Get schema
    schema = format_schema(DB_PATH)

    # Results tracking
    baseline_results = {"correct": 0, "total": 0, "tokens": {"input": 0, "output": 0}}
    magic_results = {"correct": 0, "total": 0, "tokens": {"input": 0, "output": 0}}

    print("="*80)
    print(f"MAGIC INFERENCE EVALUATION - {len(test_data)} queries")
    print("="*80)
    print()

    for idx, query_data in enumerate(test_data, 1):
        question = query_data["question"]
        ground_truth = query_data.get("ground_truth_sql") or query_data.get("sql")
        evidence = query_data.get("evidence")
        category = query_data.get("category", "unknown")

        if verbose:
            print(f"\n{'='*80}")
            print(f"Query {idx}/{len(test_data)} [{category}]")
            print(f"{'='*80}")
            print(f"Question: {question}")
            if evidence:
                print(f"Evidence: {evidence}")

        # Test 1: Baseline (without guideline)
        try:
            baseline_sql, b_input, b_output = baseline.generate_sql(question, schema, evidence)
            baseline_correct = is_correct_sql(baseline_sql, ground_truth, DB_PATH)
            baseline_results["total"] += 1
            baseline_results["tokens"]["input"] += b_input
            baseline_results["tokens"]["output"] += b_output
            if baseline_correct:
                baseline_results["correct"] += 1

            if verbose:
                print(f"\n[BASELINE] {'✓ CORRECT' if baseline_correct else '✗ INCORRECT'}")
                print(f"Generated: {baseline_sql}")
        except Exception as e:
            if verbose:
                print(f"\n[BASELINE] ERROR: {e}")
            baseline_correct = False

        # Test 2: MAGIC (with guideline)
        try:
            magic_sql, m_input, m_output = magic.generate_with_guideline(question, schema, evidence)
            magic_correct = is_correct_sql(magic_sql, ground_truth, DB_PATH)
            magic_results["total"] += 1
            magic_results["tokens"]["input"] += m_input
            magic_results["tokens"]["output"] += m_output
            if magic_correct:
                magic_results["correct"] += 1

            if verbose:
                print(f"\n[MAGIC] {'✓ CORRECT' if magic_correct else '✗ INCORRECT'}")
                print(f"Generated: {magic_sql}")
        except Exception as e:
            if verbose:
                print(f"\n[MAGIC] ERROR: {e}")
            magic_correct = False

        # Show improvement
        if verbose and not baseline_correct and magic_correct:
            print(f"\n🎯 MAGIC IMPROVED THIS QUERY!")
        elif verbose and baseline_correct and not magic_correct:
            print(f"\n⚠️  MAGIC REGRESSION (baseline was correct)")

    # Final summary
    print(f"\n\n{'='*80}")
    print("FINAL RESULTS")
    print(f"{'='*80}")

    baseline_acc = (baseline_results["correct"] / baseline_results["total"] * 100) if baseline_results["total"] > 0 else 0
    magic_acc = (magic_results["correct"] / magic_results["total"] * 100) if magic_results["total"] > 0 else 0
    improvement = magic_acc - baseline_acc

    print(f"\nBaseline (no guideline):")
    print(f"  Accuracy: {baseline_results['correct']}/{baseline_results['total']} ({baseline_acc:.1f}%)")
    print(f"  Tokens: {baseline_results['tokens']['input']:,} input, {baseline_results['tokens']['output']:,} output")

    print(f"\nMAGIC (with guideline):")
    print(f"  Accuracy: {magic_results['correct']}/{magic_results['total']} ({magic_acc:.1f}%)")
    print(f"  Tokens: {magic_results['tokens']['input']:,} input, {magic_results['tokens']['output']:,} output")

    print(f"\nImprovement: {improvement:+.1f} percentage points")

    if improvement > 0:
        print(f"✓ MAGIC guideline improved accuracy!")
    elif improvement < 0:
        print(f"✗ Guideline caused regression (needs refinement)")
    else:
        print(f"= No change in accuracy")

    # Token analysis
    if baseline_results['total'] > 0 and magic_results['total'] > 0:
        avg_baseline_input = baseline_results['tokens']['input'] / baseline_results['total']
        avg_magic_input = magic_results['tokens']['input'] / magic_results['total']
        token_overhead = avg_magic_input - avg_baseline_input
        print(f"\nToken overhead per query: {token_overhead:.0f} tokens (guideline in prompt)")
    else:
        print(f"\n⚠️  Token analysis skipped (insufficient data)")

    print(f"\n{'='*80}\n")

    return {
        "baseline": baseline_results,
        "magic": magic_results,
        "improvement": improvement
    }

if __name__ == "__main__":
    # Run on all test queries
    run_inference()
