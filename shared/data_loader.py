import json
from typing import List, Dict

def load_queries(filepath: str) -> List[Dict]:
    """Load queries from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def split_by_difficulty(queries: List[Dict]) -> Dict[str, List[Dict]]:
    """Split queries by difficulty level"""
    return {
        'simple': [q for q in queries if q['difficulty'] == 'simple'],
        'medium': [q for q in queries if q['difficulty'] == 'medium'],
        'hard': [q for q in queries if q['difficulty'] == 'hard']
    }
