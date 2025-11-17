from together import Together
from dotenv import load_dotenv
import os

load_dotenv()

client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response)