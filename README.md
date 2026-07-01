# Suugaan — English → Somali Translation (QLoRA)

Fine-tunes **Gemma 3 1B-IT** on English-Somali parallel data using QLoRA (4-bit) via PEFT + TRL.

## Quickstart (cloud GPU)

```bash
pip install -r requirements.txt
huggingface-cli login       # Gemma is gated — accept licence at hf.co/google/gemma-3-1b-it
bash configs/train.example.sh
```

## Steps

| Script | What it does |
|---|---|
| `scripts/prepare_data.py` | Downloads OPUS-100 en-so, filters, splits into train/eval JSONL |
| `scripts/train.py` | QLoRA fine-tune (CUDA required) |
| `scripts/evaluate.py` | BLEU + chrF++ on eval set; works on CPU/MPS |
| `scripts/export.py` | Merges adapter into base model; optional GGUF export for Ollama |

## Hardware

Training requires a CUDA GPU with ≥ 16 GB VRAM (A100 recommended).  
Data prep and evaluation run on CPU or Apple Silicon (MPS).

## Dataset

[michsethowusu/english-somali_sentence-pairs_mt560](https://huggingface.co/datasets/michsethowusu/english-somali_sentence-pairs_mt560) — 161k parallel sentence pairs, CC-BY 4.0, derived from OPUS MT560.

## Model

Base: [`google/gemma-3-1b-it`](https://huggingface.co/google/gemma-3-1b-it)  
LoRA rank 16, alpha 32, targeting all linear projection layers.
