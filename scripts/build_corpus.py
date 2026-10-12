#!/usr/bin/env python3
"""
Build a clean English-Somali parallel corpus for fine-tuning NLLB.

Why this exists
---------------
The original corpus (michsethowusu/english-somali_sentence-pairs_mt560) is
Tanzil + bible-uedin: 93,844 Qur'an verses and 62,195 Bible verses out of
161,865 pairs. It is ~96% scripture, and 91% of it carries Moses-style
pre-tokenized punctuation ("the word , and"). Training on it teaches archaic
register and spaced punctuation -- which is exactly what the shelved Gemma
fine-tune produced.

This script assembles the human-translated, non-scriptural en-so corpora on
OPUS instead:

  infopankki     Finnish government information for immigrants (civic, practical)
  translatewiki  software UI strings
  tico-19        health / COVID guidance, professionally translated
  TED2020        talk subtitles
  wikimedia      encyclopedic prose
  pontoon        Mozilla Common Voice UI strings (human-reviewed)

All are detokenized modern text with no scripture. They are small, so filtering
is conservative: the goal is a corpus that is clean rather than large.

Usage:
  python scripts/build_corpus.py                  # writes data/clean/{train,dev}.jsonl
  python scripts/build_corpus.py --langid         # add langid filtering (slow)
  python scripts/build_corpus.py --report_only    # inspect composition, write nothing
"""

import argparse
import json
import random
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from io import BytesIO
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / "data" / "opus"

# corpus -> OPUS moses-format zip. Versions pinned; bump deliberately.
SOURCES = {
    "infopankki": "https://object.pouta.csc.fi/OPUS-infopankki/v1/moses/en-so.txt.zip",
    "translatewiki": "https://object.pouta.csc.fi/OPUS-translatewiki/v2026-07-01/moses/en-so.txt.zip",
    "tico-19": "https://object.pouta.csc.fi/OPUS-tico-19/v2020-10-28/moses/en-so.txt.zip",
    "TED2020": "https://object.pouta.csc.fi/OPUS-TED2020/v1/moses/en-so.txt.zip",
    "wikimedia": "https://object.pouta.csc.fi/OPUS-wikimedia/v20260327/moses/en-so.txt.zip",
}
PONTOON_TMX_URL = "https://pontoon.mozilla.org/translation-memory/so.common-voice.tmx"

# Placeholder / markup noise, mostly from translatewiki and wikimedia.
MARKUP = re.compile(r"(\$\d|\{\{|\}\}|<[a-z/][^>]*>|\[\[|\]\]|&[a-z]+;|%\(?\w+\)?[sd])")
CITATION = re.compile(r"\[\d+\]")
# Belt and braces: these corpora test clean, but a stray verse should not slip in.
SCRIPTURE = re.compile(
    r"\b(thou|thee|thy|saith|unto|Yahweh|LORD God|Pharaoh|apostle|disbelievers|"
    r"Hereafter|Rabbiga|Eebe|Ilaahay baa|nebi)\b",
    re.I,
)


def norm(s: str) -> str:
    """Normalisation used only for dedup keys, never for output."""
    s = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"\s+", " ", s).strip()


def fetch_zip(name: str, url: str) -> tuple[list[str], list[str]]:
    CACHE.mkdir(parents=True, exist_ok=True)
    local = CACHE / f"{name}.zip"
    if not local.exists():
        print(f"  downloading {name}...")
        with urllib.request.urlopen(url) as r:
            local.write_bytes(r.read())
    with zipfile.ZipFile(BytesIO(local.read_bytes())) as z:
        en_name = next(n for n in z.namelist() if n.endswith(".en"))
        so_name = next(n for n in z.namelist() if n.endswith(".so"))
        en = z.read(en_name).decode("utf-8", "replace").splitlines()
        so = z.read(so_name).decode("utf-8", "replace").splitlines()
    return en, so


def fetch_pontoon() -> tuple[list[str], list[str]]:
    cache = REPO / "data" / "pontoon_common_voice_tm.xml"
    if not cache.exists():
        print("  downloading pontoon...")
        with urllib.request.urlopen(PONTOON_TMX_URL) as r:
            cache.write_bytes(r.read())
    root = ET.fromstring(cache.read_bytes())
    en_out, so_out = [], []
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
            en_out.append(en)
            so_out.append(so)
    return en_out, so_out


def keep(en: str, so: str, max_words: int, drop_markup: bool) -> str | None:
    """Return a rejection reason, or None to keep the pair."""
    en, so = en.strip(), so.strip()
    if not en or not so:
        return "empty"
    if en == so:
        return "identical"  # untranslated passthrough
    en_w, so_w = len(en.split()), len(so.split())
    if en_w < 2 or so_w < 2:
        return "too_short"
    if en_w > max_words or so_w > max_words:
        return "too_long"
    # Character-length ratio catches misalignment; Somali runs a little longer
    # than English, so the window is deliberately asymmetric.
    ratio = len(so) / max(len(en), 1)
    if not 0.5 <= ratio <= 2.2:
        return "length_ratio"
    if SCRIPTURE.search(en) or SCRIPTURE.search(so):
        return "scripture"
    if drop_markup and (MARKUP.search(en) or MARKUP.search(so)):
        return "markup"
    # Citation markers must match, or the pair is misaligned (wikimedia).
    if CITATION.findall(en) != CITATION.findall(so):
        return "citation_mismatch"
    if not re.search(r"[a-zA-Z]", en) or not re.search(r"[a-zA-Z]", so):
        return "no_letters"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="data/clean")
    ap.add_argument("--dev_size", type=int, default=1000)
    ap.add_argument("--max_words", type=int, default=120)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--keep_markup", action="store_true", help="keep UI placeholder strings")
    ap.add_argument("--langid", action="store_true", help="langid filter (slow, ~1k pairs/s)")
    ap.add_argument("--report_only", action="store_true")
    args = ap.parse_args()

    random.seed(args.seed)
    rejects: Counter = Counter()
    per_corpus: dict[str, int] = {}
    seen: set[tuple[str, str]] = set()
    seen_en: Counter = Counter()
    pairs: list[tuple[str, str, str]] = []  # (en, so, corpus)

    loaders = [(n, lambda u=u, n=n: fetch_zip(n, u)) for n, u in SOURCES.items()]
    loaders.append(("pontoon", fetch_pontoon))

    for name, load in loaders:
        en_lines, so_lines = load()
        kept = 0
        for en, so in zip(en_lines, so_lines):
            reason = keep(en, so, args.max_words, drop_markup=not args.keep_markup)
            if reason:
                rejects[reason] += 1
                continue
            en, so = en.strip(), so.strip()
            key = (norm(en), norm(so))
            if key in seen:
                rejects["duplicate"] += 1
                continue
            # One English source can legitimately have variant translations, but
            # more than two is usually boilerplate churn (infopankki nav links).
            if seen_en[norm(en)] >= 2:
                rejects["repeated_source"] += 1
                continue
            seen.add(key)
            seen_en[norm(en)] += 1
            pairs.append((en, so, name))
            kept += 1
        per_corpus[name] = kept
        print(f"  {name:<14} {len(en_lines):>7} raw -> {kept:>6} kept")

    if args.langid:
        import langid

        langid.set_languages(["en", "so", "sw", "om", "ha", "id", "fi"])
        before = len(pairs)
        pairs = [
            p for p in pairs
            if langid.classify(p[0])[0] == "en" and langid.classify(p[1])[0] in ("so", "sw", "om", "ha")
        ]
        rejects["langid"] += before - len(pairs)

    random.shuffle(pairs)
    dev = pairs[: args.dev_size]
    train = pairs[args.dev_size :]

    print(f"\n{'=' * 58}")
    print(f"  total kept   {len(pairs):,}")
    print(f"  train / dev  {len(train):,} / {len(dev):,}")
    print("  by corpus    " + ", ".join(f"{k} {v:,}" for k, v in per_corpus.items()))
    print("  rejected     " + ", ".join(f"{k} {v:,}" for k, v in rejects.most_common()))
    print(f"{'=' * 58}\n")

    for en, so, c in random.Random(0).sample(pairs, min(5, len(pairs))):
        print(f"  [{c}]")
        print(f"   EN {en[:95]}")
        print(f"   SO {so[:95]}")

    if args.report_only:
        return

    out = REPO / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    for split, rows in (("train", train), ("dev", dev)):
        path = out / f"{split}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for en, so, corpus in rows:
                f.write(json.dumps({"en": en, "so": so, "corpus": corpus}, ensure_ascii=False) + "\n")
        print(f"\nWrote {len(rows):,} pairs to {path}")


if __name__ == "__main__":
    main()
