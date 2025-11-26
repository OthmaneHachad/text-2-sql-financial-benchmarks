# MAGIC Implementation

Implementation of **MAGIC (Multi-Agent Guideline-based Iterative Correction)** for Text-to-SQL generation on the economic database (IMF GFS + World Bank GEM).

Based on the paper: *"MAGIC: Generating Self-Correction Guideline for In-Context Text-to-SQL"* ([arXiv:2406.12692](https://arxiv.org/abs/2406.12692))

## Overview

MAGIC uses a multi-agent system to iteratively improve SQL generation through:
1. **FeedbackAgent**: Analyzes mistakes between incorrect and ground truth SQL
2. **CorrectionAgent**: Uses feedback to correct SQL queries
3. **ManagerAgent**: Compiles successful corrections into reusable guidelines

The system automatically generates a self-correction guideline from training data, which is then used during inference to improve first-attempt accuracy.

## Project Structure

```
magic_implementation/
├── agents/
│   ├── feedback_agent.py          # Analyzes SQL mistakes
│   ├── correction_agent.py        # Corrects SQL based on feedback
│   ├── manager_agent.py           # Compiles correction guidelines
│   └── guideline_generator.py     # Guideline-enhanced SQL generation
├── baseline/
│   └── simple_text2sql.py         # Baseline text-to-SQL generator
├── utils/
│   ├── database.py                # Database execution and validation
│   └── helpers.py                 # Utility functions
├── config.py                      # Configuration and parameters
├── train_magic.py                 # Training pipeline
├── infer_magic.py                 # Inference and evaluation pipeline
├── test_inference.py              # Quick inference test script
└── test_magic_minimal.py          # Minimal training test script
```

## Requirements

### Python Dependencies

```bash
pip install python-dotenv together
```

### API Key Setup

Create a `.env` file in the repository root:

```bash
TOGETHER_API_KEY=your_api_key_here
```

Get a free API key from [Together.ai](https://api.together.ai/)

### Database

Ensure the economic database is available at:
```
database/economic_data.db
```

## Usage

### 1. Training: Generate Guidelines

Train MAGIC on your training queries to generate a self-correction guideline:

```bash
# Full training (70 queries)
python3 -m magic_implementation.train_magic

# Quick test (5 queries)
python3 -m magic_implementation.test_magic_minimal
```

**Training Process:**
- Iteratively corrects SQL queries (max 5 iterations per query)
- Compiles guidelines every 10 successful corrections
- Saves final guideline to `data/final_guideline.txt`
- Tracks token usage and cost

**Expected Output:**
- Guideline file: `data/final_guideline.txt`
- Intermediate batches: `data/guideline_batch_*.txt`
- Console output showing correction progress and costs

### 2. Inference: Evaluate Guidelines

Test the generated guideline on held-out test queries:

```bash
# Full evaluation (21 test queries)
python3 -c "from magic_implementation.infer_magic import run_inference; run_inference()"

# Quick test (5 queries)
python3 -m magic_implementation.test_inference
```

**Inference Process:**
- Compares baseline (no guideline) vs MAGIC (with guideline)
- Shows query-by-query improvements
- Reports accuracy gains and token overhead

**Expected Output:**
- Accuracy comparison: Baseline vs MAGIC
- Token usage analysis
- Query-level results showing improvements

## Configuration

Edit `config.py` to customize:

### Model Selection
```python
DEVELOPMENT_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"  # Fast, cheap
BENCHMARK_MODEL = "Qwen/Qwen2.5-32B-Instruct"                      # Larger Model
CURRENT_MODEL = DEVELOPMENT_MODEL  # Change this to switch models
```

### MAGIC Parameters
```python
BATCH_SIZE = 10         # Feedback batch size for guideline compilation
MAX_ITERATIONS = 5      # Max correction iterations per query
```

### Temperature Settings
```python
TEMPERATURE = {
    "feedback": 0.3,    # Lower = more consistent feedback
    "correction": 0.3,  # Lower = more conservative corrections
    "guideline": 0.7    # Higher = more creative guideline generation
}
```

## Results

Our implementation achieves:

| Metric | Baseline | MAGIC | Improvement |
|--------|----------|-------|-------------|
| **Test Accuracy** | 42.9% (9/21) | 52.4% (11/21) | **+9.5 pp** |
| **Training Success** | - | 61.4% (43/70) | - |
| **Training Cost** | - | $0.0524 | - |

**Key Findings:**
- ✅ Zero regressions (MAGIC never made queries worse)
- ✅ Improved structural patterns (ORDER BY, DISTINCT, joins)
- ✅ Generated actionable self-correction guidelines
- ⚠️ Token overhead: ~2,013 tokens per query (guideline in prompt)

See `data/magic_results_summary.md` for detailed analysis.

## Prompt Engineering

All prompts are aligned with the MAGIC paper specifications:

- **FeedbackAgent** (Figure 9): System role + mistake analysis
- **CorrectionAgent** (Figure 10): System instructions + SQL format requirements
- **ManagerAgent** (Figure 13): Guideline compilation with "ask-to-myself" questions

## Cost Estimation

Using `Meta-Llama-3.1-8B-Instruct-Turbo` ($0.18/M tokens):

| Operation | Queries | Est. Tokens | Est. Cost |
|-----------|---------|-------------|-----------|
| Training | 70 | ~290K | ~$0.05 |
| Inference (test) | 21 | ~50K | ~$0.01 |
| **Total** | **91** | **~340K** | **~$0.06** |

Costs scale linearly with dataset size. Larger models (32B, 70B) cost 2-5x more.

## Troubleshooting

### Import Errors
```bash
# If you see "ModuleNotFoundError"
pip install python-dotenv together --user
```

### API Key Issues
```bash
# Verify .env file exists and contains your key
cat .env
# Should show: TOGETHER_API_KEY=your_key_here
```

### Database Not Found
```bash
# Ensure database exists at correct path
ls database/economic_data.db
# If missing, regenerate from scripts (see main README)
```

### Relative Import Issues
```bash
# Always run as module from repository root:
python3 -m magic_implementation.train_magic

# NOT: cd magic_implementation && python3 train_magic.py
```

## Development

### Running Tests

Quick validation:
```bash
# Test training pipeline (2 queries)
python3 -m magic_implementation.test_magic_minimal

# Test inference pipeline (5 queries)
python3 -m magic_implementation.test_inference
```

### Adding New Agents

Follow the pattern in existing agents:
1. Import `Together` client and config
2. Define system and user prompts
3. Implement main method with token tracking
4. Use `extract_sql()` helper for SQL extraction

### Modifying Guidelines

Guidelines are automatically generated but can be manually edited

## Citation

If you use this implementation, please cite the original MAGIC paper:

```bibtex
@article{cho2024magic,
  title={MAGIC: Generating Self-Correction Guideline for In-Context Text-to-SQL},
  author={Cho, Jaehyuk and others},
  journal={arXiv preprint arXiv:2406.12692},
  year={2024}
}
```

## Future Improvements

- [ ] Test with larger reasoning models (32B, 70B)
- [ ] Expand training data for complex queries
- [ ] Compare with ALPHA-SQL and FinSQL techniques

## License

See main repository LICENSE file.

