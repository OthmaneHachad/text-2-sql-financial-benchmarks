from together import Together
from ..config import TOGETHER_API_KEY, CURRENT_MODEL, TEMPERATURE, MAX_TOKENS

class FeedbackAgent:
    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.model = CURRENT_MODEL # currently is Llama 7b
    
    def generate_feedback(self, question: str, schema: str, 
                         incorrect_sql: str, ground_truth_sql: str):
        """Analyze mistake and generate feedback"""
        
        prompt = f"""You are an expert SQL analyst. Analyze the incorrect SQL query and provide detailed feedback.

Question: {question}

Database Schema:
{schema}

Incorrect SQL:
{incorrect_sql}

Correct SQL:
{ground_truth_sql}

Analyze the mistakes. Format:

Mistakes:
1. [Category]
   - What went wrong: [explanation]
   - Why incorrect: [reasoning]
   - How to fix: [approach]

Feedback:"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE["feedback"],
            max_tokens=MAX_TOKENS["feedback"]
        )
        
        feedback = response.choices[0].message.content
        usage = response.usage
        
        return feedback, usage.prompt_tokens, usage.completion_tokens