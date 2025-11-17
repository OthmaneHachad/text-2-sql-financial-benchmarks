"""Test TogetherAI API connection"""
import os
from dotenv import load_dotenv
from together import Together

load_dotenv()

def test_api():
    """Test basic API connection"""
    api_key = os.getenv("TOGETHER_API_KEY")
    
    if not api_key:
        print("❌ Error: TOGETHER_API_KEY not found in .env file")
        print("Please create a .env file with your API key:")
        print('TOGETHER_API_KEY=your_key_here')
        return False
    
    try:
        client = Together(api_key=api_key)
        
        print("Testing API connection...")
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[{"role": "user", "content": "Say 'API connection successful!'"}],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✅ Response: {result}")
        print(f"✅ Tokens used: {response.usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_api()
