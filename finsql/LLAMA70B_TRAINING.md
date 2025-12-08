# FinSQL LoRA Training for Llama-3.1-70B

## Overview

This document describes the process for training FinSQL LoRA adapters on **Llama-3.1-70B-Instruct-Reference**.

## Training Configuration

**Base Model**: `meta-llama/Meta-Llama-3.1-70B-Instruct-Reference`

**Training Data**: 203 examples (same as Llama-8B)
- `cot_training.jsonl`: 70 examples (Chain-of-Thought)
- `synonym_training.jsonl`: 49 examples (Robustness)
- `skeleton_training.jsonl`: 70 examples (Structure)
- `hard_training.jsonl`: 14 examples (Hard cases)

**LoRA Config**:
- Rank: 16
- Alpha: 32
- Dropout: 0.1
- Target modules: q_proj, v_proj
- Epochs: 10

**Plugins** (4 specialists):
1. `cot_specialist` - Chain-of-thought reasoning
2. `robustness_specialist` - Synonym/paraphrase handling
3. `structure_specialist` - SQL pattern recognition
4. `hard_cases_specialist` - Complex queries

## Method 1: Launch and Wait (Recommended)

This will launch all 4 jobs and wait for completion (~4-6 hours total).

```bash
cd /Users/othmane/University-Classes/Fall-2025/VIP-NLP/group-text-2-sql
./finsql/train_llama70b.sh
```

**What happens**:
1. Uploads 4 training files to TogetherAI
2. Creates 4 fine-tuning jobs
3. Waits for all jobs to complete
4. Saves plugin registry to `finsql/lora/plugin_registry_llama70b.json`

## Method 2: Launch Without Waiting

If you want to launch jobs and check back later:

```bash
cd /Users/othmane/University-Classes/Fall-2025/VIP-NLP/group-text-2-sql
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate VIP-NLP

python -m finsql.lora.train_lora \
    --model "meta-llama/Meta-Llama-3.1-70B-Instruct-Reference" \
    --model-suffix "llama70b" \
    --no-wait
```

**Check status later**:
```bash
python -m finsql.lora.train_lora \
    --check-status <job_id_1> <job_id_2> <job_id_3> <job_id_4>
```

## Method 3: Manual (Python)

```python
from finsql.lora.train_lora import LoRATrainer

# Initialize trainer with Llama-70B
trainer = LoRATrainer(
    base_model="meta-llama/Meta-Llama-3.1-70B-Instruct-Reference"
)

# Launch training
results = trainer.train_all_plugins(
    wait_for_completion=True,  # Set to False to launch and exit
    auto_save=True,
    model_suffix="llama70b"
)

# Check results
for plugin_name, info in results.items():
    print(f"{plugin_name}: {info['status']}")
    if info.get('model'):
        print(f"  Model: {info['model']}")
```

## Expected Output

After successful training, you'll have:

**Plugin Registry**: `finsql/lora/plugin_registry_llama70b.json`
```json
{
  "cot_specialist": "your_username/Meta-Llama-3.1-70B-Instruct-Reference-cot_specialist-xxxxx",
  "robustness_specialist": "your_username/Meta-Llama-3.1-70B-Instruct-Reference-robustness_specialist-xxxxx",
  "structure_specialist": "your_username/Meta-Llama-3.1-70B-Instruct-Reference-structure_specialist-xxxxx",
  "hard_cases_specialist": "your_username/Meta-Llama-3.1-70B-Instruct-Reference-hard_cases_specialist-xxxxx"
}
```

## Cost Estimate

- **Training**: ~$0.50 (4 plugins × ~$0.125 each)
- **Time**: 4-6 hours total (plugins train sequentially)
  - Each plugin: 60-90 minutes
  - Depends on TogetherAI queue

## Monitoring

**TogetherAI Dashboard**: https://api.together.xyz/playground/fine-tuning

Check:
- Job status (pending → running → succeeded)
- Training metrics
- Estimated completion time

## Troubleshooting

**Error: "Model not found"**
- Verify model name is exactly: `meta-llama/Meta-Llama-3.1-70B-Instruct-Reference`
- Check TogetherAI supports this model for fine-tuning

**Error: "Training file not found"**
- Ensure training data exists in `data/finsql/training_data/`
- Run `ls data/finsql/training_data/*.jsonl` to verify

**Job fails during training**
- Check TogetherAI dashboard for error message
- Verify training data format is correct
- Check account has sufficient credits

## Next Steps

After training completes:

1. **Verify registry**: `cat finsql/lora/plugin_registry_llama70b.json`
2. **Run inference**: Use `finsql/lora/inference.py` with Llama-70B plugins
3. **Evaluate**: Run full FinSQL pipeline on 21-query test set
4. **Compare**: Llama-8B (47.6%) vs Llama-70B (expected 55-65%)

## Comparison with Llama-8B

| Aspect | Llama-8B | Llama-70B |
|--------|----------|-----------|
| **Training data** | 203 examples | 203 examples (same) |
| **LoRA config** | rank=16, alpha=32 | rank=16, alpha=32 (same) |
| **Training time** | ~1.5 hours | ~4-6 hours |
| **Training cost** | ~$0.30 | ~$0.50 |
| **Baseline accuracy** | 47.6% | ? (to be evaluated) |
| **Expected improvement** | Baseline | +7-17pp (55-65%) |

**Hypothesis**: Larger model should generalize better with limited training data (203 examples).
