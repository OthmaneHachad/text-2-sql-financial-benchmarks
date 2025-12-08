# Enhanced MAGIC

**Multi-Agent Guideline-based Iterative Correction + Schema Linking + Self-Consistency**

This directory contains multiple MAGIC framework variants and comprehensive evaluation scripts for Text-to-SQL generation on economic data.

## Overview

We implement and evaluate 5 MAGIC-based approaches:

1. **Zero-shot Baseline**: No schema linking, no guidelines
2. **MAGIC Baseline**: Full schema + 11 generic guidelines
3. **Enhanced MAGIC**: Schema linking + top-3 filtered guidelines + voting
4. **Smart MAGIC**: Smart schema presentation + 11 guidelines
5. **Smart MAGIC + Guidelines**: Smart schema + filtered guidelines (best performer)

---

## Quick Start

### Test Sample Inference
```bash
python test_sample.py
```

Runs a sample question through the Smart MAGIC + Guidelines method.

### Evaluate Single Method
```bash
# Zero-shot baseline
python evaluate_zero_shot.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo

# MAGIC Baseline
python evaluate_magic_baseline.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo

# Enhanced MAGIC
python evaluate_enhanced_magic.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo

# Smart MAGIC
python evaluate_smart.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo

# Smart MAGIC + Guidelines
python evaluate_smart_guidelines.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

### Evaluate All Methods on One Model
```bash
python evaluate_all_methods.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

Runs all 5 methods on the specified model and compares results.


---

## Method Descriptions

### 1. Zero-shot Baseline (`zero_shot_baseline.py`)

**Configuration**:
- Full database schema (all 6 tables)
- No guidelines
- Single sample generation
- Temperature: 0.3

**Usage**:
```python
from enhanced_magic.zero_shot_baseline import ZeroShotBaseline

baseline = ZeroShotBaseline(model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
result = baseline.generate("Show GDP for United States in 2020")
print(result["sql"])
```

**Results**: 14.3-33.3% accuracy (varies by model)

---

### 2. MAGIC Baseline (`magic_baseline_inference.py`)

**Configuration**:
- Full database schema (all 6 tables)
- 11 generic MAGIC guidelines
- Single sample generation
- Temperature: 0.3

**Key Features**:
- Uses all 11 guidelines from MAGIC paper
- No schema linking (presents full schema)
- Deterministic generation (low temperature)

**Usage**:
```python
from enhanced_magic.magic_baseline_inference import MAGICBaseline

baseline = MAGICBaseline(model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
result = baseline.generate("Show GDP for United States in 2020")
print(result["sql"])
```

**Results**: 33.3-52.4% accuracy (best on Qwen 2.5 7B)

---

### 3. Enhanced MAGIC (`enhanced_inference.py`)

**Configuration**:
- Schema linking (top-5 relevant tables)
- Top-3 filtered guidelines per query
- Self-consistency voting (10 samples)
- Temperature: 0.7

**Key Features**:
- BERT-based schema linking reduces prompt size
- Pattern-based guideline filtering
- Majority voting across 10 samples

**Usage**:
```python
from enhanced_magic.enhanced_inference import EnhancedMAGIC

enhanced = EnhancedMAGIC(
    num_samples=10,
    use_full_guideline=False,  # Use top-3 filtered guidelines
    verbose=False
)
result = enhanced.generate("Show GDP for United States in 2020")
print(result["sql"])
```

**Results**: 28.6-57.1% accuracy (best on Llama 70B)

**Note**: Only Llama 70B benefits from Enhanced MAGIC. Most models perform worse due to negative interaction effects.

---

### 4. Smart MAGIC (`smart_inference.py`)

**Configuration**:
- Smart schema presentation (top-3 detailed, rest summary)
- 11 generic MAGIC guidelines
- Single sample generation
- Temperature: 0.3

**Key Features**:
- Balances schema detail and context length
- Top-3 tables shown with full columns
- Remaining tables shown as summaries
- Uses all 11 guidelines

**Usage**:
```python
from enhanced_magic.smart_inference import SmartMAGIC

smart = SmartMAGIC(model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
result = smart.generate("Show GDP for United States in 2020")
print(result["sql"])
```

**Results**: 38.1-52.4% accuracy (consistent across models)

---

### 5. Smart MAGIC + Guidelines (`smart_inference_guidelines.py`)

**Configuration**:
- Smart schema presentation
- Top-3 filtered guidelines per query
- Single sample generation
- Temperature: 0.3

**Key Features**:
- Best of smart schema + filtered guidelines
- Pattern-based guideline selection
- Deterministic generation

**Usage**:
```python
from enhanced_magic.smart_inference_guidelines import SmartMAGICGuidelines

smart_guidelines = SmartMAGICGuidelines(model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
result = smart_guidelines.generate("Show GDP for United States in 2020")
print(result["sql"])
```

**Results**: 42.9-57.1% accuracy (best overall method)

**Best Models**: Llama 8B/70B both achieve 57.1%

---

## Evaluation Scripts

### Single Method Evaluation

Each evaluation script runs 21 test queries and outputs:
- Accuracy (correct / total)
- Execution success rate
- Per-query results
- Token usage statistics

**Example**:
```bash
python evaluate_smart_guidelines.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

**Output**:
```
================================================================================
SMART MAGIC + GUIDELINES: meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
================================================================================
  Query 1/21: ✓
  Query 2/21: ✓
  ...
  Query 21/21: ✗

  Result: 12/21 (57.1%)
  Execution errors: 2
================================================================================

Results saved to: data/results/magic/meta_llama_Meta_Llama_3.1_8B_Instruct_Turbo_20251206_123456.json
```

### All Methods Evaluation

Runs all 5 methods on a single model:
```bash
python evaluate_all_methods.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

**Duration**: ~30-45 minutes per model

**Output**: Comparison table showing accuracy for each method.

**Note**: To evaluate all 5 models, run `evaluate_all_methods.py` for each model. Results will be saved to `data/results/model_comparison/`.

---

## Results Summary

| Method | Llama 8B | Llama 70B | GPT-OSS 20B | Mistral 7B | Qwen 2.5 7B |
|--------|----------|-----------|-------------|------------|-------------|
| Zero-shot | 28.6% | 33.3% | 23.8% | 28.6% | 14.3% |
| MAGIC Baseline | 33.3% | 47.6% | 38.1% | 38.1% | 52.4% |
| Enhanced MAGIC | 42.9% | 57.1% | 33.3% | 28.6% | 38.1% |
| Smart MAGIC | 52.4% | 52.4% | 38.1% | 42.9% | 42.9% |
| **Smart MAGIC + Guidelines** | **57.1%** | **57.1%** | 47.6% | 42.9% | 42.9% |

**Key Findings**:
1. Smart MAGIC + Guidelines achieves best overall performance
2. Schema linking helps most models (+10-20pp over zero-shot)
3. Filtered guidelines outperform all 11 guidelines
4. Enhanced MAGIC only benefits Llama 70B (negative interactions for others)
5. Qwen 2.5 7B benefits most from MAGIC Baseline (52.4%)

---

## Implementation Details

### Schema Linking
- BERT-based model: `bert-base-uncased`
- Trained on 203 examples
- Predicts top-5 relevant tables per query
- Inference: <1 second

### Guideline Filtering
- Pattern matching on question keywords
- Selects top-3 most relevant guidelines
- Reduces prompt size by ~60%

### Self-Consistency Voting
- Generates 10 samples at temperature 0.7
- Normalizes SQL (whitespace, capitalization)
- Majority vote selects final query

### Smart Schema Presentation
- Top-3 tables: Full details (columns, types, descriptions)
- Remaining tables: Summary (name, purpose, key columns)
- Reduces prompt size while maintaining context

---

## Cost Analysis

**Per Query Costs** (Llama 8B):

| Method | Input Tokens | Output Tokens | Cost |
|--------|--------------|---------------|------|
| Zero-shot | ~3,500 | ~80 | $0.0042 |
| MAGIC Baseline | ~4,200 | ~80 | $0.0051 |
| Enhanced MAGIC | ~2,800 × 10 | ~80 × 10 | $0.0340 |
| Smart MAGIC | ~3,200 | ~80 | $0.0039 |
| Smart MAGIC + Guidelines | ~3,000 | ~80 | $0.0037 |

**Full Evaluation** (21 queries):
- Zero-shot: $0.088
- MAGIC Baseline: $0.107
- Enhanced MAGIC: $0.714
- Smart MAGIC: $0.082
- Smart MAGIC + Guidelines: $0.078

---

## File Structure

```
enhanced_magic/
├── README.md                           # This file
├── config.py                           # Configuration settings
├── test_sample.py                      # Quick test script
│
├── Inference Engines:
├── zero_shot_baseline.py               # Zero-shot inference
├── magic_baseline_inference.py         # MAGIC Baseline
├── enhanced_inference.py               # Enhanced MAGIC
├── smart_inference.py                  # Smart MAGIC
├── smart_inference_guidelines.py       # Smart MAGIC + Guidelines
│
├── Evaluation Scripts:
├── evaluate_zero_shot.py               # Evaluate zero-shot
├── evaluate_magic_baseline.py          # Evaluate MAGIC Baseline
├── evaluate_enhanced_magic.py          # Evaluate Enhanced MAGIC
├── evaluate_smart.py                   # Evaluate Smart MAGIC
├── evaluate_smart_guidelines.py        # Evaluate Smart MAGIC + Guidelines
├── evaluate_all_methods.py             # Evaluate all 6 methods on one model
│
└── Utilities:
    ├── check_env.py                    # Check environment setup
    └── __init__.py                     # Package initialization
```

---

## Troubleshooting

### API Timeouts
If you encounter API timeouts (especially with Qwen model):
- Timeout set to 180 seconds in `magic_baseline_inference.py:60`
- Timeout set to 60 seconds in `enhanced_inference.py`
- Increase if needed: `Together(api_key=api_key, timeout=300.0)`

### Out of Memory
For Enhanced MAGIC with 10 samples:
- Reduce `num_samples` to 5
- Use smaller model (Llama 8B instead of 70B)

### Schema Linker Not Found
If schema linker model doesn't exist:
```bash
cd finsql
python train_schema_linker.py
```

This trains the schema linker needed for Enhanced MAGIC.

---

## References

- **MAGIC Paper**: [Multi-Agent Guideline-based Iterative Correction for Text-to-SQL](https://arxiv.org/abs/...)
- **FinSQL**: Fine-tuning with Schema Linking and LoRA
- **Together AI**: API documentation at https://docs.together.ai/

---

**Last Updated**: December 2025
