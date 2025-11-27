"""
Minimal test of MAGIC implementation
Tests on 2 simple queries to verify the pipeline works
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from magic.train_magic import train_magic

if __name__ == "__main__":
    print("="*80)
    print("MINIMAL MAGIC TEST - 2 Queries")
    print("="*80)

    # Run on just 2 queries
    guideline = train_magic(max_queries=2)

    print("\n" + "="*80)
    print("TEST COMPLETE!")
    print("="*80)
    print("\nGenerated Guideline Preview (first 500 chars):")
    print(guideline[:500] if guideline else "No guideline generated")
