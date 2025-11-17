from baseline.simple_text2sql import BaselineText2SQL
from utils.database import format_schema, execute_sql, is_correct_sql
from utils.data_loader import load_queries
from utils.helpers import extract_sql, load_guideline, CostTracker
from config import DB_PATH, TOGETHER_API_KEY, CURRENT_MODEL
from together import Together

def self_correct_with_guideline(client, question, schema, initial_sql, 
                                guideline, error=None):
    """Apply self-correction guideline"""
    
    prompt = f"""You are an SQL expert with a self-correction guideline.

Guideline:
{guideline}

Schema:
{schema}

Question: {question}

Initial SQL:
{initial_sql}

{f'Execution Error: {error}' if error else ''}

Following the guideline, review and correct the SQL.

Corrected SQL:"""
    
    response = client.chat.completions.create(
        model=CURRENT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )
    
    sql = extract_sql(response.choices[0].message.content)
    usage = response.usage
    
    return sql, usage.prompt_tokens, usage.completion_tokens

def run_inference(test_file: str = "../data/test/queries.json",
                 guideline_file: str = "../data/final_guideline.txt",
                 scenario: str = "execution_errors"):
    """Run inference with MAGIC guideline
    
    Scenarios:
    - 'incorrect': Correct only incorrect SQLs (oracle available)
    - 'execution_errors': Correct only non-executable SQLs
    - 'all': Apply to all SQLs
    """
    
    client = Together(api_key=TOGETHER_API_KEY)
    baseline = BaselineText2SQL()
    cost_tracker = CostTracker()
    
    schema = format_schema(DB_PATH)
    guideline = load_guideline(guideline_file)
    test_data = load_queries(test_file)
    
    print(f"Running inference on {len(test_data)} queries (scenario: {scenario})")
    print("=" * 80)
    
    results = []
    
    for query in test_data:
        # Generate initial SQL
        initial_sql, in_tok, out_tok = baseline.generate_sql(query['question'], schema)
        cost_tracker.add_usage(in_tok, out_tok)
        
        # Decide whether to apply correction
        exec_result = execute_sql(initial_sql, DB_PATH)
        is_initially_correct = is_correct_sql(initial_sql, query['ground_truth_sql'], DB_PATH)
        
        apply_correction = False
        if scenario == "all":
            apply_correction = True
        elif scenario == "execution_errors" and not exec_result["success"]:
            apply_correction = True
        elif scenario == "incorrect" and not is_initially_correct:
            apply_correction = True
        
        # Apply correction if needed
        if apply_correction:
            corrected_sql, in_tok, out_tok = self_correct_with_guideline(
                client, query['question'], schema, initial_sql,
                guideline, exec_result.get("error")
            )
            cost_tracker.add_usage(in_tok, out_tok)
        else:
            corrected_sql = initial_sql
        
        # Evaluate
        is_correct = is_correct_sql(corrected_sql, query['ground_truth_sql'], DB_PATH)
        
        results.append({
            'id': query['id'],
            'question': query['question'],
            'initial_sql': initial_sql,
            'corrected_sql': corrected_sql,
            'ground_truth_sql': query['ground_truth_sql'],
            'initially_correct': is_initially_correct,
            'finally_correct': is_correct,
            'was_corrected': apply_correction
        })
        
        status = "✓" if is_correct else "✗"
        print(f"{status} Query {query['id']}")
    
    print("\n" + "=" * 80)
    cost_tracker.report()
    
    return results

if __name__ == "__main__":
    results = run_inference(scenario="execution_errors")