# FinSQL Phase 1 Results - Comprehensive Report

**Model**: Meta-Llama-3.1-8B-Instruct
**Dataset**: GFS + GEM Economic Data (21 queries)
**Date**: November 29, 2025

---

## 1. Executive Summary

**Final Accuracy**: 47.6% (10/21 correct)

| Framework | Accuracy | Improvement |
|-----------|----------|-------------|
| LoRA-only (6 epochs) | 14.3% (3/21) | Baseline |
| FinSQL (broken calibrator) | 19.0% (4/21) | +4.7% |
| FinSQL (fixed calibrator) | 47.6% (10/21) | +33.3% |
| **FinSQL Phase 1** (10 epochs, fixed skeleton) | **47.6% (10/21)** | **+0.0%** |
| MAGIC (best) | 52.4% (11/21) | +5.0% over FinSQL |

**Key Finding**: Placeholder issue eliminated, but accuracy unchanged. LoRA training quality is the bottleneck, not skeleton format.

---

## 2. Implementation Overview

### 2.1 Architecture

**Three Components**:
1. **Schema Linking**: Embedding-based (SentenceTransformer: all-MiniLM-L6-v2)
2. **LoRA Fine-Tuning**: 4 specialized plugins
3. **Output Calibration**: Self-consistency + typo fixes

### 2.2 Training Configurations

| Configuration | Epochs | Skeleton Format | Prompts | Accuracy |
|---------------|--------|-----------------|---------|----------|
| Baseline | 6 | SQL Pattern with placeholders | Standard | 47.6% |
| Phase 1 | 10 | Pattern Type only | + "No placeholders" | 47.6% |

**Training Data**: 203 examples
- cot_specialist: 70 examples
- robustness_specialist: 49 examples
- structure_specialist: 70 examples
- hard_cases_specialist: 14 examples

**LoRA Config**: rank=16, alpha=32, target=['q_proj', 'v_proj']

---

## 3. Problem Identification & Fixes

### 3.1 The Placeholder Issue

**Root Cause**: Training data showed skeleton with placeholders

```python
# BEFORE (Broken)
user_content = f"""
SQL Pattern: SELECT [YEAR], [METRIC] FROM [TABLE] WHERE [YEAR] > [NUMBER]
Pattern Type: time_series_with_filter
"""

# Model Output: SELECT g.[YEAR], g.[METRIC] FROM...  ❌
```

**Impact**: Queries #18-21 generated placeholders instead of concrete SQL

**Solution**:
```python
# AFTER (Fixed)
user_content = f"""
Pattern Type: time_series_with_filter
Instructions: Identify required SQL components and generate accurate SQL.
"""

# Model Output: SELECT year, value FROM gem_observations...  ✅
```

### 3.2 Phase 1 Fixes

1. **Skeleton Format**: Removed `sql_skeleton` from training input
2. **Increased Epochs**: 6 → 10 for better convergence
3. **Inference Prompts**: Added explicit "no placeholders" instruction
4. **Validation Pipeline**: Automated SQL execution checking during augmentation

---

## 4. Results Comparison

### 4.1 Accuracy by Version

| Version | Correct | Accuracy | Key Issue |
|---------|---------|----------|-----------|
| LoRA-only | 3/21 | 14.3% | No schema linking or calibration |
| FinSQL (broken cal) | 4/21 | 19.0% | Calibrator breaking SQL |
| FinSQL (fixed cal) | 10/21 | 47.6% | Placeholders in output |
| **FinSQL Phase 1** | **10/21** | **47.6%** | **Table confusion, hallucinations** |

### 4.2 Query-by-Query Changes

**Baseline → Phase 1**:

| Query | Before | After | Change |
|-------|--------|-------|--------|
| #1-5 | ✅ (5/5) | ✅ (5/5) | No change (simple queries) |
| #6-17 | ❌/✅ (5/12) | ❌/✅ (5/12) | No change |
| #18 | ❌ Placeholders | ❌ Wrong logic | Fixed placeholders, wrong JOIN |
| #19 | ❌ Placeholders | ❌ Missing CTE | Fixed placeholders, oversimplified |
| #20 | ❌ Placeholders | ❌ Missing CTE | Fixed placeholders, wrong sector |
| #21 | ❌ Placeholders | ❌ Wrong table | Fixed placeholders, hallucinated `years` |

**Net change**: Placeholders eliminated ✅, but logical errors persist ❌

### 4.3 Success Patterns

**Simple Queries (100% success)**:
- Single table, basic aggregation (COUNT, MIN, MAX)
- Examples: #1-5

**Medium Queries (41.7% success)**:
- 2-3 table JOINs with filters
- Success: #10, #12, #13, #15, #17
- Failure: #6-9, #11, #14, #16

**Complex Queries (0% success)**:
- CTEs, window functions, correlation
- All failed: #18-21

### 4.4 Persistent Errors

| Error Type | Queries | Example |
|------------|---------|---------|
| **Hallucinated tables** | #6, #16, #21 | `observations`, `tax_revenue`, `years` |
| **Table confusion** | #7-9 | Using `gfs_observations` instead of `gem_observations` |
| **Missing JOINs** | #11 | No indicator JOIN for unemployment rate |
| **Wrong logic** | #14, #18-21 | ORDER BY count (not year), missing CTEs |

---

## 5. Cost Analysis

### 5.1 Training Costs

| Version | Epochs | Plugins | Training Time | Est. Cost |
|---------|--------|---------|---------------|-----------|
| Baseline | 6 | 4 | ~1 hour | $0.30 |
| Phase 1 | 10 | 4 | ~1.5 hours | $0.50 |

**Training Details** (Phase 1):
- cot_specialist: 19 min (90 steps)
- robustness_specialist: 14 min (90 steps)
- structure_specialist: 43 min (90 steps) ← Most examples
- hard_cases_specialist: 18 min (90 steps)

### 5.2 Inference Costs

- **Per query**: ~$0.0017 (20 candidates)
- **21 queries**: $0.0352
- **Token usage**: 195,679 tokens (106K input + 89K output)

---

## 6. Key Findings for Paper

### 6.1 What Worked ✅

1. **Embedding-based Schema Linking**
   - Fast inference (<1s for full schema)
   - No training required
   - Correct table retrieval in all test cases

2. **Placeholder Issue Resolution**
   - Systematic debugging identified root cause
   - Pattern-based training > skeleton-based training
   - Zero placeholder outputs after fix

3. **Output Calibration** (after fixes)
   - Self-consistency improved over single-plugin results
   - Typo fixing prevented syntax errors
   - Removed harmful JOIN/alignment functions (+28.6% gain)

### 6.2 What Didn't Work ❌

1. **LoRA Training Quality**
   - 203 examples insufficient for 8B model
   - Table name confusion persists (gfs vs gem)
   - Hallucinates non-existent tables

2. **Epoch Increase (6→10)**
   - No accuracy improvement
   - Same errors persist
   - Suggests data quality > quantity

3. **Complex Query Handling**
   - Cannot generate CTEs or window functions
   - Oversimplifies correlation/aggregation queries
   - Missing indicator JOINs

### 6.3 Training Data vs Model Size Hypothesis

**Observation**: 203 examples may be too few for 8B model to generalize

**Evidence**:
- Simple patterns learned (single-table queries: 100%)
- Complex patterns not learned (CTEs: 0%)
- Table confusion suggests insufficient exposure

**Implications**:
- Need 500-1000+ examples for 8B model, OR
- Use larger model (70B) with same data, OR
- Use different approach (prompting > fine-tuning)

---

## 7. Error Analysis Deep Dive

### 7.1 Hallucinated Tables

**Query #6**: Uses `observations` (doesn't exist) instead of `gfs_observations`
```sql
-- Generated:
SELECT COUNT(*) FROM observations WHERE transformation = 'Percent of GDP'

-- Should be:
SELECT COUNT(*) FROM gfs_observations WHERE transformation = 'Percent of GDP'
```

**Query #16**: Creates fake tables `tax_revenue`, `country_tax_revenue`
```sql
-- Generated:
SELECT c.country_name FROM countries c
JOIN country_tax_revenue ct ON ...
JOIN tax_revenue tr ON ...

-- Should use:
JOIN gfs_observations g ON ...
JOIN indicators i ON ... WHERE i.indicator_name = 'Taxes...'
```

**Root Cause**: Model generalizes table names from training, invents plausible-sounding names

### 7.2 Table Confusion (gfs vs gem)

**Pattern**: Queries about GEM indicators use gfs_observations table

| Query | Should Use | Actually Uses | Impact |
|-------|-----------|---------------|--------|
| #8 | gem_observations | gfs_observations | Wrong data source |
| #9 | gem_observations | gfs_observations | Wrong data source |
| #13 | gfs_observations | gem_observations | Wrong data source |

**Root Cause**: Schema linking retrieves both tables; model can't distinguish which to use

### 7.3 Complex Query Failures

**Query #19** (Correlation calculation):
```sql
-- Ground Truth: 30-line CTE with correlation formula
WITH paired_data AS (...), stats AS (...)
SELECT (n * sum_xy - sum_x * sum_y) / SQRT(...) AS correlation

-- Generated: Simple SELECT
SELECT g.value AS revenue, e.value AS expenditure FROM gfs_observations...
```

**Root Cause**: Training data has no CTE examples; model defaults to simple SELECT

---

## 8. Lessons Learned

### 8.1 Skeleton-Based Training Risks

**Avoid**: Showing template syntax in training data
**Use**: Abstract pattern labels instead

```
❌ BAD: SQL Pattern: SELECT [YEAR], [METRIC] FROM [TABLE]
✅ GOOD: Pattern Type: time_series_query
```

### 8.2 LoRA Limitations with Small Datasets

- Fine-tuning ≠ guaranteed improvement
- 203 examples insufficient for 8B model
- Logical errors persist even with more epochs
- Larger models or more data needed

### 8.3 Output Calibration Design Principles

1. **Test each function independently**: Don't blindly implement paper methods
2. **Simple > Complex**: Typo fixes safer than aggressive transformations
3. **Validate during augmentation**: Catch bad training data early
4. **Disable harmful components**: Removed JOIN/alignment → +28.6% accuracy

### 8.4 Schema Linking Effectiveness

**Observation**: Schema linking works but doesn't solve table confusion

**Why**: Linking retrieves multiple relevant tables; model must still choose correctly

**Solution**: Need better table selection logic or training examples showing disambiguation

---

## 9. Future Work: Model Comparison Opportunities

### 9.1 Ablation Studies

Test each component's contribution:

| Configuration | Schema Linking | LoRA | Calibration | Expected Accuracy |
|---------------|----------------|------|-------------|-------------------|
| Baseline | ❌ | ❌ | ❌ | ~40% (baseline prompting) |
| + Schema | ✅ | ❌ | ❌ | ~42% (+2%) |
| + LoRA | ✅ | ✅ | ❌ | ~45% (+3%) |
| **Full FinSQL** | ✅ | ✅ | ✅ | **47.6%** (+2.6%) |

### 9.2 Model Size Comparison

**Hypothesis**: Larger models will handle limited training data better

| Model | Parameters | Expected Accuracy | Reasoning |
|-------|-----------|-------------------|-----------|
| Llama-3.1-8B | 8B | 47.6% | Current result |
| Llama-3.1-70B | 70B | 55-65% | Better generalization |
| Llama-3.3-70B | 70B | 60-70% | Latest architecture |

**Test Plan**: Re-run Phase 1 with same training data on larger models

### 9.3 Training Data Scaling

**Hypothesis**: More examples will improve 8B model performance

| Training Examples | Expected Accuracy |
|-------------------|-------------------|
| 203 (current) | 47.6% |
| 500 | 52-58% |
| 1000 | 58-65% |

**Limitation**: Time-consuming to curate high-quality examples

---

## 10. Files & Reproducibility

### 10.1 Training Data

**Location**: `/data/finsql/training_data/`
- `cot_training.jsonl` (70 examples, 250KB)
- `synonym_training.jsonl` (49 examples, 84.5KB)
- `skeleton_training.jsonl` (70 examples, 140KB) ← **Fixed format**
- `hard_training.jsonl` (14 examples, 31.6KB)

**Validation**: All 203 examples validated (0 errors)

### 10.2 Model Artifacts

**Plugin Registry**: `finsql/lora/plugin_registry.json`
```json
{
  "cot_specialist": "othmanehachad_a13c/Meta-Llama-3.1-8B-Instruct-Reference-cot_specialist-898a207d",
  "robustness_specialist": "othmanehachad_a13c/Meta-Llama-3.1-8B-Instruct-Reference-robustness_specialist-a72e6729",
  "structure_specialist": "othmanehachad_a13c/Meta-Llama-3.1-8B-Instruct-Reference-structure_specialist-6c4f5636",
  "hard_cases_specialist": "othmanehachad_a13c/Meta-Llama-3.1-8B-Instruct-Reference-hard_cases_specialist-e76c9fc6"
}
```

**TogetherAI Job IDs**:
- cot: `ft-663478fc-19b6`
- robustness: `ft-f4a9a31a-621a`
- structure: `ft-483ce609-ff79`
- hard_cases: `ft-6c6c0278-7329`

### 10.3 Evaluation Results

**Baseline**: `data/results/finsql/full_finsql_eval_20251128_210118.json`
- Broken calibrator: 19.0%
- Fixed calibrator: 47.6%

**Phase 1**: `data/results/finsql/full_finsql_eval_20251129_153037.json`
- Fixed skeleton + 10 epochs: 47.6%

### 10.4 Scripts

**Training**:
- `finsql/lora/train_lora.py` - Launch fine-tuning jobs
- `finsql/modules/data_augmenter.py` - Data augmentation
- `finsql/lora/data_formatter.py` - Format training data

**Evaluation**:
- `finsql/full_finsql_inference.py` - Full pipeline evaluation
- `finsql/lora/clean_training_data.py` - Validation script

---

## 11. Conclusion

### Summary

FinSQL achieved **47.6% accuracy** on 21-query economic dataset using Llama-3.1-8B:
- ✅ Competitive with MAGIC baseline (52.4%)
- ✅ Major improvement over LoRA-only (14.3%)
- ✅ Placeholder issue successfully eliminated
- ❌ No improvement from additional training (6→10 epochs)
- ❌ Persistent table confusion and hallucinations

### Key Contributions

1. **Systematic Debugging**: Root-caused placeholder issue to skeleton format
2. **Empirical Evidence**: More epochs ≠ better results with limited data
3. **Component Analysis**: Output calibration critical (+28.6%), but must be carefully designed
4. **Reusable Framework**: Ready for larger model testing


**What to emphasize**:
- FinSQL's three-component architecture
- Embedding-based schema linking (practical alternative to Cross-Encoder)
- Placeholder debugging process (shows systematic evaluation)
- Error analysis revealing LoRA limitations with small datasets

**What to acknowledge**:
- 8B model + 203 examples insufficient for complex queries
- Fine-tuning requires careful data curation
- Prompting-based approaches (MAGIC) may be more practical


### Takeaways

FinSQL demonstrates that **component integration** (schema linking + fine-tuning + calibration) can match strong baselines, but **training data quality and model size** are critical bottlenecks. The framework is sound; scaling requires either larger models or substantially more training examples.

---

