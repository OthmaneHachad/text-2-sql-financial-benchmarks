from together import Together
from ..config import TOGETHER_API_KEY, CURRENT_MODEL, TEMPERATURE, MAX_TOKENS
from ..utils.helpers import extract_sql

class CorrectionAgent:
    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.model = CURRENT_MODEL # currently is Llama 7b
    
    def correct_sql(self, question: str, schema: str, 
                   incorrect_sql: str, feedback: str):
        """Use feedback to correct the SQL"""
        
        prompt = f"""You are an expert SQL corrector. Use feedback to correct the SQL.

Schema:
{schema}

Question: {question}

Incorrect SQL:
{incorrect_sql}

Expert Feedback:
{feedback}

Generate the corrected SQL query.

Corrected SQL:"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE["correction"],
            max_tokens=MAX_TOKENS["correction"]
        )
        
        sql = extract_sql(response.choices[0].message.content)
        usage = response.usage
        
        return sql, usage.prompt_tokens, usage.completion_tokens