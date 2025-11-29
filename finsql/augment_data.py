"""
Run data augmentation on all training queries
Creates augmented datasets for LoRA fine-tuning
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_loader import load_queries
from shared.config import TRAIN_DATA_PATH
from finsql.modules.data_augmenter import DataAugmenter


def main():
    """Run full data augmentation"""

    print("\n" + "="*80)
    print("FINSQL DATA AUGMENTATION")
    print("="*80 + "\n")

    # Load training data
    print(f"Loading training data from: {TRAIN_DATA_PATH}")
    queries = load_queries(str(TRAIN_DATA_PATH))
    print(f"✓ Loaded {len(queries)} training queries\n")

    # Create augmenter
    augmenter = DataAugmenter()

    # Run all augmentations
    results = augmenter.augment_all(queries, save=True)

    print("\n" + "="*80)
    print("AUGMENTATION SUMMARY")
    print("="*80)
    print(f"\nTotal training queries: {len(queries)}")
    print(f"Total augmented examples: {sum(len(data) for data in results.values())}")
    print(f"\nBreakdown by type:")
    for aug_type, data in results.items():
        print(f"  {aug_type:12s}: {len(data):3d} examples")

    print(f"\n✓ All augmented data saved to: data/finsql/augmented/")
    print(f"\nReady for Phase 3: LoRA Training!")


if __name__ == "__main__":
    main()
