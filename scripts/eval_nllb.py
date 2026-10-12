#!/usr/bin/env python3
"""
Evaluate an NLLB translation model on English <-> Somali.

Unlike scripts/evaluate.py (which scores the shelved Gemma fine-tune), this
measures the model the API actually serves, on benchmarks that reflect how the
product is used.

Test sets:
  flores   FLORES-200 devtest, 1012 professionally translated sentences of
           modern news/wiki prose. The standard benchmark for this pair.
  eval     data/eval.jsonl, held out from the MT560 training corpus. ~39%
           Qur'anic scripture, so a high score here means little for practical
           text -- included to show the gap between domains.
  pontoon  Human-reviewed Common Voice UI strings from Mozilla Pontoon. Short
           and imperative; the closest thing here to product copy.

Examples:
  python scripts/eval_nllb.py --testset flores --limit 200
  python scripts/eval_nllb.py --testset flores --direction so-en
  python scripts/eval_nllb.py --model facebook/nllb-200-distilled-600M
"""

import argparse
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import sacrebleu
import torch
from tqdm import tqdm
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

LANG_CODES = {"en": "eng_Latn", "so": "som_Latn"}
REPO = Path(__file__).resolve().parent.parent


def detect_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_flores(direction: str) -> list[tuple[str, str]]:
    eng = (REPO / "data/flores/eng_Latn.devtest").read_text(encoding="utf-8").splitlines()
    som = (REPO / "data/flores/som_Latn.devtest").read_text(encoding="utf-8").splitlines()
    if not eng or not som:
        raise SystemExit("FLORES devtest missing -- see README for the download command")
    return list(zip(eng, som)) if direction == "en-so" else list(zip(som, eng))


def load_eval_jsonl(direction: str) -> list[tuple[str, str]]:
    path = REPO / "data/eval.jsonl"
    if not path.exists():
        raise SystemExit("data/eval.jsonl missing -- run scripts/prepare_data.py")
    pairs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        ex = json.loads(line)
        en = next(m["content"] for m in ex["messages"] if m["role"] == "user")
        so = next(m["content"] for m in ex["messages"] if m["role"] == "assistant")
        en = en.replace("Translate to Somali: ", "").strip()
        pairs.append((en, so) if direction == "en-so" else (so, en))
    return pairs


def load_pontoon(direction: str) -> list[tuple[str, str]]:
    path = REPO / "data/pontoon_common_voice_tm.xml"
    if not path.exists():
        raise SystemExit("Pontoon TM missing -- run scripts/prepare_data.py")
    root = ET.fromstring(path.read_bytes())
    pairs = []
    for tu in root.iter("tu"):
        en = so = None
        for tuv in tu.findall("tuv"):
            lang = tuv.get("{http://www.w3.org/XML/1998/namespace}lang", "")
            seg = (tuv.findtext("seg", "") or "").strip()
            if lang.startswith("en"):
                en = seg
            elif lang.startswith("so"):
                so = seg
        if en and so:
            pairs.append((en, so) if direction == "en-so" else (so, en))
    return pairs


LOADERS = {"flores": load_flores, "eval": load_eval_jsonl, "pontoon": load_pontoon}


def is_nllb(model_id: str) -> bool:
    return "nllb" in model_id.lower()


def translate_batch(model, tok, texts, src, tgt, device, beams, max_len, nllb=True):
    kwargs = {}
    if nllb:
        # NLLB is multilingual: the source language is set on the tokenizer and
        # the target is forced as the first generated token.
        tok.src_lang = LANG_CODES[src]
        kwargs["forced_bos_token_id"] = tok.convert_tokens_to_ids(LANG_CODES[tgt])
    enc = tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=max_len).to(device)
    with torch.no_grad():
        out = model.generate(**enc, max_length=max_len, num_beams=beams, **kwargs)
    return tok.batch_decode(out, skip_special_tokens=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="facebook/nllb-200-distilled-1.3B")
    ap.add_argument("--testset", default="flores", choices=list(LOADERS))
    ap.add_argument("--direction", default="en-so", choices=["en-so", "so-en"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--batch_size", type=int, default=8)
    ap.add_argument("--beams", type=int, default=4)
    ap.add_argument("--max_len", type=int, default=256)
    ap.add_argument("--device", default=None)
    ap.add_argument("--save", type=str, default=None, help="write hypotheses to this JSONL")
    args = ap.parse_args()

    src, tgt = args.direction.split("-")
    device = args.device or detect_device()
    nllb = is_nllb(args.model)
    if not nllb and args.direction != "en-so":
        raise SystemExit(f"{args.model} is a single-direction model; use --direction en-so")
    # fp16 on MPS still produces NaNs in some seq2seq stacks; fp32 is the safe default there.
    dtype = torch.float16 if device == "cuda" else torch.float32

    pairs = LOADERS[args.testset](args.direction)
    if args.limit:
        pairs = pairs[: args.limit]
    sources = [p[0] for p in pairs]
    refs = [p[1] for p in pairs]

    print(f"Loading {args.model} on {device} ({dtype})...")
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model, dtype=dtype).to(device)
    model.eval()

    print(f"{args.testset} / {args.direction} / {len(pairs)} sentences / beams={args.beams}")
    hyps: list[str] = []
    start = time.time()
    for i in tqdm(range(0, len(sources), args.batch_size), unit="batch"):
        hyps.extend(
            translate_batch(
                model, tok, sources[i : i + args.batch_size], src, tgt,
                device, args.beams, args.max_len, nllb=nllb,
            )
        )
    elapsed = time.time() - start

    bleu = sacrebleu.corpus_bleu(hyps, [refs])
    chrf = sacrebleu.CHRF(word_order=2).corpus_score(hyps, [refs])

    print(f"\n{'=' * 62}")
    print(f"  model     {args.model}")
    print(f"  testset   {args.testset} ({args.direction}, n={len(pairs)})")
    print(f"  BLEU      {bleu.score:.2f}")
    print(f"  chrF++    {chrf.score:.2f}")
    print(f"  speed     {len(pairs) / elapsed:.2f} sent/s ({elapsed:.0f}s total)")
    print(f"{'=' * 62}\n")

    for s, h, r in list(zip(sources, hyps, refs))[:5]:
        print(f"  SRC {s[:100]}")
        print(f"  HYP {h[:100]}")
        print(f"  REF {r[:100]}\n")

    if args.save:
        out = Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for s, h, r in zip(sources, hyps, refs):
                f.write(json.dumps({"src": s, "hyp": h, "ref": r}, ensure_ascii=False) + "\n")
        print(f"Wrote {len(hyps)} hypotheses to {out}")


if __name__ == "__main__":
    main()
