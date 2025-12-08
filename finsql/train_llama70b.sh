#!/bin/bash
# Train FinSQL LoRA plugins for Llama-3.1-70B

echo "================================================================================"
echo "FINSQL LORA TRAINING: Llama-3.1-70B"
echo "================================================================================"
echo ""
echo "Model: meta-llama/Meta-Llama-3.1-70B-Instruct-Reference"
echo "Training data: 203 examples (4 plugins)"
echo "Registry: finsql/lora/plugin_registry_llama70b.json"
echo ""
echo "WARNING: This will launch 4 fine-tuning jobs (~1-2 hours each)"
echo "Estimated cost: ~$0.50"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Activate conda environment
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate VIP-NLP

# Launch training
cd "$(dirname "$0")/.."
python -m finsql.lora.train_lora \
    --model "meta-llama/Meta-Llama-3.1-70B-Instruct-Reference" \
    --model-suffix "llama70b"

echo ""
echo "================================================================================"
echo "TRAINING JOBS LAUNCHED"
echo "================================================================================"
echo ""
echo "Monitor progress on TogetherAI dashboard:"
echo "https://api.together.xyz/playground/fine-tuning"
echo ""
echo "Jobs will save to: finsql/lora/plugin_registry_llama70b.json"
echo ""
