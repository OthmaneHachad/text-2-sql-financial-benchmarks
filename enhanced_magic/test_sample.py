"""
Test Enhanced MAGIC on sample queries

Quick validation before full evaluation
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.enhanced_inference import EnhancedMAGIC
from shared.database import execute_sql
from enhanced_magic.config import DB_PATH


def test_samples():
    """Test Enhanced MAGIC on sample queries"""

    # Test cases with expected behavior
    test_cases = [
        {
            "id": 1,
            "question": "List all available sectors in the GFS data",
            "expected_elements": ["sectors", "sector_name", "ORDER BY"],
            "description": "Simple query - MAGIC fixed this (added ORDER BY)"
        },
        {
            "id": 6,
            "question": "How many observations have 'Percent of GDP' as the transformation?",
            "expected_elements": ["gfs_observations", "transformation", "COUNT"],
            "description": "FinSQL hallucinated 'observations' table - schema linking should fix"
        },
        {
            "id": 12,
            "question": "List the top 5 countries by number of GEM observations",
            "expected_elements": ["gem_observations", "countries", "country_name", "LIMIT 5"],
            "description": "MAGIC fixed this (JOIN with countries table)"
        },
    ]

    print("="*80)
    print("ENHANCED MAGIC - SAMPLE TEST")
    print("="*80)

    # Initialize Enhanced MAGIC (use config defaults)
    print("\nInitializing Enhanced MAGIC...")
    enhanced = EnhancedMAGIC(
        num_samples=None,  # Use config default
        use_full_guideline=False,  # Use filtered guidelines from config
        verbose=True
    )

    results = []

    for test_case in test_cases:
        print(f"\n{'='*80}")
        print(f"TEST CASE #{test_case['id']}: {test_case['description']}")
        print(f"{'='*80}")
        print(f"Question: {test_case['question']}")

        # Generate SQL
        result = enhanced.generate(
            question=test_case['question'],
            return_candidates=True
        )

        final_sql = result['sql']

        # Check expected elements
        print(f"\n--- Generated SQL ---")
        print(final_sql)

        print(f"\n--- Validation ---")
        all_present = True
        for element in test_case['expected_elements']:
            present = element.lower() in final_sql.lower()
            status = "✓" if present else "✗"
            print(f"  {status} Contains '{element}': {present}")
            if not present:
                all_present = False

        # Try to execute
        print(f"\n--- Execution Test ---")
        try:
            exec_result = execute_sql(final_sql, str(DB_PATH))
            if exec_result is not None:
                print(f"  ✓ Executes successfully")
                print(f"  Result rows: {len(exec_result)}")
            else:
                print(f"  ✗ Execution returned None")
                all_present = False
        except Exception as e:
            print(f"  ✗ Execution failed: {str(e)}")
            all_present = False

        # Summary
        print(f"\n--- Summary ---")
        print(f"  Linked tables: {result['linked_tables']}")
        print(f"  Candidates: {result['num_candidates']}")
        print(f"  Unique candidates: {result['num_unique_candidates']}")
        print(f"  Vote count: {result['vote_count']}/{result['num_candidates']}")
        print(f"  Overall: {'✓ PASS' if all_present else '✗ FAIL'}")

        results.append({
            'test_case': test_case,
            'result': result,
            'passed': all_present
        })

    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")

    for r in results:
        status = "✓" if r['passed'] else "✗"
        print(f"  {status} Test #{r['test_case']['id']}: {r['test_case']['description']}")

    return results


if __name__ == "__main__":
    test_samples()
