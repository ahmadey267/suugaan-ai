#!/usr/bin/env python3
"""
Fine-tune NLLB-200 on the clean English-Somali corpus.

This is the replacement for scripts/train.py, which fine-tuned Gemma-3-1B on
Qur'an and Bible verses and scored BLEU 6.46. Two things change here:

  1. The base model is NLLB-200, which already knows Somali, instead of a 1B
     English-centric model that had to learn it from 28k verses.
  2. The data is data/clean/, built by scripts/build_corpus.py from human
     translated civic, health, UI and talk corpora -- no scripture.

Training runs in both directions (en->so and so->en) from the same pairs, which
doubles the examples and keeps one model serving both ways, as the API expects.

LoRA is the default because a full fine-tune of even the 600M model needs ~10GB
of optimiser state, which does not fit alongside anything else on a laptop.
Pass --full on a real GPU.

  python scripts/train_nllb.py                      # LoRA, 600M, MPS or CUDA
  python scripts/train_nllb.py --full --epochs 3    # full fine-tune (GPU)
  python scripts/train_nllb.py --model facebook/nllb-200-distilled-1.3B
"""

import argparse
import json
import math
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

REPO = Path(__file__).resolve().parent.parent
LANG = {"en": "eng_Latn", "so": "som_Latn"}


def detect_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class BiDirectional(Dataset):
    """Each pair yields two examples: en->so and so->en.

    NLLB needs the language of both sides at tokenisation time, so the tokenizer
    is reconfigured per item rather than once for the whole set.
    """

    def __init__(self, path: Path, tokenizer, max_len: int):
        self.rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.tok = tokenizer
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.rows) * 2

    def __getitem__(self, i: int):
        row = self.rows[i // 2]
        src, tgt = ("en", "so") if i % 2 == 0 else ("so", "en")
        self.tok.src_lang = LANG[src]
        self.tok.tgt_lang = LANG[tgt]
        enc = self.tok(
            row[src],
            text_target=row[tgt],
            max_length=self.max_len,
            truncation=True,
        )
        return {k: enc[k] for k in ("input_ids", "attention_mask", "labels")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="facebook/nllb-200-distilled-600M")
    ap.add_argument("--data_dir", default="data/clean")
    ap.add_argument("--out_dir", default="outputs/nllb-ft")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--batch_size", type=int, default=8)
    ap.add_argument("--grad_accum", type=int, default=4)
    ap.add_argument("--lr", type=float, default=None, help="default: 1e-4 LoRA, 3e-5 full")
    ap.add_argument("--max_len", type=int, default=128)
    ap.add_argument("--full", action="store_true", help="full fine-tune instead of LoRA")
    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--warmup_ratio", type=float, default=0.03)
    ap.add_argument("--save_steps", type=int, default=500)
    ap.add_argument("--max_steps", type=int, default=-1, help="stop early; -1 runs full epochs")
    ap.add_argument("--optim", default="adamw_torch",
                    help="adafactor or adamw_bnb_8bit for a full 1.3B fine-tune on a 24GB card")
    ap.add_argument("--save_strategy", default="steps", choices=["steps", "no"],
                    help="'no' skips checkpoints; torch.save of optimiser state can fail on MPS")
    args = ap.parse_args()

    device = detect_device()
    lr = args.lr or (3e-5 if args.full else 1e-4)
    print(f"device={device}  model={args.model}  mode={'full' if args.full else 'LoRA'}  lr={lr}")

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)

    if not args.full:
        from peft import LoraConfig, get_peft_model

        # Attention projections only: the FFN adds parameters without much gain
        # on a corpus this size, and the point is to adapt register, not to
        # teach the model Somali from scratch.
        model = get_peft_model(
            model,
            LoraConfig(
                r=args.lora_r,
                lora_alpha=args.lora_r * 2,
                lora_dropout=0.05,
                bias="none",
                task_type="SEQ_2_SEQ_LM",
                target_modules=["q_proj", "k_proj", "v_proj", "out_proj"],
            ),
        )
        model.print_trainable_parameters()

    data_dir = REPO / args.data_dir
    train_ds = BiDirectional(data_dir / "train.jsonl", tok, args.max_len)
    dev_ds = BiDirectional(data_dir / "dev.jsonl", tok, args.max_len)
    print(f"train={len(train_ds)} examples (both directions)  dev={len(dev_ds)}")

    steps_per_epoch = math.ceil(len(train_ds) / (args.batch_size * args.grad_accum))
    print(f"~{steps_per_epoch} optimiser steps per epoch")

    targs = Seq2SeqTrainingArguments(
        output_dir=str(REPO / args.out_dir),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=lr,
        warmup_ratio=args.warmup_ratio,
        lr_scheduler_type="cosine",
        logging_steps=25,
        save_strategy=args.save_strategy,
        save_steps=args.save_steps,
        optim=args.optim,
        save_total_limit=2,
        eval_strategy="epoch",
        # fp16 is CUDA-only here: MPS autocast still produces NaNs in this stack.
        fp16=(device == "cuda"),
        report_to=[],
        remove_unused_columns=False,
        dataloader_num_workers=0,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=dev_ds,
        data_collator=DataCollatorForSeq2Seq(tok, model=model, label_pad_token_id=-100),
    )

    trainer.train()

    out = REPO / args.out_dir / "final"
    out.mkdir(parents=True, exist_ok=True)
    if args.full:
        model.save_pretrained(out)
    else:
        # Merge so the result loads as a plain NLLB model and the API needs no
        # PEFT dependency at serving time.
        model.merge_and_unload().save_pretrained(out)
    tok.save_pretrained(out)
    print(f"\nSaved to {out}")
    print(f"Evaluate with:\n  python scripts/eval_nllb.py --model {out} --testset flores")


if __name__ == "__main__":
    main()
