"""
Quick test of MAGIC inference on a few queries
"""
from magic_implementation.infer_magic import run_inference

if __name__ == "__main__":
    print("="*80)
    print("MAGIC INFERENCE TEST - 5 Test Queries")
    print("="*80)

    # Run on just 5 queries to verify the pipeline
    results = run_inference(max_queries=5, verbose=True)

    print("\n" + "="*80)
    print("TEST COMPLETE!")
    print("="*80)
