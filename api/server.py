#!/usr/bin/env python3
"""
Sugan AI — Translation API server.
Uses NLLB-200 for production-quality English ↔ Somali translation.

Start: SUGAN_API_KEY=your-key uvicorn api.server:app --host 0.0.0.0 --port 10100
"""

import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

import torch
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
import anthropic as anthropic_sdk
from pydantic import BaseModel, Field
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

HTML_FILE = Path(__file__).parent / "index.html"

MODEL = os.environ.get("SUGAN_MODEL", "facebook/nllb-200-distilled-1.3B")

LANG_CODES = {
    "en": "eng_Latn",
    "so": "som_Latn",
}

state: dict = {}

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: Annotated[str | None, Security(_api_key_header)]) -> str:
    expected = os.environ.get("SUGAN_API_KEY", "")
    if not expected:
        return key or ""
    if key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return key


# NLLB is a sentence-level model, so feeding it a whole paragraph is both worse
# and slower. Measured on 60 FLORES paragraphs, en->so: one-blob decoding scored
# BLEU 6.29 / chrF++ 29.93 in 469s, while splitting into sentences and batching
# them scored BLEU 13.02 / chrF++ 46.46 in 36s. Long inputs also got silently
# truncated mid-paragraph. So: always split, batch the sentences, reassemble.
NUM_BEAMS = int(os.environ.get("SUGAN_NUM_BEAMS", "4"))
MAX_SENTENCES = 200
SENT_TOKEN_LIMIT = 256

# Periods that do not end a sentence. Protected with a sentinel before splitting
# because Python's re has no variable-width lookbehind.
_ABBREVIATIONS = (
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "St.", "Rev.", "Gen.",
    "Capt.", "Sgt.", "vs.", "etc.", "e.g.", "i.e.", "No.", "Fig.", "Inc.",
    "Ltd.", "Co.", "U.S.", "U.K.", "U.N.", "a.m.", "p.m.", "approx.", "Ave.",
)
_SENTINEL = "\x00"
_PARA_BREAK = ""
_SENT_BOUNDARY = re.compile(r"(?<=[.!?؟])[\"')\]”]*\s+")


def split_sentences(text: str) -> list[str]:
    """Split into sentences, keeping blank-line paragraph breaks as '' markers."""
    protected = text
    for abbrev in _ABBREVIATIONS:
        protected = protected.replace(abbrev, abbrev.replace(".", _SENTINEL))

    out: list[str] = []
    for i, block in enumerate(re.split(r"\n\s*\n", protected)):
        if i:
            out.append(_PARA_BREAK)
        for line in block.splitlines():
            for sent in _SENT_BOUNDARY.split(line):
                sent = sent.replace(_SENTINEL, ".").strip()
                if sent:
                    out.append(sent)
    return out


def _translate_sentences(sentences: list[str], src: str, tgt: str) -> list[str]:
    """Translate a flat list of sentences in one batched forward pass."""
    if not sentences:
        return []
    tokenizer = state["tokenizer"]
    model = state["model"]
    device = state["device"]
    tokenizer.src_lang = LANG_CODES[src]
    inputs = tokenizer(
        sentences, return_tensors="pt", padding=True, truncation=True, max_length=SENT_TOKEN_LIMIT
    ).to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids(LANG_CODES[tgt]),
            max_length=SENT_TOKEN_LIMIT,
            num_beams=NUM_BEAMS,
        )
    return [tokenizer.decode(o, skip_special_tokens=True).strip() for o in out]


def translate(text: str | list, src: str, tgt: str) -> str | list:
    """Translate one string, or a list of strings, sentence by sentence.

    Each input is split independently, every sentence across every input goes
    through the model as a single batch, then each input is reassembled from its
    own pieces so paragraph structure survives.
    """
    texts = text if isinstance(text, list) else [text]

    pieces: list[list[str]] = [split_sentences(t) for t in texts]
    flat: list[str] = []
    owners: list[tuple[int, int]] = []  # (text index, piece index)
    for ti, sents in enumerate(pieces):
        for si, sent in enumerate(sents):
            if sent != _PARA_BREAK:
                flat.append(sent)
                owners.append((ti, si))

    if len(flat) > MAX_SENTENCES:
        raise HTTPException(413, f"too many sentences ({len(flat)} > {MAX_SENTENCES})")

    for (ti, si), done in zip(owners, _translate_sentences(flat, src, tgt)):
        pieces[ti][si] = done

    results = []
    for sents in pieces:
        paragraphs: list[str] = []
        current: list[str] = []
        for sent in sents:
            if sent == _PARA_BREAK:
                paragraphs.append(" ".join(current))
                current = []
            else:
                current.append(sent)
        paragraphs.append(" ".join(current))
        results.append("\n\n".join(p for p in paragraphs if p).strip())

    return results if isinstance(text, list) else results[0]


@asynccontextmanager
async def lifespan(app: FastAPI):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {MODEL} on {device}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL, dtype=torch.float16).to(device)
    model.eval()
    state["tokenizer"] = tokenizer
    state["model"] = model
    state["device"] = device
    api_key_set = bool(os.environ.get("SUGAN_API_KEY"))
    print(f"Ready. API key auth: {'enabled' if api_key_set else 'DISABLED — set SUGAN_API_KEY'}")
    yield
    state.clear()


app = FastAPI(
    title="Sugan AI",
    description="English ↔ Somali translation API powered by NLLB-200",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    source: Literal["en", "so"] = "en"
    target: Literal["en", "so"] = "so"


class TranslateResponse(BaseModel):
    translation: str
    source: str
    target: str
    model: str


class BatchTranslateRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=50)
    source: Literal["en", "so"] = "en"
    target: Literal["en", "so"] = "so"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


SYSTEM_PROMPT = (
    "You are Sugan AI, a helpful and friendly AI assistant. "
    "The user writes to you in English. Always respond in Somali (Af-Soomaali). "
    "Be natural, conversational, and helpful. "
    "Keep replies concise for casual messages, more detailed for complex questions."
)


@app.get("/")
def root():
    if HTML_FILE.exists():
        return FileResponse(HTML_FILE, media_type="text/html")
    return {"service": "Sugan AI", "status": "ok", "version": "0.1.0"}


@app.get("/health")
def health():
    # auth_required lets the UI prompt for a key only when one is enforced.
    return {
        "status": "ok",
        "model": MODEL,
        "auth_required": bool(os.environ.get("SUGAN_API_KEY", "")),
    }


@app.post("/v1/translate", response_model=TranslateResponse)
def translate_endpoint(req: TranslateRequest, _: str = Depends(require_api_key)):
    if req.source == req.target:
        raise HTTPException(400, "source and target must differ")
    result = translate(req.text, req.source, req.target)
    return TranslateResponse(translation=result, source=req.source, target=req.target, model=MODEL)


@app.post("/v1/chat")
def chat_endpoint(req: ChatRequest, _: str = Depends(require_api_key)):
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        raise HTTPException(503, "ANTHROPIC_API_KEY not set on server")

    client = anthropic_sdk.Anthropic(api_key=anthropic_key)
    messages = []
    for m in req.history[-10:]:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": req.message})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    reply_so = response.content[0].text.strip()
    return {"reply_en": "", "reply_so": reply_so}


@app.post("/v1/translate/batch")
def translate_batch(req: BatchTranslateRequest, _: str = Depends(require_api_key)):
    if req.source == req.target:
        raise HTTPException(400, "source and target must differ")
    results = translate(req.texts, req.source, req.target)
    return {"translations": results, "source": req.source, "target": req.target, "model": MODEL}
