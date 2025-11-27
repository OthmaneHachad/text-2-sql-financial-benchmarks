"""
Shared configuration for all text-to-SQL methods
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
# Get repository root (config.py is in shared/ directory)
REPO_ROOT = Path(__file__).parent.parent
DB_PATH = str(REPO_ROOT / "database/economic_data.db")
TRAIN_DATA_PATH = str(REPO_ROOT / "data/train/queries.json")
TEST_DATA_PATH = str(REPO_ROOT / "data/test/queries.json")
RESULTS_DIR = str(REPO_ROOT / "data/results")

# Model Pricing (per million tokens)
MODEL_PRICING = {
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": {"input": 0.18, "output": 0.18},
    "Qwen/Qwen2.5-7B-Instruct": {"input": 0.20, "output": 0.20},
    "Qwen/Qwen2.5-32B-Instruct": {"input": 0.40, "output": 0.40},
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},
}
