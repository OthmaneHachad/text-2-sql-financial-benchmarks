"""Helper utilities"""
import re
from typing import Optional

def extract_sql(text: str) -> str:
    """Extract SQL query from LLM response"""
    # Try to find SQL in code blocks
    sql_pattern = r"```sql\s*(.*?)\s*```"
    match = re.search(sql_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try generic code blocks
    code_pattern = r"```\s*(.*?)\s*```"
    match = re.search(code_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Return the text as-is if no code blocks found
    return text.strip()

def save_guideline(guideline: str, filepath: str):
    """Save guideline to file"""
    with open(filepath, 'w') as f:
        f.write(guideline)

def load_guideline(filepath: str) -> str:
    """Load guideline from file"""
    with open(filepath, 'r') as f:
        return f.read()

class CostTracker:
    """Track API usage costs"""
    def __init__(self, model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"):
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        self.pricing = {
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": {"input": 0.18, "output": 0.18},
            "Qwen/Qwen2.5-32B-Instruct": {"input": 0.40, "output": 0.40},
        }

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def get_cost(self) -> float:
        """Calculate total cost"""
        p = self.pricing.get(self.model, {"input": 0.18, "output": 0.18})
        cost = (self.total_input_tokens / 1_000_000 * p["input"]) + \
               (self.total_output_tokens / 1_000_000 * p["output"])
        return cost

    def report(self):
        """Print cost report"""
        total = self.total_input_tokens + self.total_output_tokens
        print(f"\n{'='*60}")
        print(f"Cost Report ({self.model})")
        print(f"{'='*60}")
        print(f"Total tokens:  {total:,}")
        print(f"Input tokens:  {self.total_input_tokens:,}")
        print(f"Output tokens: {self.total_output_tokens:,}")
        print(f"Estimated cost: ${self.get_cost():.4f}")
        print(f"{'='*60}\n")
