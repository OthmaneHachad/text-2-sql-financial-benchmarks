"""Database execution utilities"""
import sqlite3
from typing import Dict, Any

def execute_sql(sql: str, db_path: str) -> Dict[str, Any]:
    """Execute SQL and return results or error"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return {"success": True, "results": results, "error": None}
    except Exception as e:
        return {"success": False, "results": None, "error": str(e)}

def is_correct_sql(predicted_sql: str, ground_truth_sql: str, db_path: str) -> bool:
    """Check if predicted SQL produces same results as ground truth"""
    pred_result = execute_sql(predicted_sql, db_path)
    gt_result = execute_sql(ground_truth_sql, db_path)
    
    if not pred_result["success"] or not gt_result["success"]:
        return False
    
    return pred_result["results"] == gt_result["results"]

def format_schema(db_path: str) -> str:
    """Extract and format database schema for prompts"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    schema_text = []
    for (table_name,) in tables:
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        schema_text.append(f"Table: {table_name}")
        schema_text.append("Columns:")
        for col in columns:
            col_name, col_type = col[1], col[2]
            schema_text.append(f"  - {col_name} ({col_type})")
        schema_text.append("")
    
    conn.close()
    return "\n".join(schema_text)
