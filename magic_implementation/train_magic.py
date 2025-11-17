from agents.manager_agent import ManagerAgent
from agents.feedback_agent import FeedbackAgent
from agents.correction_agent import CorrectionAgent
from baseline.simple_text2sql import BaselineText2SQL
from utils.database import format_schema, is_correct_sql
from utils.data_loader import load_queries
from utils.helpers import CostTracker, save_guideline
from config import DB_PATH, MAX_ITERATIONS

def train_magic(train_file: str = "../data/train/queries.json"):
    """Main MAGIC training loop"""
    
    # Initialize components
    manager = ManagerAgent()
    feedback_agent = FeedbackAgent()
    correction_agent = CorrectionAgent()
    baseline = BaselineText2SQL()
    cost_tracker = CostTracker()
    
    # Load data
    schema = format_schema(DB_PATH)
    train_data = load_queries(train_file)
    
    print(f"Training MAGIC on {len(train_data)} queries...")
    print("=" * 80)
    
    successful_feedbacks = []
    
    for idx, query in enumerate(train_data):
        print(f"\n[{idx+1}/{len(train_data)}] {query['question'][:60]}...")
        
        # Generate initial SQL
        predicted_sql, in_tok, out_tok = baseline.generate_sql(query['question'], schema)
        cost_tracker.add_usage(in_tok, out_tok)
        
        # Check if correct
        if is_correct_sql(predicted_sql, query['ground_truth_sql'], DB_PATH):
            print("  ✓ Already correct, skipping")
            continue
        
        print("  ✗ Incorrect, starting correction...")
        
        # Correction loop
        for iteration in range(MAX_ITERATIONS):
            # Feedback
            feedback, in_tok, out_tok = feedback_agent.generate_feedback(
                query['question'], schema, predicted_sql, query['ground_truth_sql']
            )
            cost_tracker.add_usage(in_tok, out_tok)
            
            # Correction
            corrected_sql, in_tok, out_tok = correction_agent.correct_sql(
                query['question'], schema, predicted_sql, feedback
            )
            cost_tracker.add_usage(in_tok, out_tok)
            
            # Check success
            if is_correct_sql(corrected_sql, query['ground_truth_sql'], DB_PATH):
                print(f"  ✓ Corrected at iteration {iteration+1}")
                
                # Store successful feedback
                successful_feedbacks.append({
                    'question': query['question'],
                    'incorrect_sql': predicted_sql,
                    'corrected_sql': corrected_sql,
                    'feedback': feedback
                })
                
                # Compile guideline every BATCH_SIZE feedbacks
                if len(successful_feedbacks) % manager.batch_size == 0:
                    batch_num = len(successful_feedbacks) // manager.batch_size
                    print(f"\n*** Compiling guideline (batch {batch_num}) ***")
                    
                    guideline, in_tok, out_tok = manager.compile_guideline(
                        successful_feedbacks[-manager.batch_size:]
                    )
                    cost_tracker.add_usage(in_tok, out_tok)
                    
                    # Save intermediate
                    save_guideline(guideline, f"../data/guideline_batch_{batch_num}.txt")
                
                break
            else:
                print(f"  ✗ Failed at iteration {iteration+1}")
        
        # Progress report every 10 queries
        if (idx + 1) % 10 == 0:
            cost_tracker.report()
    
    # Final guideline
    if len(successful_feedbacks) % manager.batch_size != 0:
        print("\n*** Compiling final guideline ***")
        guideline, in_tok, out_tok = manager.compile_guideline(
            successful_feedbacks[-(len(successful_feedbacks) % manager.batch_size):]
        )
        cost_tracker.add_usage(in_tok, out_tok)
    
    # Save final
    save_guideline(manager.current_guideline, "../data/final_guideline.txt")
    
    print("\n" + "=" * 80)
    print("Training Complete!")
    print(f"Successful corrections: {len(successful_feedbacks)}/{len(train_data)}")
    cost_tracker.report()
    
    return manager.current_guideline

if __name__ == "__main__":
    train_magic()