#!/usr/bin/env python3
"""
Fine-tune a translation model on the clean English-Somali corpus.

This is the replacement for scripts/train.py, which fine-tuned Gemma-3-1B on
Qur'an and Bible verses and scored BLEU 6.46. Two things change here:

  1. The base model already knows Somali, instead of a 1B English-centric model
     that had to learn it from 28k verses.
  2. The data is data/clean/, built by scripts/build_corpus.py from human
     translated civic, health, UI and talk corpora -- no scripture.

Training runs in both directions (en->so and so->en) from the same pairs, which
doubles the examples and keeps one model serving both ways, as the API expects.

The default base is google/madlad400-3b-mt: Apache-2.0, so the result can back a
paid product. NLLB-200 is CC-BY-NC-4.0 and cannot, however good it is -- a
fine-tune inherits the licence of its base.

LoRA is the default because MADLAD-3B is 2.94B parameters: a full fine-tune with
AdamW needs roughly 47GB of parameters, gradients and optimiser state before
activations. LoRA fits on a 24GB card.

  python scripts/train_mt.py                        # LoRA on MADLAD-3B
  python scripts/train_mt.py --full --optim adafactor   # needs ~40GB+
  python scripts/train_mt.py --model facebook/nllb-200-distilled-1.3B  # research only
"""

import argparse
import json
import math
from pathlib import Path

import sys

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
sys.path.insert(0, str(REPO))
import sugaan_mt  # noqa: E402

# LoRA attention projection names differ between architectures.
LORA_TARGETS = {
    "madlad": ["q", "k", "v", "o"],
    "nllb": ["q_proj", "k_proj", "v_proj", "out_proj"],
    "marian": ["q_proj", "k_proj", "v_proj", "out_proj"],
}


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

    def __init__(self, path: Path, tokenizer, max_len: int, family: str):
        self.rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.tok = tokenizer
        self.max_len = max_len
        self.family = family

    def __len__(self) -> int:
        return len(self.rows) * 2

    def __getitem__(self, i: int):
        row = self.rows[i // 2]
        src, tgt = ("en", "so") if i % 2 == 0 else ("so", "en")
        enc = sugaan_mt.train_pair(
            self.tok, row[src], row[tgt], src, tgt, self.family, self.max_len
        )
        return {k: enc[k] for k in ("input_ids", "attention_mask", "labels")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="google/madlad400-3b-mt")
    ap.add_argument("--data_dir", default="data/clean")
    ap.add_argument("--out_dir", default="outputs/mt-ft")
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

    family = sugaan_mt.detect_family(model, tok)
    warning = sugaan_mt.licence_warning(family)
    if warning:
        print(f"\n  !! {warning}\n")
    print(f"family={family}")

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
                target_modules=LORA_TARGETS[family],
            ),
        )
        model.print_trainable_parameters()

    data_dir = REPO / args.data_dir
    train_ds = BiDirectional(data_dir / "train.jsonl", tok, args.max_len, family)
    dev_ds = BiDirectional(data_dir / "dev.jsonl", tok, args.max_len, family)
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
    print(f"Evaluate with:\n  python scripts/eval_mt.py --model {out} --testset flores")


if __name__ == "__main__":
    main()
