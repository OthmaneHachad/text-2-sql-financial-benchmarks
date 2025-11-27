"""
Test Baseline Text-to-SQL Generator

Run evaluation of the baseline generator on test queries.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from magic.baseline.simple_text2sql import BaselineText2SQL
from shared.database import is_correct_sql, execute_sql, format_schema
from shared.data_loader import load_queries
from shared.helpers import CostTracker
from shared.config import DB_PATH


def test_baseline(
    queries: List[Dict],
    db_path: str,
    max_queries: int = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Test baseline generator on a set of queries.
    
    Args:
        queries: List of query dictionaries
        db_path: Path to database
        max_queries: Maximum queries to test (None for all)
        verbose: Print progress
        
    Returns:
        Results dictionary
    """
    cost_tracker = CostTracker()
    
    # Initialize generator
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("Error: TOGETHER_API_KEY not set")
        return None
    
    generator = BaselineText2SQL()
    schema = format_schema(db_path)
    
    # Limit queries if specified
    if max_queries:
        queries = queries[:max_queries]
    
    if verbose:
        print(f"\nTesting {len(queries)} queries...")
        print("=" * 60)
    
    results = []
    correct = 0
    execution_errors = 0
    
    for i, query in enumerate(queries):
        if verbose:
            print(f"\n[{i+1}/{len(queries)}] {query['question'][:60]}...")
        
        try:
            # Generate SQL
            generated_sql, in_tokens, out_tokens = generator.generate_sql(
                query['question'], schema
            )
            cost_tracker.add_usage(in_tokens, out_tokens)
            
            # Check if valid SQL (can be executed)
            exec_result = execute_sql(generated_sql, db_path)
            is_valid = exec_result["success"]
            error = exec_result.get("error")
            
            if not is_valid:
                execution_errors += 1
                is_match = False
                if verbose:
                    print(f"  ✗ Execution error: {error[:50]}...")
            else:
                # Check if correct (same results as ground truth)
                is_match = is_correct_sql(generated_sql, query['ground_truth_sql'], db_path)
            
            if is_match:
                correct += 1
                if verbose:
                    print(f"  ✓ CORRECT")
            elif is_valid:
                if verbose:
                    print(f"  ✗ Wrong results")
            
            results.append({
                'id': query['id'],
                'question': query['question'],
                'ground_truth_sql': query['ground_truth_sql'],
                'generated_sql': generated_sql,
                'is_valid': is_valid,
                'is_correct': is_match,
                'error': error if not is_valid else None,
                'difficulty': query.get('difficulty', 'unknown'),
                'category': query.get('category', 'unknown')
            })
            
        except Exception as e:
            if verbose:
                print(f"  ✗ Exception: {str(e)[:50]}")
            results.append({
                'id': query['id'],
                'question': query['question'],
                'ground_truth_sql': query['ground_truth_sql'],
                'generated_sql': None,
                'is_valid': False,
                'is_correct': False,
                'error': str(e),
                'difficulty': query.get('difficulty', 'unknown'),
                'category': query.get('category', 'unknown')
            })
    
    # Calculate metrics
    total = len(results)
    accuracy = correct / total * 100 if total > 0 else 0
    execution_rate = (total - execution_errors) / total * 100 if total > 0 else 0
    
    # Breakdown by difficulty
    by_difficulty = {}
    for diff in ['simple', 'medium', 'hard']:
        diff_results = [r for r in results if r['difficulty'] == diff]
        if diff_results:
            diff_correct = sum(1 for r in diff_results if r['is_correct'])
            by_difficulty[diff] = {
                'total': len(diff_results),
                'correct': diff_correct,
                'accuracy': diff_correct / len(diff_results) * 100
            }
    
    summary = {
        'total_queries': total,
        'correct': correct,
        'accuracy': accuracy,
        'execution_errors': execution_errors,
        'execution_rate': execution_rate,
        'by_difficulty': by_difficulty,
        'cost': cost_tracker.get_cost(),
        'tokens': {
            'input': cost_tracker.total_input_tokens,
            'output': cost_tracker.total_output_tokens,
            'total': cost_tracker.total_input_tokens + cost_tracker.total_output_tokens
        }
    }
    
    return {
        'summary': summary,
        'results': results
    }


def print_results(results: Dict[str, Any]) -> None:
    """Print formatted test results."""
    summary = results['summary']
    
    print("\n" + "=" * 60)
    print("BASELINE TEST RESULTS")
    print("=" * 60)
    
    print(f"\nOverall Performance:")
    print(f"  Total Queries:     {summary['total_queries']}")
    print(f"  Correct:           {summary['correct']}")
    print(f"  Accuracy:          {summary['accuracy']:.1f}%")
    print(f"  Execution Rate:    {summary['execution_rate']:.1f}%")
    print(f"  Execution Errors:  {summary['execution_errors']}")
    
    if summary['by_difficulty']:
        print(f"\nBy Difficulty:")
        for diff in ['simple', 'medium', 'hard']:
            if diff in summary['by_difficulty']:
                metrics = summary['by_difficulty'][diff]
                print(f"  {diff.capitalize():8s}: {metrics['correct']}/{metrics['total']} = {metrics['accuracy']:.1f}%")
    
    print(f"\nCost:")
    print(f"  Total Tokens: {summary['tokens']['total']:,}")
    print(f"  Total Cost:   ${summary['cost']:.4f}")
    
    print("=" * 60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test baseline Text-to-SQL generator")
    parser.add_argument("--max", type=int, default=None, help="Maximum queries to test")
    parser.add_argument("--output", type=str, default=None, help="Output file for results")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument("--train", action="store_true", help="Test on training set instead of test set")
    
    args = parser.parse_args()
    
    # Determine paths (relative to magic_implementation directory)
    base_dir = Path(__file__).parent.parent.parent
    
    if args.train:
        queries_path = base_dir / "data" / "train" / "queries.json"
    else:
        queries_path = base_dir / "data" / "test" / "queries.json"
    
    db_path = base_dir / "database" / "economic_data.db"
    results_dir = base_dir / "results"
    
    # Check files exist
    if not queries_path.exists():
        print(f"Error: Queries file not found: {queries_path}")
        sys.exit(1)
    
    if not db_path.exists():
        print(f"Error: Database not found: {db_path}")
        sys.exit(1)
    
    # Check API key
    if not os.getenv("TOGETHER_API_KEY"):
        print("Error: TOGETHER_API_KEY environment variable not set")
        print("Set it with: export TOGETHER_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Load queries
    queries = load_queries(str(queries_path))
    
    print(f"Loaded {len(queries)} queries from {queries_path.name}")
    
    # Count by difficulty
    by_diff = {}
    for q in queries:
        d = q.get('difficulty', 'unknown')
        by_diff[d] = by_diff.get(d, 0) + 1
    print(f"Distribution: {by_diff}")
    
    # Run test
    results = test_baseline(
        queries=queries,
        db_path=str(db_path),
        max_queries=args.max,
        verbose=not args.quiet
    )
    
    if results:
        print_results(results)
        
        # Save results
        if args.output:
            output_path = Path(args.output)
        else:
            results_dir.mkdir(parents=True, exist_ok=True)
            output_path = results_dir / "baseline_results.json"
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
