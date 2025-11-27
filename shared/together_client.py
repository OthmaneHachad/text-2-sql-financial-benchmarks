"""TogetherAI API client utilities"""
import os
from together import Together
from typing import Dict, Any, Optional

def get_together_client() -> Together:
    """Get TogetherAI client instance"""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise ValueError("TOGETHER_API_KEY not found in environment")
    return Together(api_key=api_key)

def chat_completion(
    client: Together,
    model: str,
    messages: list,
    temperature: float = 0.3,
    max_tokens: int = 500,
    stop: Optional[list] = None
) -> Dict[str, Any]:
    """
    Make a chat completion request to TogetherAI

    Returns:
        Dict with 'content', 'input_tokens', 'output_tokens'
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stop=stop
    )

    return {
        "content": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens
    }
