"""
MAGIC-specific configuration
"""
from pathlib import Path

# Import shared config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config import *

# MAGIC-specific parameters
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

# MAGIC training parameters
BATCH_SIZE = 10  # Feedback batch size for guideline compilation
MAX_ITERATIONS = 5  # Max correction iterations per query

# MAGIC results directory
MAGIC_RESULTS_DIR = str(REPO_ROOT / "data/results/magic")
GUIDELINE_PATH = str(REPO_ROOT / "data/final_guideline.txt")
