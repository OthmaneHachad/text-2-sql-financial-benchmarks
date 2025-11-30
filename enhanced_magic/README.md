# Enhanced MAGIC

**Multi-Agent Guideline-based Iterative Correction + Schema Linking + Self-Consistency**

## Overview

Enhanced MAGIC combines the best components from MAGIC and FinSQL:

- **From MAGIC**: Proven guidelines (11 mistake patterns, +9.5pp improvement)
- **From FinSQL**: Fast schema linking (fixes table confusion)
- **From FinSQL**: Self-consistency voting (reduces output variance)

### Architecture

```
Input Question
     ↓
Schema Linking (FinSQL - embedding-based, <1s)
     ↓
Generate N candidates with guidelines (MAGIC approach)
     ↓
Self-Consistency Voting (FinSQL calibration)
     ↓
Final SQL
```

## Why This Approach?

### Avoids LoRA Weaknesses
- FinSQL's LoRA: 203 examples insufficient for 8B model
- Table confusion persists (gfs vs gem)
- Hallucinates tables (observations, tax_revenue)
- Cannot generalize to complex queries (CTEs)

### Leverages Proven Strengths
- MAGIC baseline: 52.4% (better than FinSQL's 47.6%)
- Schema linking: Eliminates table hallucination
- Guidelines: Capture patterns without training
- Self-consistency: Fixes single-sample variance

## Expected Results

| Method | Accuracy | Cost | Strengths |
|--------|----------|------|-----------|
| MAGIC (baseline) | 52.4% | $0.10 | Guidelines work |
| FinSQL Phase 1 | 47.6% | $0.54 | Schema linking, voting |
| **Enhanced MAGIC** | **57-62%** | **$0.22** | **Best of both** |

### Specific Improvements

**Schema Linking fixes:**
- Query #6: No hallucinated `observations` table
- Query #7-8: Correct gfs vs gem selection
- Query #16: No hallucinated `tax_revenue` table

**Self-Consistency fixes:**
- Query #11: Vote on correct indicator JOIN
- Query #14: Vote on correct ORDER BY

**Expected gain:** +3-5 queries over MAGIC baseline

## Components

### 1. Schema Linking (`modules/schema_linker.py`)
- Reuses FinSQL's `EmbeddingSchemaLinker`
- SentenceTransformer: all-MiniLM-L6-v2
- Fast inference (<1s)

### 2. Guideline Manager (`modules/guideline_manager.py`)
- Loads MAGIC's trained guideline
- Optional: Extract relevant patterns based on question keywords
- Reduces token overhead

### 3. Enhanced Inference (`enhanced_inference.py`)
- Generates N candidates (default: 5)
- Uses base model (no fine-tuning)
- Temperature: 0.7 for diversity

### 4. Output Calibrator (`modules/output_calibrator.py`)
- Reuses FinSQL's self-consistency voting
- SQL normalization
- Execution validation

## Usage

```python
from enhanced_magic.enhanced_inference import EnhancedMAGIC

# Initialize
enhanced = EnhancedMAGIC(num_samples=5)

# Generate SQL
sql = enhanced.generate(
    question="Show GDP for United States from 2010 to 2020"
)

print(sql)
```

## Evaluation

```bash
# Run on 21-query test set
python enhanced_magic/evaluate.py

# Compare with MAGIC and FinSQL
python enhanced_magic/comparison.py
```

## Cost Analysis

**Per Query:**
- Schema linking: Free (embedding-based)
- Input tokens: ~2,500 (linked schema + guideline + question)
- Output tokens: ~80 per sample
- Samples: 5
- Cost: ~$0.008/query

**Full Evaluation (21 queries):**
- Inference: $0.168
- Total: $0.220 (vs FinSQL $0.54, MAGIC $0.10)

## Files

```
enhanced_magic/
├── __init__.py
├── README.md
├── config.py                    # Configuration
├── enhanced_inference.py        # Main inference engine
├── evaluate.py                  # 21-query evaluation
├── comparison.py                # Compare with MAGIC/FinSQL
├── modules/
│   ├── schema_linker.py        # Reuse FinSQL's linker
│   ├── guideline_manager.py    # Load/filter MAGIC guidelines
│   └── output_calibrator.py    # Reuse FinSQL's calibrator
└── evaluation/
    └── results/                # Evaluation outputs
```

## Next Steps

1. Implement core components
2. Test on sample queries
3. Full 21-query evaluation
4. Compare with MAGIC and FinSQL
5. Error analysis and refinement
