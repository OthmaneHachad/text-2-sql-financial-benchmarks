# FinSQL Implementation

**Fine-tuning with Schema Linking and LoRA**

This directory contains the FinSQL framework implementation: a Text-to-SQL approach combining BERT-based schema linking with LoRA fine-tuning.

## Overview

FinSQL uses a two-stage approach:

1. **Schema Linking**: BERT model predicts relevant tables for each query
2. **LoRA Fine-tuning**: Fine-tune LLM with LoRA on training data

**Key Features**:
- Lightweight schema linking (BERT-based, <1s inference)
- Parameter-efficient fine-tuning (LoRA with 4-bit quantization)
- Works with Llama models (8B and 70B tested)

**Results**:
- Llama 8B: 47.6% accuracy (10/21 queries)
- Llama 70B: 42.9% accuracy (9/21 queries)

---

## Quick Start

### 1. Train Schema Linker

Train BERT model on 203 training examples:

```bash
python train_schema_linker.py
```

**Duration**: ~15-20 minutes on CPU, ~5 minutes on GPU

**Output**:
- Model saved to `models/schema_linker/`
- Training metrics printed to console

### 2. Test Schema Linker

Verify schema linker works:

```bash
python test_schema_linker.py
```

**Expected output**: Top-5 predicted tables for sample questions.

### 3. Run Full FinSQL Inference

Fine-tune and evaluate on 21 test queries:

```bash
# Llama 8B
python full_finsql_inference.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo

# Llama 70B
python full_finsql_inference.py meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
```

**Duration**: ~30-45 minutes per model

**Output**: Results saved to `../data/results/finsql/`

---

## Implementation Details

### Schema Linking

**Model**: BERT-base-uncased fine-tuned for table relevance prediction

**Architecture**:
```
Question → BERT Encoder → Classification Head → Table Probabilities
```

**Training**:
- Dataset: 203 training examples
- Input: Question text
- Output: Binary relevance for each of 6 tables
- Loss: Binary cross-entropy
- Optimizer: AdamW with learning rate 2e-5
- Epochs: 3

**Inference**:
- Input: Natural language question
- Output: Top-5 most relevant tables
- Speed: <1 second per query

**Files**:
- `modules/schema_linker.py`: Schema linking model implementation
- `train_schema_linker.py`: Training script
- `test_schema_linker.py`: Testing script
- `models/schema_linker/`: Trained model checkpoints (not tracked)

### LoRA Fine-tuning

**Configuration**:
- Rank: 8
- Alpha: 16
- Dropout: 0.05
- Target modules: Query and value projection layers
- Quantization: 4-bit (bitsandbytes)

**Training**:
- Dataset: 203 training examples with linked schemas
- Batch size: 1 (gradient accumulation: 4)
- Epochs: 5
- Learning rate: 1e-4
- Optimizer: AdamW

**Inference**:
- Temperature: 0.3 (deterministic)
- Max tokens: 512
- Single sample generation

### Evaluation Metrics

- **Exact Match Accuracy**: Generated SQL must produce identical results to ground truth
- **Execution Success Rate**: Percentage of queries that execute without errors

---

## Results

### Performance by Model

| Model | Accuracy | Correct | Total | Execution Errors |
|-------|----------|---------|-------|------------------|
| Llama 8B | 47.6% | 10 | 21 | 3 |
| Llama 70B | 42.9% | 9 | 21 | 2 |

### Key Findings

1. **Data Scarcity Effects**: 203 examples insufficient for 70B model
2. **Schema Linking Helps**: Reduces table hallucination
3. **Underperforms MAGIC**: Smart MAGIC + Guidelines achieves 57.1%
4. **Model Size Paradox**: Larger model (70B) performs worse than 8B

### Error Analysis

**Common Errors**:
- Table confusion (gfs vs gem observations)
- Incorrect JOIN conditions
- Missing aggregations
- Hallucinated columns

**Schema Linking Successes**:
- Reduces full schema (6 tables) to top-5 relevant tables
- Eliminates hallucinated tables in most cases
- Improves prompt efficiency

---

## File Structure

```
finsql/
├── README.md                      # This file
├── config.py                      # Configuration settings
│
├── Schema Linking:
├── modules/
│   └── schema_linker.py           # BERT-based schema linker
├── train_schema_linker.py         # Train schema linker
├── test_schema_linker.py          # Test schema linker
│
├── FinSQL Inference:
├── full_finsql_inference.py       # Complete FinSQL pipeline
│
└── Models:
    └── schema_linker/             # Trained schema linker (not tracked)
```

---

## Usage Examples

### Train Schema Linker

```python
from finsql.train_schema_linker import train_schema_linker

# Train on 203 examples
train_schema_linker(
    train_file="../data/train/queries.json",
    output_dir="models/schema_linker",
    epochs=3,
    learning_rate=2e-5
)
```

### Use Trained Schema Linker

```python
from finsql.modules.schema_linker import SchemaLinker

# Load trained model
linker = SchemaLinker(model_path="models/schema_linker")

# Predict relevant tables
question = "Show GDP for United States in 2020"
top_tables = linker.predict(question, top_k=5)

print(f"Top tables: {top_tables}")
# Output: ['gem_observations', 'indicators', 'countries', 'time_periods', 'gfs_observations']
```

### Run Full FinSQL Pipeline

```python
from finsql.full_finsql_inference import run_finsql

# Run full pipeline
results = run_finsql(
    model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    test_file="../data/test/queries.json",
    schema_linker_path="models/schema_linker"
)

print(f"Accuracy: {results['accuracy']:.1f}%")
print(f"Correct: {results['correct']}/{results['total']}")
```

---

## Comparison with MAGIC

| Metric | FinSQL (8B) | MAGIC Baseline | Smart MAGIC + Guidelines |
|--------|-------------|----------------|--------------------------|
| Accuracy | 47.6% | 52.4% | **57.1%** |
| Schema Linking | ✓ BERT | ✗ None | ✓ BERT |
| Guidelines | ✗ None | ✓ 11 generic | ✓ Top-3 filtered |
| Fine-tuning | ✓ LoRA | ✗ None | ✗ None |
| Cost (21 queries) | ~$0.30 | $0.11 | $0.08 |

**Key Takeaway**: MAGIC's prompt-based approach outperforms FinSQL's fine-tuning approach on this dataset, likely due to data scarcity (203 examples insufficient for effective fine-tuning).

---

## Limitations

1. **Data Scarcity**: 203 examples too few for effective fine-tuning
   - Larger models (70B) perform worse than smaller (8B)
   - Model overfits to training patterns

2. **Model Constraints**: Only works with Llama models
   - LoRA fine-tuning requires model compatibility
   - Cannot evaluate on GPT-OSS, Mistral, or Qwen

3. **Schema Linking Accuracy**: BERT model makes errors
   - Sometimes misses relevant tables
   - Occasionally includes irrelevant tables

4. **Cost**: Fine-tuning adds overhead
   - Training time: ~30 minutes per model
   - API costs higher than prompt-based methods

---

## Future Improvements

1. **More Training Data**: Increase from 203 to 500+ examples
2. **Better Schema Linking**: Use cross-encoder instead of bi-encoder
3. **Hybrid Approach**: Combine LoRA with MAGIC guidelines
4. **Data Augmentation**: Synthetic example generation
5. **Model-Agnostic**: Adapt to work with non-Llama models

---

## Dependencies

Key packages:
- `transformers`: BERT and Llama models
- `peft`: LoRA implementation
- `bitsandbytes`: 4-bit quantization
- `torch`: PyTorch backend
- `sentence-transformers`: For embeddings

See `../requirements.txt` or `../environment.yml` for full dependencies.

---

## Troubleshooting

### CUDA Out of Memory

If you encounter OOM during fine-tuning:
```python
# Reduce batch size in full_finsql_inference.py
per_device_train_batch_size=1
gradient_accumulation_steps=8  # Increase from 4
```

### Schema Linker Not Found

Train the schema linker first:
```bash
python train_schema_linker.py
```

### Model Download Issues

If Together AI download fails:
```python
# Use HuggingFace directly
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3.1-8B-Instruct")
```

---

## References

- **FinSQL Paper**: "FinSQL: Model-Agnostic LLMs-based Text-to-SQL Framework for Financial Analysis"
- **LoRA**: "LoRA: Low-Rank Adaptation of Large Language Models"
- **PEFT Library**: https://github.com/huggingface/peft

---

**Last Updated**: December 2025
