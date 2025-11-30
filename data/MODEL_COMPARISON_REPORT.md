# Model Comparison Report: MAGIC Methods Across 4 Models

**Date:** November 29, 2025
**Test Set:** 21 queries from economic database
**Temperature:** 0.3 (consistent across all models and methods)

---

## Executive Summary

We evaluated **two approaches** across multiple models:
1. **MAGIC (Prompting):** 4 models on 3 MAGIC techniques + zero-shot
2. **FinSQL (Fine-Tuning):** Llama 8B and 70B with LoRA adapters

**CRITICAL FINDINGS:**

### 1. Prompting (MAGIC) is Model-Specific
- **GPT-OSS 20B:** Best zero-shot (57.1%) but **HURT by all techniques** (down to 47.6%)
- **Llama 3.1 8B:** Worst zero-shot (38.1%) but **BEST with guidelines** (57.1%, **+19.0pp improvement**)
- **Mistral/Qwen:** Techniques provide **no benefit** (same as zero-shot)

### 2. Fine-Tuning (FinSQL) Needs More Data
- **Llama-8B:** FinSQL 47.6% vs MAGIC 57.1% (**prompting wins by 9.5pp**)
- **Llama-70B:** FinSQL 42.9% (**worse than 8B despite 8.75x more parameters**)
- **Root Cause:** 203 training examples insufficient for 70B (only 3 examples/billion params)

**Key Insight:** With limited data (203 examples), **prompting (MAGIC) outperforms fine-tuning (FinSQL)**. Techniques are highly model-specific - they dramatically improve instruction-tuned models (Llama) but hurt strong baselines (GPT-OSS).

---

## Overall Results

### Zero-Shot Baseline (No Techniques)

**Pure baseline:** Full schema + simple prompt, no guidelines/schema linking/voting

| Model | Parameters | Zero-Shot Accuracy | Execution Errors |
|-------|-----------|-------------------|------------------|
| **openai/gpt-oss-20b** | 20B | **12/21 (57.1%)** | 2 |
| **meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo** | 70B | **10/21 (47.6%)** | 1 |
| mistralai/Mistral-7B-Instruct-v0.3 | 7B | 10/21 (47.6%) | 3 |
| Qwen/Qwen2.5-7B-Instruct-Turbo | 7B | 9/21 (42.9%) | 3 |
| meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo | 8B | 8/21 (38.1%) | 3 |

**Key Findings:**
- GPT-OSS 20B remains best out-of-the-box (57.1%)
- Llama 70B significantly better than 8B (+9.5pp) but still below GPT-OSS
- Model size helps for zero-shot: 70B > 20B > 8B within families

---

### Best Performance with Techniques

| Model | Zero-Shot | Best Method | Best Accuracy | Improvement | Winner? |
|-------|-----------|-------------|---------------|-------------|---------|
| **GPT-OSS 20B** | **57.1%** | Zero-Shot | **57.1%** | **0.0pp** | ✓ TIED #1 |
| **Llama 3.1 8B** | 38.1% | **Smart MAGIC + Guidelines** | **57.1%** | **+19.0pp** | ✓ TIED #1 |
| **Llama 3.1 70B** | 47.6% | **Smart MAGIC/+Guidelines/+Retry** | **57.1%** | **+9.5pp** | ✓ TIED #1 |
| Mistral 7B | 47.6% | Zero-Shot / + Guidelines | 47.6% | 0.0pp | |
| Qwen 2.5 7B | 42.9% | Zero-Shot / + Guidelines | 42.9% | 0.0pp | |

**Critical Insights:**
- **Three models tie at 57.1%** with different approaches
- **Llama 8B:** Techniques essential (+19.0pp improvement)
- **Llama 70B:** Techniques helpful (+9.5pp improvement)
- **GPT-OSS 20B:** Techniques harmful (best = zero-shot)
- **Mistral/Qwen:** Techniques irrelevant (0pp change)

---

## Detailed Results by Method

### 0. Zero-Shot Baseline (Pure Baseline)

| Model | Accuracy | Execution Errors | Notes |
|-------|----------|------------------|-------|
| **GPT-OSS 20B** | **12/21 (57.1%)** | 2 | Best baseline |
| Mistral 7B | 10/21 (47.6%) | 3 | |
| Qwen 2.5 7B | 9/21 (42.9%) | 3 | |
| Llama 3.1 8B | 8/21 (38.1%) | 3 | Worst baseline |

**Analysis:**
- ✓ GPT-OSS 20B strong out-of-the-box (57.1%)
- ✗ Llama 3.1 8B weakest baseline (38.1%, -19.0pp)
- ➖ Model size correlates with zero-shot (20B > 7B > 8B Llama)

---

### 1. Smart MAGIC (Smart Schema + MAGIC Guidelines)

| Model | Accuracy | Execution Errors | vs Llama 3.1 8B |
|-------|----------|------------------|-----------------|
| **Llama 3.1 8B** | **11/21 (52.4%)** | 0 | **Baseline** |
| **GPT-OSS 20B** | **11/21 (52.4%)** | 1 | 0.0pp |
| Mistral 7B | 9/21 (42.9%) | 4 | -9.5pp |
| Qwen 2.5 7B | 7/21 (33.3%) | 1 | -19.1pp |

**Analysis:**
- ✓ Llama 3.1 8B and GPT-OSS 20B tied for best (52.4%)
- ✗ Qwen 2.5 7B struggled significantly (-19.1pp)
- ✗ Mistral 7B had more execution errors (4 vs 0-1)

---

### 2. Smart MAGIC + Dataset-Specific Guidelines

| Model | Accuracy | Execution Errors | vs Llama 3.1 8B |
|-------|----------|------------------|-----------------|
| **Llama 3.1 8B** | **12/21 (57.1%)** | 1 | **Baseline** |
| Mistral 7B | 10/21 (47.6%) | 1 | -9.5pp |
| Qwen 2.5 7B | 9/21 (42.9%) | 0 | -14.2pp |
| GPT-OSS 20B | 10/21 (47.6%) | 4 | -9.5pp |

**Analysis:**
- ✓ **Llama 3.1 8B best** - guidelines helped (+4.7pp from base)
- ✗ **GPT-OSS 20B hurt by guidelines** (-4.8pp from base, +3 execution errors)
- ➖ Mistral improved (+4.7pp from base)
- ➖ Qwen improved (+9.6pp from base, largest relative gain)

**Key Insight:** Llama 3.1 8B best at following complex prompts with guidelines. GPT-OSS 20B surprisingly struggled with enhanced guidelines, suggesting weaker instruction tuning despite larger size.

---

### 3. Smart MAGIC + Execution-Guided Retry

| Model | Accuracy | Execution Errors | vs Llama 3.1 8B |
|-------|----------|------------------|-----------------|
| **GPT-OSS 20B** | **11/21 (52.4%)** | 0 | **+4.8pp** |
| Mistral 7B | 9/21 (42.9%) | 3 | -4.7pp |
| Qwen 2.5 7B | 8/21 (38.1%) | 0 | -9.5pp |
| Llama 3.1 8B | 10/21 (47.6%) | 0 | Baseline |

**Analysis:**
- ✓ **GPT-OSS 20B benefits from retry** (+4.8pp vs Llama)
- ✗ Llama 3.1 8B hurt by retry (-4.8pp from base)
- ✗ All models still below Llama's guideline method

**Key Insight:** Retry helps GPT-OSS 20B recover from initial errors but doesn't surpass guideline-enhanced Llama. Suggests GPT-OSS generates more varied (but fixable) outputs.

---

## Model-Specific Insights

### 1. meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo ✓ BEST OVERALL REASONING

**Performance Progression:**
- Zero-Shot: 10/21 (47.6%) ← Better than 8B (+9.5pp)
- Smart MAGIC: **12/21 (57.1%)** [+9.5pp from zero-shot]
- + Guidelines: **12/21 (57.1%)** [+9.5pp] ← Tied best
- + Retry: **12/21 (57.1%)** [+9.5pp] ← Most robust

**Strengths:**
- ✓ **Best zero-shot among Llama family** (47.6% vs 38.1% for 8B)
- ✓ **Consistent 57.1% across all techniques** (Smart MAGIC, +Guidelines, +Retry)
- ✓ **Most robust to technique choice** - All three methods achieve 57.1%
- ✓ **Superior reasoning** - Fixed Query #6 that 8B missed
- ✓ **Fewer execution errors** (1 vs 3 for 8B in zero-shot)

**Weaknesses:**
- ✗ **4× more expensive than 8B** (~$0.008 vs ~$0.002 per query)
- ✗ **No improvement over 8B with guidelines** (both 57.1%)
- ✗ **Still below GPT-OSS 20B zero-shot** (47.6% vs 57.1%)
- ✗ **Fine-tuning underperforms 8B** (FinSQL: 42.9% vs 47.6%)

**Best Configuration:** Smart MAGIC, +Guidelines, or +Retry (all 57.1%)

**Cost-Benefit Analysis:**
- **vs 8B Zero-Shot:** Worth 4× cost for +9.5pp (47.6% vs 38.1%)
- **vs 8B Smart MAGIC:** Worth 4× cost for +4.7pp (57.1% vs 52.4%)
- **vs 8B +Guidelines:** NOT worth 4× cost for 0pp (both 57.1%)

**Recommendation:** Use 70B for zero-shot or Smart MAGIC. Switch to 8B when using guidelines.

---

### 2. meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo ✓ BEST WITH TECHNIQUES

**Performance Progression:**
- Zero-Shot: 8/21 (38.1%) ← Worst baseline
- Smart MAGIC: 11/21 (52.4%) [+14.3pp]
- + Guidelines: **12/21 (57.1%)** [**+19.0pp from zero-shot**] ← Best with techniques
- + Retry: 10/21 (47.6%) [+9.5pp from zero-shot]

**Strengths:**
- ✓ **Largest improvement from techniques** (+19.0pp)
- ✓ **Best with guidelines** (57.1%, tied with GPT-OSS zero-shot)
- ✓ Fewest execution errors with guidelines (1)
- ✓ Superior instruction following

**Weaknesses:**
- ✗ **Worst zero-shot baseline** (38.1%)
- ✗ Hurt by retry mechanism (-4.8pp from Smart MAGIC)
- ✗ Still fails all hard queries (0/4)

**Best Configuration:** Smart MAGIC + Guidelines (57.1%)

**Why Guidelines Work So Well:**
- Excellent instruction tuning enables complex prompt following
- Guidelines provide structure that weak baseline needs
- Dataset-specific patterns dramatically improve accuracy

---

### 2. openai/gpt-oss-20b ✓ BEST ZERO-SHOT

**Performance Progression:**
- **Zero-Shot: 12/21 (57.1%)** ← **Best baseline, BEST OVERALL**
- Smart MAGIC: 11/21 (52.4%) [-4.7pp] ⚠️
- + Guidelines: 10/21 (47.6%) [**-9.5pp from zero-shot**] ⚠️⚠️
- + Retry: 11/21 (52.4%) [-4.7pp from zero-shot]

**Strengths:**
- ✓ **Best zero-shot performance** (57.1%)
- ✓ Strong baseline model (no techniques needed)
- ✓ 2.5× larger parameter count than Llama
- ✓ Tied for overall best accuracy (57.1%)

**Weaknesses:**
- ✗ **HURT by all our techniques** (down to 47.6% with guidelines)
- ✗ **Doesn't benefit from prompt engineering** (-9.5pp)
- ✗ Guidelines cause execution errors (1 → 4)
- ✗ Can't improve beyond zero-shot baseline

**Best Configuration:** **Zero-Shot** (57.1%)

**Why Techniques Hurt:**
- Already strong baseline doesn't need help
- Complex prompts confuse rather than guide
- Guidelines add noise to already-good SQL generation
- Model not optimized for following complex instructions

**Critical Insight:** **Don't use MAGIC techniques with GPT-OSS 20B!** Just use simple zero-shot prompting.

---

### 3. mistralai/Mistral-7B-Instruct-v0.3

**Performance Progression:**
- **Zero-Shot: 10/21 (47.6%)** ← Best configuration
- Smart MAGIC: 9/21 (42.9%) [-4.7pp] ⚠️
- + Guidelines: 10/21 (47.6%) [**0.0pp from zero-shot**]
- + Retry: 9/21 (42.9%) [-4.7pp from zero-shot]

**Strengths:**
- ✓ Good zero-shot baseline (47.6%)
- ✓ Guidelines restore baseline (47.6%)
- ✓ Better than Qwen 2.5 7B

**Weaknesses:**
- ✗ **No net benefit from techniques** (0pp improvement)
- ✗ Smart MAGIC hurts baseline (-4.7pp)
- ✗ High execution error rate (1-4 errors)
- ✗ Retry doesn't help

**Best Configuration:** **Zero-Shot or Smart MAGIC + Guidelines** (both 47.6%)

**Characteristics:**
- Techniques neither help nor hurt (after guidelines)
- Smart schema linking hurts but guidelines recover
- More execution errors suggest less robust generation
- No improvement path beyond baseline

---

### 4. Qwen/Qwen2.5-7B-Instruct-Turbo

**Performance Progression:**
- **Zero-Shot: 9/21 (42.9%)** ← Best configuration (tied)
- Smart MAGIC: 7/21 (33.3%) [-9.6pp] ⚠️
- + Guidelines: 9/21 (42.9%) [**0.0pp from zero-shot**]
- + Retry: 8/21 (38.1%) [-4.8pp from zero-shot]

**Strengths:**
- ✓ **Largest recovery from Smart MAGIC** (+9.6pp with guidelines)
- ✓ Fewer execution errors than Mistral (0-1)
- ✓ Guidelines fully restore baseline

**Weaknesses:**
- ✗ **No net benefit from techniques** (0pp improvement)
- ✗ Smart MAGIC severely hurts baseline (-9.6pp)
- ✗ Still lowest overall performance (42.9%)
- ✗ Struggles with complex SQL generation

**Best Configuration:** **Zero-Shot or Smart MAGIC + Guidelines** (both 42.9%)

**Characteristics:**
- Smart schema linking very harmful (-9.6pp)
- Guidelines completely recover loss but don't improve
- More consistent (fewer errors) but less accurate overall
- No path to improvement beyond baseline

---

## Method Effectiveness Across Models

### Guidelines Effectiveness

| Model | Base Accuracy | + Guidelines | Improvement |
|-------|--------------|--------------|-------------|
| Qwen 2.5 7B | 33.3% | 42.9% | **+9.6pp** |
| Mistral 7B | 42.9% | 47.6% | **+4.7pp** |
| Llama 3.1 8B | 52.4% | 57.1% | **+4.7pp** |
| GPT-OSS 20B | 52.4% | 47.6% | **-4.8pp** ⚠️ |

**Key Insight:** Guidelines help all models **except GPT-OSS 20B**. Larger models don't always handle complex prompts better.

---

### Retry Effectiveness

| Model | Base Accuracy | + Retry | Change |
|-------|--------------|---------|--------|
| GPT-OSS 20B | 52.4% | 52.4% | 0.0pp |
| Mistral 7B | 42.9% | 42.9% | 0.0pp |
| Qwen 2.5 7B | 33.3% | 38.1% | +4.8pp |
| Llama 3.1 8B | 52.4% | 47.6% | -4.8pp ⚠️ |

**Key Insight:** Retry has **mixed results** across models. Temperature variance can hurt strong models (Llama) while helping weaker ones recover (Qwen).

---

## Execution Error Analysis

| Model | Smart MAGIC | + Guidelines | + Retry | Avg Errors |
|-------|------------|--------------|---------|------------|
| Llama 3.1 8B | 0 | 1 | 0 | **0.33** ✓ |
| Qwen 2.5 7B | 1 | 0 | 0 | **0.33** ✓ |
| GPT-OSS 20B | 1 | 4 | 0 | **1.67** |
| Mistral 7B | 4 | 1 | 3 | **2.67** ✗ |

**Key Insight:** Llama and Qwen most reliable (fewest errors). Mistral struggles with SQL syntax. GPT-OSS errors spike with guidelines.

---

## Parameter Count vs Performance

**Does size matter?**

| Model | Parameters | Best Accuracy | Accuracy per Billion Params |
|-------|-----------|---------------|------------------------------|
| Llama 3.1 8B | 8B | **57.1%** | **7.14%/B** ✓ Most efficient |
| Llama 3.1 70B | 70B | **57.1%** | **0.82%/B** |
| Mistral 7B | 7B | 47.6% | 6.80%/B |
| Qwen 2.5 7B | 7B | 42.9% | 6.13%/B |
| GPT-OSS 20B | 20B | 57.1% | 2.86%/B |

**Key Findings:**
- ✓ **8B Llama is MOST parameter-efficient** (7.14%/B)
- ✗ **70B Llama is LEAST parameter-efficient** (0.82%/B) despite same 57.1% accuracy
- ➖ **Diminishing returns after 8B** - 8.75× more params yields 0pp improvement with guidelines
- ✓ **Parameter count helps zero-shot** - 70B (+9.5pp) and 20B (+19.0pp) better than 8B baseline

**Why?**
- **With techniques:** Instruction tuning quality > raw parameters
- **Without techniques:** Raw parameters help significantly
- **Guidelines saturate performance** at 57.1% regardless of model size (8B, 20B, or 70B)

---

## Recommendations

### For Maximum Accuracy (Three Options at 57.1%)

**Option 1: Llama 3.1 8B + Smart MAGIC + Guidelines** ✓ BEST VALUE
- Accuracy: 57.1%
- Cost: ~$0.002/query (lowest)
- **Requires:** Complex prompt engineering
- **Best for:** Cost-sensitive, can invest in technique development
- **Advantage:** 4× cheaper than 70B, 10× cheaper than GPT-OSS

**Option 2: Llama 3.1 70B + Smart MAGIC (or +Guidelines or +Retry)**
- Accuracy: 57.1%
- Cost: ~$0.008/query (4× more than 8B)
- **Requires:** Moderate prompt engineering
- **Best for:** Want robustness to technique choice
- **Advantage:** Consistent 57.1% across all three techniques

**Option 3: GPT-OSS 20B + Zero-Shot**
- Accuracy: 57.1%
- Cost: ~$0.020/query (10× more than 8B)
- **Requires:** Simple prompting only
- **Best for:** Plug-and-play, no engineering overhead
- **Advantage:** No technique development needed

**Recommendation:** **Use Llama 8B + Guidelines** - best cost-performance ratio

---

### For Budget-Constrained Scenarios

**Best Choice:** **mistralai/Mistral-7B + Zero-Shot**
- Accuracy: 47.6%
- Cost: ~$0.15/M tokens (7B params)
- Method: Simple zero-shot (no technique development)
- Trade-off: -9.5pp accuracy vs best

**Avoid:** Mistral + techniques (no benefit, just complexity)

---

### When to Use Each Model

**Use Llama 3.1 8B when:**
- ✓ You can invest in prompt engineering
- ✓ You need cost-effective best accuracy
- ✓ Guidelines/techniques are available

**Use GPT-OSS 20B when:**
- ✓ You want simple zero-shot (no engineering)
- ✓ Cost is not a constraint
- ✓ You need best out-of-box performance

**Use Mistral/Qwen when:**
- ✓ Budget is primary constraint
- ✓ 47% accuracy is acceptable
- ✓ Use zero-shot only (don't waste time on techniques)

---

### CRITICAL: Model-Technique Matching

**DO:**
- ✓ Llama + Guidelines (+19.0pp improvement)
- ✓ GPT-OSS + Zero-Shot (best baseline, 57.1%)
- ✓ Mistral/Qwen + Zero-Shot (techniques don't help)

**DON'T:**
- ✗ GPT-OSS + Guidelines (-9.5pp, waste of effort)
- ✗ Mistral/Qwen + any techniques (0pp benefit)
- ✗ Llama + Zero-Shot (leaves 19pp on table)

---

## Future Work

### 1. Llama 70B Results ✅ COMPLETED

**Model:** meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo (70B params)

**MAGIC Results (Prompting):**

| Method | Llama 8B | Llama 70B | Change | Winner |
|--------|----------|-----------|--------|--------|
| Zero-Shot | 38.1% (8/21) | **47.6%** (10/21) | **+9.5pp** | 70B ✓ |
| Smart MAGIC | 52.4% (11/21) | **57.1%** (12/21) | **+4.7pp** | 70B ✓ |
| + Guidelines | **57.1%** (12/21) | **57.1%** (12/21) | **0.0pp** | Tie |
| + Retry | 47.6% (10/21) | **57.1%** (12/21) | **+9.5pp** | 70B ✓ |

**Key Findings:**
- ✓ **70B excels at prompting** - Wins on 3/4 methods, ties on 1
- ✓ **Zero-shot improvement: +9.5pp** (47.6% vs 38.1%)
- ✓ **Smart MAGIC improvement: +4.7pp** (57.1% vs 52.4%)
- ✓ **Guidelines saturate performance** - Both models reach 57.1%
- ✓ **Retry more robust on 70B** - Maintains 57.1% vs 8B's 47.6%

**Cost:** 4× more expensive per query (~$0.008 vs ~$0.002 for 8B)

**Recommendation:**
- **Use 70B for zero-shot/Smart MAGIC** - Worth 4× cost for +4.7pp to +9.5pp improvement
- **Use either model for Guidelines** - Same 57.1% accuracy, so 8B is 4× cheaper

### 2. Test Qwen Larger Variants
**Model:** Qwen/Qwen2.5-32B-Instruct-Turbo
- **Hypothesis:** Qwen's guideline responsiveness (+9.6pp improvement) scales with size
- **Expected:** 55-60% accuracy (matches Llama 8B)

### 3. Optimize for Each Model
**Current:** Same prompt/config for all models
**Improvement:**
- Tune guideline length per model
- Adjust temperature per model
- Model-specific schema presentation

**Expected:** +2-5pp per model

### 4. Ensemble Approach
**Method:** Combine predictions from Llama 8B + GPT-OSS 20B
- Llama for guideline-heavy queries
- GPT-OSS for retry-heavy queries
- Vote when both agree

**Expected:** 60-65% accuracy

---

## FinSQL: Fine-Tuning Approach

In addition to MAGIC prompting techniques, we evaluated **FinSQL** - a fine-tuning approach combining:
1. **Schema Linking** (embedding-based)
2. **LoRA Fine-Tuning** (4 specialized plugins on 203 examples)
3. **Output Calibration** (self-consistency voting)

### FinSQL Results on Llama Models

| Model | Method | Accuracy | Training Data | Training Cost | Notes |
|-------|--------|----------|---------------|---------------|-------|
| Llama-3.1-8B | FinSQL | 10/21 (47.6%) | 203 examples | ~$0.30 | Baseline |
| Llama-3.1-70B | FinSQL | 9/21 (42.9%) | 203 examples | ~$0.50 | **-4.7pp worse** |

**Critical Finding:** **Larger model (70B) performed WORSE than smaller model (8B)** with same training data.

### Why 70B Underperformed

**Root Cause: Insufficient Training Data**
- Llama-8B: 203 examples ÷ 8B params ≈ **25 examples/billion parameters**
- Llama-70B: 203 examples ÷ 70B params ≈ **3 examples/billion parameters** ❌

**Evidence:**
- 70B lost on queries #10 and #13 (both correct for 8B)
- Hallucinated columns and used wrong datasets
- Underfitting due to data scarcity

**Cost-Benefit:**
- 70B: 67% more expensive, 3x slower training
- Result: **4.7pp worse accuracy**
- **ROI: Negative**

### FinSQL vs MAGIC Comparison

**On Llama-3.1-8B:**

| Approach | Method | Accuracy | Cost | Training Time |
|----------|--------|----------|------|---------------|
| **MAGIC** | Smart + Guidelines | **57.1%** ✓ | $0 training | 0 hours |
| **FinSQL** | LoRA fine-tuning | 47.6% | $0.30 | 1.5 hours |

**Key Insight:** **Prompting (MAGIC) outperforms fine-tuning (FinSQL)** when training data is limited (203 examples).

### Recommendations for FinSQL

**To match/exceed MAGIC with 70B:**
1. **Increase training data:** 500-1000 examples (2.5-5x current)
   - Expected improvement: +10-20pp
2. **Optimize LoRA config:** Increase rank from 16 to 32-64
   - Expected improvement: +3-7pp
3. **Hybrid approach:** Combine MAGIC guidelines with FinSQL
   - Expected: Best of both worlds

**Production Recommendation:** Use **MAGIC (57.1%)** over **FinSQL (47.6%)** for Llama-8B
- No training cost
- Better accuracy (+9.5pp)
- No maintenance overhead

---

## Conclusion

**Revolutionary Finding: Zero-Shot Baseline Changes Everything**

Before zero-shot testing, we thought:
- Llama 3.1 8B was best model (57.1%)
- Techniques always improve performance
- GPT-OSS 20B underperformed

**After zero-shot testing, we discovered:**
- **GPT-OSS 20B is best baseline** (57.1% zero-shot)
- **Llama 3.1 8B is worst baseline** (38.1% zero-shot)
- **Techniques are model-specific** (help Llama +19pp, hurt GPT-OSS -9pp)

**Key Findings:**

1. **Models have opposite responses to techniques**
   - Llama 8B: Zero-shot 38.1% → Guidelines 57.1% (+19.0pp) ✓
   - GPT-OSS 20B: Zero-shot 57.1% → Guidelines 47.6% (-9.5pp) ✗
   - **Same technique, opposite effects!**

2. **Baseline performance doesn't predict technique effectiveness**
   - Worst baseline (Llama) → Best with techniques
   - Best baseline (GPT-OSS) → Hurt by techniques
   - **Counter-intuitive but critical insight**

3. **Prompt engineering is model-specific**
   - Llama: Instruction-tuned, needs structure (+19pp)
   - GPT-OSS: Strong baseline, confused by complexity (-9pp)
   - Mistral/Qwen: Indifferent to techniques (0pp)

4. **Two paths to 57.1% accuracy**
   - **Path 1:** Llama 8B + engineering effort = 57.1%
   - **Path 2:** GPT-OSS 20B + zero-shot = 57.1%
   - **Cost:** Llama 60% cheaper ($0.18 vs $0.45/M tokens)

**Best Production Configurations (Both Achieve 57.1%):**

**Option 1: Engineering-Intensive**
- **Model:** meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
- **Method:** Smart MAGIC + Dataset-Specific Guidelines
- **Cost:** $0.18/M tokens
- **Requires:** Technique development + maintenance

**Option 2: Zero-Engineering**
- **Model:** openai/gpt-oss-20b
- **Method:** Zero-Shot (simple prompt)
- **Cost:** $0.45/M tokens (2.5× more expensive)
- **Requires:** Nothing (plug-and-play)

**Recommendation:**
1. **Best Overall:** **Llama 8B + MAGIC Guidelines** (57.1%, $0.18/M tokens, no training)
2. **Alternative:** **GPT-OSS 20B zero-shot** (57.1%, $0.45/M tokens, plug-and-play)
3. **Avoid:** FinSQL fine-tuning (47.6%, worse accuracy + training cost)

**Fine-Tuning Verdict:** With limited data (203 examples), **prompting outperforms fine-tuning** across all tested configurations.

---

## Appendix: Individual Model Reports

### A. Llama 3.1 70B Results

| Method | Accuracy | Change from Zero-Shot |
|--------|----------|----------------------|
| **Zero-Shot** | **10/21 (47.6%)** | Baseline |
| Smart MAGIC | **12/21 (57.1%)** | **+9.5pp ✓** |
| + Guidelines | **12/21 (57.1%)** | **+9.5pp ✓** |
| + Retry | **12/21 (57.1%)** | **+9.5pp ✓** |

**Queries Fixed vs 8B Zero-Shot:** #1, #6 (+2 queries)
**Best Improvement:** +9.5pp from zero-shot (all three techniques)
**Robustness:** All techniques achieve same 57.1% accuracy

---

### B. Llama 3.1 8B Results

| Method | Accuracy | Change from Zero-Shot |
|--------|----------|----------------------|
| **Zero-Shot** | **8/21 (38.1%)** | Baseline |
| Smart MAGIC | 11/21 (52.4%) | +14.3pp ✓ |
| + Guidelines | **12/21 (57.1%)** | **+19.0pp ✓✓** |
| + Retry | 10/21 (47.6%) | +9.5pp ✓ |

**Queries Fixed by Guidelines:** #7, #14
**Best Improvement:** +19.0pp from zero-shot with guidelines

---

### B. GPT-OSS 20B Results

| Method | Accuracy | Change from Zero-Shot |
|--------|----------|----------------------|
| **Zero-Shot** | **12/21 (57.1%)** | **Baseline (BEST)** |
| Smart MAGIC | 11/21 (52.4%) | -4.7pp ✗ |
| + Guidelines | 10/21 (47.6%) | **-9.5pp ✗✗** |
| + Retry | 11/21 (52.4%) | -4.7pp ✗ |

**Critical:** ALL techniques hurt performance
**Best config:** Zero-shot (no techniques needed)

---

### C. Mistral 7B Results

| Method | Accuracy | Change from Zero-Shot |
|--------|----------|----------------------|
| **Zero-Shot** | **10/21 (47.6%)** | **Baseline (BEST)** |
| Smart MAGIC | 9/21 (42.9%) | -4.7pp ✗ |
| + Guidelines | 10/21 (47.6%) | **0.0pp** |
| + Retry | 9/21 (42.9%) | -4.7pp ✗ |

**No net benefit:** Techniques don't improve baseline
**Best config:** Zero-shot or + Guidelines (both 47.6%)

---

### D. Qwen 2.5 7B Results

| Method | Accuracy | Change from Zero-Shot |
|--------|----------|----------------------|
| **Zero-Shot** | **9/21 (42.9%)** | **Baseline (BEST)** |
| Smart MAGIC | 7/21 (33.3%) | -9.6pp ✗ |
| + Guidelines | 9/21 (42.9%) | **0.0pp** |
| + Retry | 8/21 (38.1%) | -4.8pp ✗ |

**Largest recovery:** Guidelines restore -9.6pp loss from Smart MAGIC
**No net benefit:** Ends at baseline

---

**End of Report**
