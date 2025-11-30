"""Check if TOGETHER_API_KEY is accessible"""
import os
import sys

print("Python executable:", sys.executable)
print("TOGETHER_API_KEY in os.environ:", "TOGETHER_API_KEY" in os.environ)
print("os.environ.get('TOGETHER_API_KEY'):", os.environ.get("TOGETHER_API_KEY", "NOT FOUND"))
print("os.getenv('TOGETHER_API_KEY'):", os.getenv("TOGETHER_API_KEY", "NOT FOUND"))

# Try to import config
sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))
from enhanced_magic.config import get_api_key

print("get_api_key():", get_api_key() or "NOT FOUND")

if get_api_key():
    print("\n✓ API key is accessible")
else:
    print("\n✗ API key is NOT accessible")
    print("\nPlease run:")
    print("  export TOGETHER_API_KEY='your-api-key-here'")
    print("\nOr add it to your .env file or shell profile")
