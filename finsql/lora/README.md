# FinSQL LoRA Plugins

This directory contains LoRA fine-tuning code and plugin registry for FinSQL.

## Plugin Registry

`plugin_registry.json` contains TogetherAI model IDs for the 4 specialized LoRA plugins:
- `cot_specialist` - Chain-of-thought reasoning
- `robustness_specialist` - Synonym/paraphrase handling
- `structure_specialist` - SQL pattern recognition
- `hard_cases_specialist` - Complex query handling

### Privacy Note

**These model IDs are safe to commit publicly** because:
1. TogetherAI LoRA models are private by default (account-specific)
2. Model IDs follow format: `username_suffix/model-name-hash`
3. They only work with the owner's API key
4. Others cannot access or use these models without authentication

The IDs are committed for reproducibility and to allow easy re-running of experiments.

## Training

Train all plugins:
```bash
python finsql/lora/train_lora.py --plugin cot_specialist --epochs 10
python finsql/lora/train_lora.py --plugin robustness_specialist --epochs 10
python finsql/lora/train_lora.py --plugin structure_specialist --epochs 10
python finsql/lora/train_lora.py --plugin hard_cases_specialist --epochs 10
```

## Inference

```python
from finsql.lora.inference import LoRAInference

inferencer = LoRAInference()
sql = inferencer.generate(
    question="Show GDP for United States",
    schema="...",
    plugin_name="cot_specialist",
    num_samples=20
)
```
