from .simple_text2sql import BaselineText2SQL
from ..utils.database import format_schema, is_correct_sql
from ..utils.data_loader import load_queries
from ..config import DB_PATH

def test_baseline():
    """Test baseline on sample queries"""
    
    generator = BaselineText2SQL()
    schema = format_schema(DB_PATH)
    queries = load_queries("../data/test/queries.json")[:10]
    
    correct = 0
    for query in queries:
        sql, _, _ = generator.generate_sql(query['question'], schema)
        
        if is_correct_sql(sql, query['ground_truth_sql'], DB_PATH):
            correct += 1
            print(f"✓ Query {query['id']}: CORRECT")
        else:
            print(f"✗ Query {query['id']}: INCORRECT")
    
    print(f"\nAccuracy: {correct}/{len(queries)} = {correct/len(queries)*100:.1f}%")

if __name__ == "__main__":
    test_baseline()