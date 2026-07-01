#!/usr/bin/env python3
"""
Evaluate a fine-tuned (or base) model on eval.jsonl.
Reports BLEU and chrF++ scores with sample translations.
Works on CPU, MPS (Apple Silicon), and CUDA.
"""

import argparse
import json
from pathlib import Path

import sacrebleu
import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "google/gemma-3-1b-it"


def detect_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_eval_pairs(eval_file: Path, limit: int | None = None):
    pairs = []
    with open(eval_file, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            ex = json.loads(line)
            user_msg = next(m["content"] for m in ex["messages"] if m["role"] == "user")
            ref = next(m["content"] for m in ex["messages"] if m["role"] == "assistant")
            pairs.append((user_msg, ref))
    return pairs


def generate(model, tokenizer, prompt: str, device: str, max_new_tokens: int = 200) -> str:
    messages = [{"role": "user", "content": prompt}]
    input_ids = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(device)
    with torch.no_grad():
        out = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )
    new_tokens = out[0][input_ids.shape[-1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", type=str, default=None,
                        help="Path to fine-tuned checkpoint. Omit to evaluate the base model.")
    parser.add_argument("--base_model", type=str, default=MODEL_ID)
    parser.add_argument("--eval_file", type=str, default="data/eval.jsonl")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--show_samples", type=int, default=5)
    parser.add_argument("--lora", action="store_true",
                        help="model_dir is a LoRA adapter directory (loads and merges on the fly)")
    args = parser.parse_args()

    device = detect_device()
    print(f"Device: {device}")

    model_path = args.model_dir or args.base_model
    print(f"Loading model: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16 if device != "cpu" else torch.float32

    if args.lora:
        from peft import PeftModel
        base = AutoModelForCausalLM.from_pretrained(
            args.base_model, torch_dtype=dtype, device_map=device
        )
        model = PeftModel.from_pretrained(base, args.model_dir)
        model = model.merge_and_unload()
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype=dtype, device_map=device
        )

    model.eval()

    eval_file = Path(args.eval_file)
    if not eval_file.exists():
        raise FileNotFoundError(f"{eval_file} not found — run prepare_data.py first")

    pairs = load_eval_pairs(eval_file, args.limit)
    print(f"Evaluating on {len(pairs)} examples...")

    hypotheses, references = [], []
    for prompt, ref in tqdm(pairs):
        hyp = generate(model, tokenizer, prompt, device=device)
        hypotheses.append(hyp)
        references.append(ref)

    bleu = sacrebleu.corpus_bleu(hypotheses, [references])
    chrf = sacrebleu.corpus_chrf(hypotheses, [references], beta=2)

    print(f"\n{'='*40}")
    print(f"BLEU:   {bleu.score:.2f}")
    print(f"chrF++: {chrf.score:.2f}")
    print(f"{'='*40}\n")

    n = min(args.show_samples, len(hypotheses))
    print(f"--- {n} sample translations ---")
    for i in range(n):
        print(f"\n[{i+1}] {pairs[i][0]}")
        print(f"    REF: {references[i]}")
        print(f"    HYP: {hypotheses[i]}")


if __name__ == "__main__":
    main()
