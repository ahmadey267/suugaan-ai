#!/usr/bin/env python3
"""
Quick test: NLLB-200 English → Somali translation.
Run on the VPS: python scripts/translate_nllb.py
"""

import torch
from transformers import pipeline

MODEL = "facebook/nllb-200-distilled-1.3B"
device = 0 if torch.cuda.is_available() else -1

print(f"Loading {MODEL}...")
translator = pipeline(
    "translation",
    model=MODEL,
    src_lang="eng_Latn",
    tgt_lang="som_Latn",
    device=device,
    max_length=400,
)

sentences = [
    "Where is the hospital?",
    "The government announced new elections.",
    "I love you.",
    "Please send the invoice by Friday.",
    "Children need access to education.",
    "What is the price of this?",
    "The flight has been delayed.",
]

print()
for en in sentences:
    result = translator(en)[0]["translation_text"]
    print(f"EN: {en}")
    print(f"SO: {result}")
    print()
