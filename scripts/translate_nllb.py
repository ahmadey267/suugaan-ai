#!/usr/bin/env python3
"""
Quick test: NLLB-200 English → Somali translation.
Run on the VPS: python scripts/translate_nllb.py
"""

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL = "facebook/nllb-200-distilled-1.3B"
SRC = "eng_Latn"
TGT = "som_Latn"
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading {MODEL} on {device}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL, dtype=torch.float16).to(device)
model.eval()


def translate(text: str) -> str:
    tokenizer.src_lang = SRC
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=400).to(device)
    tgt_lang_id = tokenizer.convert_tokens_to_ids(TGT)
    with torch.no_grad():
        out = model.generate(**inputs, forced_bos_token_id=tgt_lang_id, max_length=400)
    return tokenizer.decode(out[0], skip_special_tokens=True)


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
    print(f"EN: {en}")
    print(f"SO: {translate(en)}")
    print()
