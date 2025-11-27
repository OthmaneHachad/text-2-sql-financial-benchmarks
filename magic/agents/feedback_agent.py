import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from together import Together
from magic.config import TEMPERATURE, MAX_TOKENS
from shared.config import TOGETHER_API_KEY, CURRENT_MODEL

class FeedbackAgent:
    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.model = CURRENT_MODEL

    def generate_feedback(self, question: str, schema: str,
                         incorrect_sql: str, ground_truth_sql: str, evidence: str = None):
        """Analyze mistake and generate feedback

        Args:
            question: Natural language question
            schema: Database schema
            incorrect_sql: The incorrect SQL generated
            ground_truth_sql: The correct SQL
            evidence: Optional evidence/hints for complex questions
        """

        # System role (as per paper Figure 9)
        system_prompt = """Complete the text in chat style like a database manager expert. Write in simple present without using correct SQL. Accept what the user identifies as correct or incorrect."""

        # Build evidence section if provided
        evidence_section = f'\n"evidence": "{evidence}",' if evidence else ""

        # User prompt (as per paper Figure 9)
        user_prompt = f""""question": "{question}",{evidence_section}
"Correct SQL": "{ground_truth_sql}",
"Incorrect SQL": "{incorrect_sql}",

Incorrect SQL mistakes are:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE["feedback"],
            max_tokens=MAX_TOKENS["feedback"]
        )

        feedback = response.choices[0].message.content
        usage = response.usage

        return feedback, usage.prompt_tokens, usage.completion_tokens