"""
Guideline-enhanced SQL Generator
Uses learned guidelines during inference
"""
from together import Together
from ..config import TOGETHER_API_KEY, CURRENT_MODEL, MAX_TOKENS
from ..utils.helpers import extract_sql

class GuidelineGenerator:
    """SQL generator that uses MAGIC guidelines"""

    def __init__(self, guideline: str = ""):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.model = CURRENT_MODEL
        self.guideline = guideline

    def set_guideline(self, guideline: str):
        """Update the guideline"""
        self.guideline = guideline

    def generate_sql(self, question: str, schema: str, evidence: str = None):
        """Generate SQL using guideline-enhanced prompt"""

        # Build evidence section if provided
        evidence_section = f"\n- Evidence/Hint: {evidence}" if evidence else ""

        # Enhanced system prompt with guideline
        system_prompt = f"""You are an expert in converting natural language to SQL queries.

IMPORTANT: Before generating SQL, review these common mistakes to avoid:

{self.guideline}

Now generate an accurate SQL query following the guidelines above."""

        # User prompt
        user_prompt = f"""Database Schema:
{schema}

Question: {question}{evidence_section}

Generate only the SQL query in the following format: ```sql YOUR_SQL_HERE ```"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=MAX_TOKENS["correction"],
            temperature=0.3
        )

        sql = extract_sql(response.choices[0].message.content)
        usage = response.usage

        return sql, usage.prompt_tokens, usage.completion_tokens
