# Data

This directory contains training and test queries for benchmarking.

## Structure
- `train/` - Training queries with ground truth SQL
- `test/` - Test queries for evaluation

## Format
Queries should be in JSON format:
```json
{
    "id": 1,
    "question": "What is the average GDP...",
    "ground_truth_sql": "SELECT AVG(value)...",
    "database": "economic_data.db"
}
```
