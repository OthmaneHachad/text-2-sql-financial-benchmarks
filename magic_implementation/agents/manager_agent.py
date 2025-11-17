from together import Together
from ..config import TOGETHER_API_KEY, CURRENT_MODEL, TEMPERATURE, MAX_TOKENS, BATCH_SIZE

class ManagerAgent:
    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.model = CURRENT_MODEL
        self.correction_memory = []
        self.current_guideline = ""
        self.feedback_batch = []
        self.batch_size = BATCH_SIZE
    
    def compile_guideline(self, feedback_batch):
        """Generate or update self-correction guideline"""
        
        # Format feedback batch
        feedback_text = "\n\n".join([
            f"Example {i+1}:\n"
            f"Question: {fb['question']}\n"
            f"Incorrect SQL: {fb['incorrect_sql']}\n"
            f"Corrected SQL: {fb['corrected_sql']}\n"
            f"Feedback: {fb['feedback']}"
            for i, fb in enumerate(feedback_batch)
        ])
        
        if not self.current_guideline:
            # Initial guideline
            prompt = f"""Generate a self-correction guideline for text-to-SQL based on these successful corrections:

{feedback_text}

Create a guideline with:
1. Mistake category name
2. Example question
3. Incorrect SQL
4. Corrected SQL
5. "Ask-to-myself" questions to prevent this mistake

Guideline:"""
        else:
            # Update guideline
            prompt = f"""Update the self-correction guideline with new feedback:

Current Guideline:
{self.current_guideline}

New Successful Feedbacks:
{feedback_text}

Updated Guideline:"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE["guideline"],
            max_tokens=MAX_TOKENS["guideline"]
        )
        
        self.current_guideline = response.choices[0].message.content
        usage = response.usage
        
        return self.current_guideline, usage.prompt_tokens, usage.completion_tokens