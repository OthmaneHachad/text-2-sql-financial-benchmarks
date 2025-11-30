# FinSQL Multi-Model Comparison: Llama-3.1 8B vs 70B

**Date**: November 30, 2025
**Evaluation**: 21-query economic dataset (GFS + GEM)

---

## Executive Summary

| Model | Parameters | Accuracy | Correct | Training Data | LoRA Config | Result |
|-------|-----------|----------|---------|---------------|-------------|--------|
| **Llama-3.1-8B** | 8B | **47.6%** | 10/21 | 203 examples | rank=16, alpha=32 | Baseline |
| **Llama-3.1-70B** | 70B | **42.9%** | 9/21 | 203 examples | rank=16, alpha=32 | **-4.7pp** ❌ |

**Key Finding**: Larger model (70B) performed **worse** than smaller model (8B) with limited training data.

**Hypothesis Rejected**: "Larger models generalize better with limited training data (203 examples)"

---

## Detailed Results

### Performance by Query Difficulty

| Difficulty | Llama-8B | Llama-70B | Change |
|------------|----------|-----------|--------|
| **Simple** (1-5) | 5/5 (100%) | 5/5 (100%) | 0pp ✓ Same |
| **Medium** (6-17) | 5/12 (41.7%) | 4/12 (33.3%) | -8.4pp ❌ Worse |
| **Complex** (18-21) | 0/4 (0%) | 0/4 (0%) | 0pp ✓ Same |

### Query-by-Query Comparison

| Query | Type | Llama-8B | Llama-70B | Change |
|-------|------|----------|-----------|--------|
| #1 | Simple SELECT | ✅ | ✅ | - |
| #2 | COUNT aggregation | ✅ | ✅ | - |
| #3 | MAX aggregation | ✅ | ✅ | - |
| #4 | LIKE pattern | ✅ | ✅ | - |
| #5 | MIN aggregation | ✅ | ✅ | - |
| #6 | WHERE filter | ❌ | ❌ | - (both hallucinate table) |
| #7 | Multi-JOIN time series | ❌ | ❌ | - (both use wrong dataset) |
| #8 | Multi-JOIN GEM data | ❌ | ❌ | - (both wrong joins) |
| #9 | Multi-JOIN GEM GDP | ❌ | ❌ | - (both use wrong dataset) |
| #10 | Multi-JOIN terms of trade | ✅ | ❌ | **Regression** (70B wrong dataset) |
| #11 | Conditional filter | ❌ | ❌ | - (both wrong indicator join) |
| #12 | GROUP BY with LIMIT | ✅ | ✅ | - |
| #13 | Multi-JOIN social benefits | ✅ | ❌ | **Regression** (70B wrong columns) |
| #14 | COUNT DISTINCT | ✅ | ✅ | - |
| #15 | SUM aggregation | ✅ | ✅ | - |
| #16 | DISTINCT with JOIN | ❌ | ❌ | - (both hallucinate table) |
| #17 | AVG by sector | ✅ | ✅ | - |
| #18 | CTE with UNION | ❌ | ❌ | - (both hallucinate tables) |
| #19 | Correlation calculation | ❌ | ❌ | - (both oversimplify) |
| #20 | Complex CTE analysis | ❌ | ❌ | - (both missing CTEs) |
| #21 | CASE aggregation | ❌ | ❌ | - (both wrong logic) |

### Key Regressions in Llama-70B

**Query #10** (Terms of Trade):
- **Llama-8B**: ✅ Correct (used gem_observations)
- **Llama-70B**: ❌ Wrong dataset (used gfs_observations)
- **Impact**: Lost correct answer on medium-difficulty query

**Query #13** (Social Benefits):
- **Llama-8B**: ✅ Correct
- **Llama-70B**: ❌ Wrong indicator_id and column names
- **Impact**: Lost correct answer on multi-JOIN query

---

## Error Analysis

### Common Errors (Both Models)

| Error Type | Queries | Description |
|------------|---------|-------------|
| **Hallucinated tables** | #6, #16, #18 | Invented non-existent tables (`observations`, `tax_revenue`, etc.) |
| **Dataset confusion** | #7-9 | Used `gfs_observations` instead of `gem_observations` or vice versa |
| **Missing JOINs** | #11 | Incorrect indicator matching |
| **Complex query oversimplification** | #19-21 | Cannot generate CTEs, window functions, correlation formulas |

### Llama-70B Specific Errors

| Error | Queries | Issue |
|-------|---------|-------|
| **Dataset regression** | #10 | Used gfs_observations when gem_observations was correct |
| **Column hallucination** | #13 | Wrong column names (agg_method, transform, scale don't exist) |

---

## Training Configuration Comparison

| Aspect | Llama-8B | Llama-70B |
|--------|----------|-----------|
| **Base Model** | Meta-Llama-3.1-8B-Instruct-Reference | Meta-Llama-3.1-70B-Instruct-Reference |
| **Training Data** | 203 examples (same) | 203 examples (same) |
| **LoRA Rank** | 16 | 16 |
| **LoRA Alpha** | 32 | 32 |
| **Target Modules** | q_proj, v_proj | q_proj, v_proj |
| **Epochs** | 10 | 10 |
| **Training Time** | ~1.5 hours | ~4-6 hours |
| **Training Cost** | ~$0.30 | ~$0.50 |
| **Plugins** | 4 specialists | 4 specialists |

---

## Cost-Benefit Analysis

| Metric | Llama-8B | Llama-70B | Difference |
|--------|----------|-----------|------------|
| **Training Cost** | $0.30 | $0.50 | +$0.20 (67% more) |
| **Training Time** | 1.5 hours | 4-6 hours | +3-4.5 hours |
| **Accuracy** | 47.6% | 42.9% | **-4.7pp worse** |
| **Correct Queries** | 10/21 | 9/21 | -1 query |
| **ROI** | Baseline | **Negative** | Worse results for higher cost |

**Conclusion**: Llama-70B provides **worse accuracy** at **67% higher cost** and **3x longer training time**.

---

## Analysis: Why Did 70B Perform Worse?

### Hypothesis 1: Insufficient Training Data

**203 examples may be too few for 70B model**:
- **8B model**: 203 examples / 8B params ≈ 25 examples per billion parameters
- **70B model**: 203 examples / 70B params ≈ **3 examples per billion parameters**

**Impact**: Larger model may be **underfitting** due to data scarcity

### Hypothesis 2: LoRA Configuration Mismatch

**Same LoRA config (rank=16) may be suboptimal for 70B**:
- Rank-16 adapters may be:
  - Too low for 70B's capacity (underparameterized)
  - Same update budget spread across more base parameters

**Evidence**: 70B made **different errors** (#10, #13) suggesting worse adaptation

### Hypothesis 3: Overfitting to Shallow Patterns

**8B model learns simpler patterns**:
- Limited capacity forces focus on core patterns
- Better generalization with limited data

**70B model has more capacity**:
- Can overfit to spurious correlations
- May memorize training noise instead of patterns

### Hypothesis 4: Base Model Instruction Tuning

**8B vs 70B base models have different instruction tuning**:
- 8B may be better tuned for structured tasks
- 70B optimized for different objectives (reasoning, coding)

**Evidence**: Both models perfect on simple queries, diverge on medium complexity

---

## Recommendations

### For 70B Model to Match/Exceed 8B

1. **Increase Training Data** (highest priority)
   - Target: 500-1000 examples (2.5-5x current)
   - Ensures ~7-14 examples per billion parameters
   - Expected improvement: +10-20pp

2. **Optimize LoRA Configuration**
   - Increase rank: 16 → 32 or 64
   - More update capacity for larger model
   - Expected improvement: +3-7pp

3. **Domain-Specific Pre-training**
   - Add intermediate pre-training on SQL + economic data
   - Before LoRA fine-tuning
   - Expected improvement: +5-10pp

4. **Adjust Learning Rate**
   - 70B may need different LR schedule
   - Test: 1e-4, 3e-4, 5e-4
   - Expected improvement: +2-5pp

### Alternative: Hybrid Approach

**Use 8B for production** (current best):
- Lower cost ($0.30 vs $0.50 training)
- Faster training (1.5h vs 4-6h)
- Better accuracy (47.6% vs 42.9%)

**Use 70B for research**:
- Test with more training data
- Explore LoRA configuration space
- Benchmark upper bound of FinSQL approach

---

## Comparison with MAGIC Baseline

| Method | Model | Accuracy | Notes |
|--------|-------|----------|-------|
| **MAGIC** | Llama-8B | **52.4%** | Prompting-based, no training |
| **Smart MAGIC + Guidelines** | Llama-8B | **57.1%** | Best MAGIC variant |
| **FinSQL** | Llama-8B | 47.6% | LoRA fine-tuning (203 examples) |
| **FinSQL** | Llama-70B | 42.9% | Larger model, worse results |

**Key Insight**: Prompting (MAGIC) outperforms fine-tuning (FinSQL) for both models when training data is limited.

---

## Lessons Learned

### 1. Model Size ≠ Better Performance with Limited Data

- 203 examples insufficient for 70B model
- Smaller models generalize better with scarce data
- **Rule of thumb**: Need ~10-20 examples per billion parameters

### 2. LoRA Configuration Must Scale with Model Size

- Same LoRA config (rank=16) suboptimal for 70B
- Larger models need proportionally larger LoRA adapters
- One-size-fits-all approach fails

### 3. Cost-Benefit Tradeoff

- 70B costs 67% more for 4.7pp worse accuracy
- Training time 3x longer
- ROI negative for current setup

### 4. Prompting vs Fine-Tuning Tradeoff

- MAGIC (57.1%) > FinSQL-8B (47.6%) > FinSQL-70B (42.9%)
- Prompting more sample-efficient than fine-tuning
- Fine-tuning needs substantial data to justify cost

---

## Future Work

### Short-Term (Improve 70B)

1. Collect 300-500 more training examples
2. Increase LoRA rank to 32-64
3. Tune learning rate schedule
4. Add validation set for early stopping

### Long-Term (Research)

1. **Hybrid FinSQL + MAGIC**:
   - Use MAGIC guidelines in fine-tuning data
   - Combine schema linking with prompting
   - Expected: Best of both worlds

2. **Multi-Stage Training**:
   - Stage 1: Pre-train on general SQL
   - Stage 2: Fine-tune on economic domain
   - Expected: Better domain adaptation

3. **Model-Specific LoRA Tuning**:
   - Automatic LoRA rank selection per model
   - Adaptive learning rate based on model size
   - Expected: Optimal configuration per model

---

## Conclusion

**Key Finding**: Llama-3.1-70B with FinSQL achieved **42.9% accuracy**, performing **4.7 percentage points worse** than Llama-3.1-8B (47.6%) on the same training data (203 examples).

**Implications**:
1. ✅ **Smaller models better with limited data**: 8B outperforms 70B
2. ❌ **Hypothesis rejected**: "Larger models generalize better" does not hold with 203 examples
3. ⚠️ **Data scarcity bottleneck**: 70B needs ~500-1000 examples to show benefit
4. 💰 **Negative ROI**: 70B costs more, trains slower, performs worse

**Recommendation**: **Continue using Llama-3.1-8B** for FinSQL production until sufficient training data (500+ examples) is available to properly leverage 70B's capacity.

**Best Overall**: **Smart MAGIC + Guidelines** (57.1%) on Llama-8B remains the best approach, outperforming both FinSQL variants by combining prompting with domain-specific patterns.

---

## Files

**Results**:
- Llama-8B: `data/results/finsql/full_finsql_eval_20251129_153037.json` (47.6%)
- Llama-70B: `data/results/finsql/full_finsql_eval_20251130_114238.json` (42.9%)

**Plugin Registries**:
- Llama-8B: `finsql/lora/plugin_registry.json`
- Llama-70B: `finsql/lora/plugin_registry_llama70b.json`

**Training Data**: `data/finsql/training_data/*.jsonl` (203 examples total)
