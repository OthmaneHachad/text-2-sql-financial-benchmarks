# Text-to-SQL for Economic Data: MAGIC and FinSQL Frameworks

This repository contains the complete implementation and evaluation of two Text-to-SQL frameworks on a custom economic database: **MAGIC** (Multi-Agent Guideline-Integrated Prompting) and **FinSQL** (Fine-tuning with Schema Linking).

## Overview

We evaluate multiple approaches to Text-to-SQL generation on a unified economic database containing IMF Government Finance Statistics (GFS) and World Bank Global Economic Monitor (GEM) data:

- **MAGIC Framework**: Prompt-based approach with schema linking and guideline generation
- **FinSQL Framework**: Fine-tuning approach with LoRA and learned schema linking
- **Baseline Methods**: Zero-shot, MAGIC Baseline, Enhanced Magic, and other MAGIC variants
- **Multi-Model Evaluation**: 5 models tested across all methods

---

## Prerequisites

### 1. Environment Setup

**Option A: Using Conda (Recommended)**
```bash
conda env create -f environment.yml
conda activate VIP-NLP
```

**Option B: Using pip**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API Key Configuration

Create a `.env` file in the project root:
```bash
TOGETHER_API_KEY=your_together_ai_api_key_here
```

Get your API key from [Together AI](https://api.together.xyz/).

### 3. Database Setup

Generate the economic database:
```bash
cd database
python master_setup.py
```

This creates `database/economic_data.db`

**Note**: You need the raw data files:
- `Dataset Nov 9 2025 IMF GFS 10.0.0.csv` (in project root)
- `Gem Data Extraction/` folder with Excel files

See `database/README.md` for detailed setup instructions.

---

## Quick Start: Test Inference

Verify your setup works by running test inferences:

### Test MAGIC Framework
```bash
python enhanced_magic/test_sample.py
```

Expected output: SQL query generated for a sample question.

### Test FinSQL Framework
```bash
python finsql/test_schema_linker.py
```

Expected output: Schema linking predictions for sample questions.

### Test API Connection
```bash
python test_together_ai.py
```

Expected output: Successful API response from Together AI.

If all three tests pass, your environment is ready for full pipeline execution.

---

## Full Pipeline: Step-by-Step Tutorial

This section guides you through reproducing all experiments from scratch.

### Phase 1: Prepare Training and Test Data

The repository includes pre-split data:
- **Training**: `data/train/queries.json`
- **Testing**: `data/test/queries.json`

Verify data files exist:
```bash
ls data/train/queries.json data/test/queries.json
```

### Phase 2: Generate MAGIC Guidelines

Train the guideline generator by analyzing training data:

```bash
cd magic
python train_magic.py
```

**Output**:
- Guidelines saved to `data/final_guideline.txt`
- Intermediate guidelines in `data/guideline_*.txt`

**What it does**:
- Analyzes all training queries to extract common patterns
- Generates 9 generic SQL generation guidelines
- Uses iterative refinement across training examples

### Phase 3: Evaluate All Methods

#### 4.1 Evaluate MAGIC Framework (All Variants)

Run all MAGIC variants on Llama 8B:
```bash
cd enhanced_magic
python evaluate_all_methods.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```


**What it evaluates**:
- Zero-shot (no schema linking, no guidelines)
- MAGIC Baseline (full schema + 11 guidelines)
- Enhanced MAGIC (schema linking + top-3 guidelines + voting)
- Smart MAGIC (smart schema + 11 guidelines)
- Smart MAGIC + Guidelines (best performer)
- Smart MAGIC + Retry (with error correction)

**Output**: Results saved to `data/results/magic/`

To evaluate other models:
```bash
# Llama 70B
python evaluate_all_methods.py meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo

# GPT-OSS 20B
python evaluate_all_methods.py openai/gpt-oss-20b

# Mistral 7B
python evaluate_all_methods.py mistralai/Mistral-7B-Instruct-v0.3

# Qwen 2.5 7B
python evaluate_all_methods.py Qwen/Qwen2.5-7B-Instruct-Turbo
```

#### 4.2 Evaluate FinSQL Framework

Run FinSQL inference on Llama 8B (or 70B):
```bash
cd finsql
python full_finsql_inference.py meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

**What it does**:
- Uses trained schema linker to predict top-3 relevant tables
- Fine-tunes Llama 8B with LoRA on training data
- Evaluates on 21 test queries

**Output**: Results saved to `data/results/finsql/`

To evaluate Llama 70B:
```bash
python full_finsql_inference.py meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
```

**Note**: FinSQL only works on Llama models due to fine-tuning constraints.

**Note**: To evaluate all models, simply run `evaluate_all_methods.py` for each model listed above.

### Phase 5: Analyze Results

After all evaluations complete, results are saved under `data/results/`

Each result file contains:
- Per-query correctness
- Execution success rates
- Token usage statistics
- Generated SQL queries

View consolidated results:
```bash
cat data/MODEL_COMPARISON_REPORT.md
```

---

## Project Structure

```
.
├── database/              # Database setup and data import
│   ├── database_setup.py
│   ├── import_gfs_data.py
│   ├── import_gem_data.py
│   ├── master_setup.py
│   └── economic_data.db   # Generated database (not tracked)
│
├── data/                  # Training/test data and results
│   ├── train/
│   │   └── queries.json   # 203 training examples
│   ├── test/
│   │   └── queries.json   # 21 test examples
│   └── results/           # Evaluation results (not tracked)
│
├── magic/                 # Original MAGIC implementation
│   ├── train_magic.py     # Guideline generator training
│   ├── infer_magic.py     # MAGIC inference
│   └── config.py
│
├── enhanced_magic/        # Enhanced MAGIC variants
│   ├── evaluate_all_methods.py       # Evaluate all MAGIC variants
│   ├── run_all_ablations.py          # Run ablation study
│   ├── zero_shot_baseline.py         # Zero-shot inference
│   ├── magic_baseline_inference.py   # MAGIC Baseline
│   ├── enhanced_inference.py         # Enhanced MAGIC
│   ├── smart_inference.py            # Smart MAGIC
│   └── smart_inference_guidelines.py # Smart MAGIC + Guidelines
│
├── finsql/                # FinSQL implementation
│   ├── train_schema_linker.py        # Train BERT schema linker
│   ├── full_finsql_inference.py      # FinSQL with LoRA fine-tuning
│   └── modules/
│       └── schema_linker.py          # Schema linking model
│
├── shared/                # Shared utilities
│   ├── database.py        # Database utilities
│   ├── data_loader.py     # Data loading utilities
│   └── together_client.py # Together AI client
│
├── environment.yml        # Conda environment
├── requirements.txt       # Pip requirements
└── README.md             # This file
```

## Folder-Specific Documentation

Each module has detailed documentation:

- `database/README.md` - Database setup and regeneration
- `enhanced_magic/README.md` - MAGIC evaluation scripts
- `finsql/README.md` - FinSQL training and evaluation
- `data/README.md` - Data structure and regeneration

---

## Citation

If you use this code or data, please cite:

```bibtex
@misc{economic-text2sql-2025,
  title={Text-to-SQL for Finance: Evaluating MAGIC and FinSQL Frameworks},
  author={Othmane Hachad},
  year={2025},
  url={https://github.com/OthmaneHachad/text-2-sql-financial-benchmarks}
}
```

---

## License

- **Code**: MIT License
- **Data Sources**:
  - IMF GFS: IMF Copyright and Usage
  - World Bank GEM: Creative Commons Attribution 4.0

---

**Last Updated**: December 2025
