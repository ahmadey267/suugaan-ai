#!/usr/bin/env python3
"""
Prepare English-Somali parallel data for QLoRA fine-tuning.
Outputs data/train.jsonl and data/eval.jsonl in Gemma-3 chat-template format.
"""

import argparse
import json
import random
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm


def format_example(en: str, so: str) -> dict:
    return {
        "messages": [
            {"role": "user", "content": f"Translate to Somali: {en.strip()}"},
            {"role": "assistant", "content": so.strip()},
        ]
    }


def clean_text(text: str) -> str:
    """Remove OPUS tokenization artefacts like 'word @-@ word' → 'word-word'."""
    import re
    text = re.sub(r' @-@ ', '-', text)
    text = re.sub(r' @,@ ', ',', text)
    return text.strip()


def is_valid_pair(en: str, so: str, min_len: int = 5, max_len: int = 400) -> bool:
    en, so = en.strip(), so.strip()
    if not en or not so:
        return False
    if len(en) < min_len or len(so) < min_len:
        return False
    if len(en) > max_len or len(so) > max_len:
        return False
    return True


def is_valid_pair_langid(en: str, so: str) -> bool:
    import langid
    en_lang, _ = langid.classify(en)
    # langid struggles with Somali — accept 'so' or adjacent false positives ('sw', 'ha')
    so_lang, _ = langid.classify(so)
    return en_lang == "en" and so_lang in ("so", "sw", "ha", "om")


def load_en_so(max_bulk: int):
    """Load michsethowusu/english-somali_sentence-pairs_mt560 (161k pairs, CC-BY 4.0)."""
    print("  Loading michsethowusu/english-somali_sentence-pairs_mt560...")
    ds = load_dataset("michsethowusu/english-somali_sentence-pairs_mt560")
    pairs = []
    for split in ("train", "validation", "test"):
        if split not in ds:
            continue
        for ex in ds[split]:
            en = clean_text(ex.get("eng", ""))
            so = clean_text(ex.get("som", ""))
            if en and so:
                pairs.append((en, so))
            if len(pairs) >= max_bulk:
                break
        if len(pairs) >= max_bulk:
            break
    print(f"  Loaded {len(pairs)} pairs")
    return pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_bulk", type=int, default=50000)
    parser.add_argument("--eval_size", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out_dir", type=str, default="data")
    parser.add_argument("--no_langid", action="store_true",
                        help="Skip langid filtering (faster, less clean)")
    args = parser.parse_args()

    random.seed(args.seed)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(exist_ok=True)

    print(f"Loading en-so dataset (cap {args.max_bulk} pairs)...")
    pairs = load_en_so(args.max_bulk)
    print(f"Raw pairs: {len(pairs)}")

    print("Filtering by length...")
    pairs = [(en, so) for en, so in pairs if is_valid_pair(en, so)]
    print(f"After length filter: {len(pairs)}")

    if not args.no_langid:
        print("Filtering with langid (slow — use --no_langid to skip)...")
        pairs = [(en, so) for en, so in tqdm(pairs) if is_valid_pair_langid(en, so)]
        print(f"After langid filter: {len(pairs)}")

    random.shuffle(pairs)

    eval_size = min(args.eval_size, len(pairs) // 10)
    eval_pairs = pairs[:eval_size]
    train_pairs = pairs[eval_size:]

    # Prevent eval leakage
    eval_en = {en for en, _ in eval_pairs}
    train_pairs = [(en, so) for en, so in train_pairs if en not in eval_en]

    print(f"Train: {len(train_pairs)} | Eval: {len(eval_pairs)}")

    train_path = out_dir / "train.jsonl"
    eval_path = out_dir / "eval.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for en, so in train_pairs:
            f.write(json.dumps(format_example(en, so), ensure_ascii=False) + "\n")

    with open(eval_path, "w", encoding="utf-8") as f:
        for en, so in eval_pairs:
            f.write(json.dumps(format_example(en, so), ensure_ascii=False) + "\n")

    print(f"\nWrote: {train_path}, {eval_path}")

    print("\n--- 3 sample train examples ---")
    with open(train_path) as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            ex = json.loads(line)
            print(f"  EN: {ex['messages'][0]['content']}")
            print(f"  SO: {ex['messages'][1]['content']}")
            print()


if __name__ == "__main__":
    main()
