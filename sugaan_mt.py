"""Shared translation-model plumbing.

Three model families are supported, and they steer the target language in three
different ways. Getting this wrong fails silently -- the model returns fluent
text in the wrong language -- so the logic lives here once rather than being
copied into the server and each script.

  madlad  google/madlad400-*-mt. T5. The target language is a token prefixed to
          the SOURCE text ("<2so> Hello"). Apache-2.0, so it can back a paid
          product.
  nllb    facebook/nllb-200-*. Target is forced as the first generated token,
          source is set on the tokenizer. CC-BY-NC-4.0 -- research only, NOT
          licensed for commercial deployment.
  marian  Helsinki-NLP/opus-mt-*. One direction per checkpoint, no steering.

Family is detected from the loaded config and tokenizer rather than the model
name, so a fine-tune saved to outputs/whatever still resolves correctly.
"""

from __future__ import annotations

# MADLAD uses bare ISO codes; NLLB uses code_Script.
MADLAD_LANG = {"en": "en", "so": "so"}
NLLB_LANG = {"en": "eng_Latn", "so": "som_Latn"}

NONCOMMERCIAL = {"nllb"}


def detect_family(model, tokenizer) -> str:
    """Return 'madlad', 'nllb' or 'marian' for a loaded model."""
    model_type = getattr(model.config, "model_type", "") or ""
    if model_type == "m2m_100":
        return "nllb"
    if model_type == "marian":
        return "marian"
    if model_type in ("t5", "mt5", "umt5"):
        # MADLAD is a T5 whose vocabulary carries <2xx> language tokens.
        if "<2so>" in tokenizer.get_vocab():
            return "madlad"
        raise ValueError(
            "T5 model without MADLAD language tokens; target language cannot be steered"
        )
    raise ValueError(f"unsupported model_type {model_type!r}")


def prepare(tokenizer, texts: list[str], src: str, tgt: str, family: str, max_len: int):
    """Tokenize `texts` and return (encoding, generate kwargs) for this family."""
    if family == "madlad":
        prefixed = [f"<2{MADLAD_LANG[tgt]}> {t}" for t in texts]
        enc = tokenizer(prefixed, return_tensors="pt", padding=True,
                        truncation=True, max_length=max_len)
        return enc, {}

    if family == "nllb":
        tokenizer.src_lang = NLLB_LANG[src]
        enc = tokenizer(texts, return_tensors="pt", padding=True,
                        truncation=True, max_length=max_len)
        return enc, {"forced_bos_token_id": tokenizer.convert_tokens_to_ids(NLLB_LANG[tgt])}

    enc = tokenizer(texts, return_tensors="pt", padding=True,
                    truncation=True, max_length=max_len)
    return enc, {}


def train_pair(tokenizer, src_text: str, tgt_text: str, src: str, tgt: str,
               family: str, max_len: int):
    """Tokenize one training pair, with labels, for this family."""
    if family == "madlad":
        return tokenizer(
            f"<2{MADLAD_LANG[tgt]}> {src_text}",
            text_target=tgt_text,
            max_length=max_len,
            truncation=True,
        )

    if family == "nllb":
        tokenizer.src_lang = NLLB_LANG[src]
        tokenizer.tgt_lang = NLLB_LANG[tgt]
        return tokenizer(src_text, text_target=tgt_text, max_length=max_len, truncation=True)

    return tokenizer(src_text, text_target=tgt_text, max_length=max_len, truncation=True)


def licence_warning(family: str) -> str | None:
    if family in NONCOMMERCIAL:
        return (
            "NLLB-200 is CC-BY-NC-4.0: research use only, not licensed for "
            "commercial deployment, and a fine-tune inherits the term. "
            "Use google/madlad400-3b-mt (Apache-2.0) to ship."
        )
    return None
