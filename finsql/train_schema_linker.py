"""
Train Schema Linker Cross-Encoder Model

Run this script to train the Cross-Encoder for schema linking.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from finsql.modules.schema_linking_trainer import SchemaLinkingTrainer, PROJECT_ROOT, DB_PATH, TRAIN_DATA_PATH


def main():
    print("="*80)
    print("TRAINING SCHEMA LINKER CROSS-ENCODER")
    print("="*80)

    print(f"\nDatabase: {DB_PATH}")
    print(f"Training data: {TRAIN_DATA_PATH}")

    # Check if files exist
    if not DB_PATH.exists():
        print(f"\n✗ Database not found: {DB_PATH}")
        return

    if not TRAIN_DATA_PATH.exists():
        print(f"\n✗ Training data not found: {TRAIN_DATA_PATH}")
        return

    # Initialize trainer
    trainer = SchemaLinkingTrainer(
        db_path=str(DB_PATH),
        train_data_path=str(TRAIN_DATA_PATH)
    )

    print("\n" + "="*80)
    print("Training Configuration:")
    print("="*80)
    print(f"Model: roberta-base")
    print(f"Epochs: 3")
    print(f"Batch size: 16")
    print(f"Output directory: {PROJECT_ROOT / 'finsql' / 'schema_linking' / 'cross_encoder_model'}")

    # Train model
    print("\n" + "="*80)
    model_path = trainer.train_model(
        model_name='roberta-base',
        epochs=3,
        batch_size=16
    )

    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80)
    print(f"✓ Model saved to: {model_path}")
    print("\nNext steps:")
    print("1. Test the model: python finsql/test_schema_linker.py")
    print("2. Integrate with inference pipeline")


if __name__ == "__main__":
    main()
