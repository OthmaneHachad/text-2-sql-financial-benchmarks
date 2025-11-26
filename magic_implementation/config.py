"""
Configuration for MAGIC implementation
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Configuration
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Model Selection
DEVELOPMENT_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
BENCHMARK_MODEL = "Qwen/Qwen2.5-32B-Instruct"
CURRENT_MODEL = DEVELOPMENT_MODEL

# Paths - Repository-relative paths (works from any location)
# Get repository root (config.py is in magic_implementation/ directory)
REPO_ROOT = Path(__file__).parent.parent
MAIN_REPO = REPO_ROOT  # Alias for backward compatibility
DB_PATH = str(REPO_ROOT / "database/economic_data.db")
TRAIN_DATA_PATH = str(REPO_ROOT / "data/train/queries.json")
TEST_DATA_PATH = str(REPO_ROOT / "data/test/queries.json")

# Generation Parameters
TEMPERATURE = {
    "feedback": 0.3,
    "correction": 0.3,
    "guideline": 0.7
}

MAX_TOKENS = {
    "feedback": 1000,
    "correction": 500,
    "guideline": 2000
}

# MAGIC Parameters
BATCH_SIZE = 10  # Feedback batch size for guideline compilation
MAX_ITERATIONS = 5  # Max correction iterations per query

# Model Pricing (per million tokens)
MODEL_PRICING = {
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": {"input": 0.18, "output": 0.18},
    "Qwen/Qwen2.5-7B-Instruct": {"input": 0.20, "output": 0.20},
    "Qwen/Qwen2.5-32B-Instruct": {"input": 0.40, "output": 0.40},
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},
}
