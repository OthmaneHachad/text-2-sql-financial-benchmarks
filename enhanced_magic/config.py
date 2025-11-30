"""
Enhanced MAGIC Configuration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import shared configuration (same as MAGIC and FinSQL)
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config import TOGETHER_API_KEY, DEVELOPMENT_MODEL

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MAGIC_DIR = DATA_DIR / "magic"
RESULTS_DIR = DATA_DIR / "results" / "enhanced_magic"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = PROJECT_ROOT / "database" / "economic_data.db"

# Test data
TEST_DATA_PATH = DATA_DIR / "test" / "test_queries.json"

# MAGIC guideline
GUIDELINE_PATH = MAGIC_DIR / "final_guideline.txt"

# Model configuration (use shared config)
MODEL_NAME = DEVELOPMENT_MODEL
API_KEY = TOGETHER_API_KEY

# Inference configuration
INFERENCE_CONFIG = {
    "num_samples": 10,          # Number of candidates for self-consistency (increased for consensus)
    "temperature": 0.3,         # Temperature for diversity (lowered for more consensus)
    "max_tokens": 512,          # Max SQL length
    "top_p": 0.9,
}

# Schema linking configuration
SCHEMA_LINKING_CONFIG = {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "top_k_tables": 5,          # Max tables to retrieve
    "top_k_columns": 10,        # Max columns per table
    "similarity_threshold": 0.3,
}

# Output calibration configuration
CALIBRATION_CONFIG = {
    "enable_execution_validation": True,
    "enable_typo_fixing": True,
    "voting_method": "self_consistency",  # or "majority"
}

# Guideline filtering (optional optimization)
GUIDELINE_CONFIG = {
    "use_full_guideline": False,  # Use filtered guidelines for focused patterns
    "max_patterns": 3,            # Max patterns to include if filtering (reduced for clarity)
}

# Evaluation configuration
EVAL_CONFIG = {
    "save_results": True,
    "verbose": True,
    "save_candidates": True,     # Save all candidates for analysis
}
