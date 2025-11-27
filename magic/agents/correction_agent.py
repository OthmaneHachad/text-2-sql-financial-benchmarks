import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from together import Together
from magic.config import TEMPERATURE, MAX_TOKENS
from shared.config import TOGETHER_API_KEY, CURRENT_MODEL
from shared.helpers import extract_sql

class CorrectionAgent:
    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.model = CURRENT_MODEL

    def correct_sql(self, question: str, schema: str,
                   incorrect_sql: str, feedback: str):
        """Use feedback to correct the SQL

        Args:
            question: Natural language question
            schema: Database schema
            incorrect_sql: The incorrect SQL to fix
            feedback: Expert feedback on the mistakes
        """

        # System role (as per paper Figure 10)
        system_prompt = """Your task is to correct the predicted SQL based on the provided feedback by expert human.

1. Input Information: You will receive a question, a database schema, a predicted SQL query, and a human feedback.

2. SQL format in your response:
- You must ensure that your response contains a valid SQL.
- The format of SQL in your response must be in the following format: ```sql SQL ```."""

        # User prompt (as per paper Figure 10)
        user_prompt = f"""- Schema Overview: {schema}
- Question: {question}
- Predicted SQL: ```sql {incorrect_sql} ```
- Expert Human Feedback: {feedback}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE["correction"],
            max_tokens=MAX_TOKENS["correction"]
        )

        sql = extract_sql(response.choices[0].message.content)
        usage = response.usage

        return sql, usage.prompt_tokens, usage.completion_tokens