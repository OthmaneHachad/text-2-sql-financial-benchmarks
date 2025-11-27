import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from together import Together
from magic.config import MAX_TOKENS
from shared.config import TOGETHER_API_KEY, CURRENT_MODEL
from shared.helpers import extract_sql

class BaselineText2SQL:
    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.model = CURRENT_MODEL

    def generate_sql(self, question: str, schema: str, evidence: str = None) -> str:
        """Generate SQL from natural language question

        Args:
            question: Natural language question
            schema: Database schema
            evidence: Optional evidence/hints for the question
        """

        # System prompt for baseline
        system_prompt = """You are an expert in converting natural language to SQL queries.
Generate accurate SQL queries based on the provided schema and question."""

        # Build evidence section if provided
        evidence_section = f"\n- Evidence/Hint: {evidence}" if evidence else ""

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

        # Track usage
        usage = response.usage
        return sql, usage.prompt_tokens, usage.completion_tokens