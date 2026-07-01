#!/bin/bash
# Full training run — paste this into a cloud GPU shell (A100 40GB recommended).
# Prerequisites:
#   1. pip install -r requirements.txt
#   2. hf auth login           (Gemma is gated — accept licence at hf.co/google/gemma-3-1b-it)
#      (old CLI was huggingface-cli login; the new one is: hf auth login)
set -e

cd "$(dirname "$0")/.."

# 1. Build dataset
python scripts/prepare_data.py \
  --max_bulk 100000 \
  --eval_size 1000 \
  --out_dir data

# 2. Train
python scripts/train.py \
  --data_dir data \
  --output_dir outputs/checkpoint \
  --epochs 3 \
  --batch_size 8 \
  --grad_accum 4 \
  --lr 2e-4 \
  --max_seq_len 256

# 3. Evaluate adapter
python scripts/evaluate.py \
  --model_dir outputs/checkpoint \
  --base_model google/gemma-3-1b-it \
  --eval_file data/eval.jsonl \
  --limit 500 \
  --lora

# 4. Merge + export GGUF (optional — needs llama.cpp cloned to ./llama.cpp)
# python scripts/export.py \
#   --adapter_dir outputs/checkpoint \
#   --output_dir outputs/merged \
#   --gguf
