from together import Together
from ..config import TOGETHER_API_KEY, CURRENT_MODEL, MAX_TOKENS
from ..utils.helpers import extract_sql

class BaselineText2SQL:
    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.model = CURRENT_MODEL # currentl is Llama 7b
    
    def generate_sql(self, question: str, schema: str) -> str:
        """Generate SQL from natural language question"""
        
        prompt = f"""You are an expert in converting natural language to SQL.

Database Schema:
{schema}

Question: {question}

Generate only the SQL query without explanation.

SQL:"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS["correction"],
            temperature=0.3
        )
        
        sql = extract_sql(response.choices[0].message.content)
        
        # Track usage
        usage = response.usage
        return sql, usage.prompt_tokens, usage.completion_tokens