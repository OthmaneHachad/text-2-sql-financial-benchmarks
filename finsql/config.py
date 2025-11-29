"""
FinSQL-specific configuration
Extends shared config with LoRA and augmentation parameters
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import shared configuration
from shared.config import *

# ===========================
# LoRA Fine-Tuning Parameters
# ===========================

LORA_CONFIG = {
    "rank": 16,                          # LoRA rank (balance expressiveness/cost)
    "alpha": 32,                         # Scaling factor (typically 2×rank)
    "target_modules": ["q_proj", "v_proj"],  # Attention query/value layers
    "dropout": 0.05,                     # LoRA dropout
    "bias": "none",                      # Don't train bias parameters
    "task_type": "CAUSAL_LM"            # Causal language modeling
}

TRAINING_CONFIG = {
    "learning_rate": 3e-4,               # Learning rate for LoRA training
    "epochs": 10,                        # Training epochs (increased from 6 for Phase 1 fixes)
    "batch_size": 8,                     # Batch size per device (min 8 for TogetherAI)
    "warmup_steps": 10,                  # Learning rate warmup
    "max_seq_length": 2048,              # Maximum sequence length
}

# ===========================
# Data Augmentation Parameters
# ===========================

AUGMENTATION_CONFIG = {
    # Enable/disable augmentation types
    "enable_cot": True,                  # Chain-of-Thought augmentation
    "enable_synonym": True,              # Synonym replacement augmentation
    "enable_skeleton": True,             # SQL skeleton augmentation
    "enable_hard_examples": True,        # Failed MAGIC queries augmentation

    # Augmentation ratios (how many variants per query)
    "cot_ratio": 1,                      # 1 CoT variant per query
    "synonym_ratio": 1,                  # 1 synonym variant per query
    "skeleton_ratio": 1,                 # 1 skeleton variant per query

    # Temperature for augmentation generation
    "augmentation_temperature": 0.7,
    "augmentation_max_tokens": 1000,
}

# Economic domain synonym dictionary
# may need to expand and have dedicated task for determining synonyms.
ECONOMIC_SYNONYMS = {
    # Countries
    "USA": ["United States", "America", "US"],
    "UK": ["United Kingdom", "Britain", "Great Britain"],

    # Economic terms
    "revenue": ["income", "earnings", "receipts"],
    "expenditure": ["spending", "expenses", "outlays"],
    "GDP": ["gross domestic product", "economic output"],
    "growth": ["increase", "expansion", "rise"],
    "deficit": ["shortfall", "gap", "negative balance"],
    "surplus": ["excess", "positive balance"],

    # Time periods
    "year": ["annual", "yearly"],
    "quarter": ["quarterly", "Q1/Q2/Q3/Q4"],

    # General terms
    "total": ["aggregate", "sum", "combined"],
    "average": ["mean", "typical"],
    "show": ["display", "retrieve", "get"],
    "count": ["number of", "total number"],
}

# ===========================
# LoRA Plugin Configuration
# ===========================

PLUGIN_CONFIG = {
    "num_plugins": 4,                    # Number of specialized LoRA adapters
    "plugin_names": [
        "cot_specialist",                # CoT reasoning expert
        "robustness_specialist",         # Synonym/paraphrase expert
        "structure_specialist",          # SQL pattern expert
        "hard_cases_specialist"          # Failed query expert
    ],

    # Weight merging for ensemble
    "merge_weights": {
        "equal": [0.25, 0.25, 0.25, 0.25],           # Equal weighting
        "cot_heavy": [0.4, 0.2, 0.2, 0.2],           # Favor CoT
        "structure_heavy": [0.2, 0.2, 0.4, 0.2],     # Favor structure
        "hard_heavy": [0.2, 0.2, 0.2, 0.4],          # Favor hard cases
    },
    "default_merge_strategy": "equal",
}

# ===========================
# Schema Linking Parameters
# ===========================

SCHEMA_LINKING_CONFIG = {
    "method": "tfidf",                   # 'cross_encoder' or 'tfidf' ('Term Frequency-Inverse Document Frequency')
    "top_k_tables": 3,                   # Max tables to return
    "top_k_columns": 10,                 # Max columns to return
    "similarity_threshold": 0.1,         # Minimum similarity score
}

# ===========================
# Value Retrieval Parameters
# ===========================

VALUE_RETRIEVAL_CONFIG = {
    # MinHash-LSH parameters
    # MinHash (similarity Estimation) Converts text into a compact "signature" that preserves similarity
    # LSH (Locality Sensitive Hashing) Groups similar items into "buckets" so you only search relevant buckets

    "num_perm": 128,                     # Number of permutations for MinHash
    "lsh_threshold": 0.5,                # LSH similarity threshold
    "lsh_num_bands": 16,                 # Number of LSH bands

    # Semantic matching
    "use_semantic_fallback": True,       # Use embeddings if LSH fails
    "semantic_threshold": 0.7,           # Minimum semantic similarity

    # Value index columns (which DB columns to index)
    "indexed_columns": [
        "countries.country_name",
        "indicators.indicator_name",
        "indicators.indicator_code",
        "sectors.sector_name",
    ],
}

# ===========================
# Output Calibration Parameters
# ===========================

CALIBRATION_CONFIG = {
    # Scoring weights
    "syntax_weight": 0.3,                # SQL syntax validity
    "schema_weight": 0.3,                # Schema consistency
    "value_weight": 0.2,                 # Value usage correctness
    "structure_weight": 0.2,             # SQL structural soundness

    # Thresholds
    "min_confidence": 0.5,               # Minimum score to accept SQL
    "high_confidence": 0.8,              # Score for "high confidence"
}

# ===========================
# Inference Strategy Selection
# ===========================

INFERENCE_STRATEGY = "individual_ensemble"  # Options:
                                             # - "merged_only" (Strategy 1)
                                             # - "individual_ensemble" (Strategy 2)
                                             # - "full_ensemble" (Strategy 3)
                                             # - "sequential" (Strategy 4)
                                             # - "adaptive" (Strategy 5)

# ===========================
# File Paths (FinSQL-specific)
# ===========================

FINSQL_DATA_DIR = REPO_ROOT / "data" / "finsql"
FINSQL_RESULTS_DIR = REPO_ROOT / "data" / "results" / "finsql"
PLUGIN_REGISTRY_PATH = REPO_ROOT / "finsql" / "lora" / "plugin_registry.json"

# Augmented data paths
AUGMENTED_DATA_DIR = FINSQL_DATA_DIR / "augmented"
COT_DATA_PATH = AUGMENTED_DATA_DIR / "cot_augmented.json"
SYNONYM_DATA_PATH = AUGMENTED_DATA_DIR / "synonym_augmented.json"
SKELETON_DATA_PATH = AUGMENTED_DATA_DIR / "skeleton_augmented.json"
HARD_DATA_PATH = AUGMENTED_DATA_DIR / "hard_examples.json"

# Value retrieval index
VALUE_INDEX_PATH = FINSQL_DATA_DIR / "value_index.pkl"

# ===========================
# Model Selection for FinSQL
# ===========================

# Base model for LoRA fine-tuning
FINSQL_BASE_MODEL = DEVELOPMENT_MODEL  # Start with 8B, scale to 70B later

# Temperature settings for different tasks
FINSQL_TEMPERATURE = {
    "augmentation": 0.7,                 # Higher for creative augmentation
    "inference": 0.3,                    # Lower for precise SQL generation
    "calibration": 0.1,                  # Very low for scoring
}

FINSQL_MAX_TOKENS = {
    "augmentation": 1000,                # Allow longer CoT reasoning
    "inference": 500,                    # Standard SQL generation
    "calibration": 200,                  # Short scoring explanation
}
