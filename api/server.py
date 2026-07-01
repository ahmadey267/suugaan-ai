#!/usr/bin/env python3
"""
Sugan AI — Translation API server.
Uses NLLB-200 for production-quality English ↔ Somali translation.

Start: SUGAN_API_KEY=your-key uvicorn api.server:app --host 0.0.0.0 --port 10100
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

import torch
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

HTML_FILE = Path(__file__).parent / "index.html"

MODEL = "facebook/nllb-200-distilled-1.3B"

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


def translate(text: str | list, src: str, tgt: str) -> str | list:
    tokenizer = state["tokenizer"]
    model = state["model"]
    device = state["device"]
    tokenizer.src_lang = LANG_CODES[src]
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=400).to(device)
    tgt_id = tokenizer.convert_tokens_to_ids(LANG_CODES[tgt])
    with torch.no_grad():
        out = model.generate(**inputs, forced_bos_token_id=tgt_id, max_length=400)
    if isinstance(text, list):
        return [tokenizer.decode(o, skip_special_tokens=True) for o in out]
    return tokenizer.decode(out[0], skip_special_tokens=True)


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


@app.get("/")
def root():
    if HTML_FILE.exists():
        return FileResponse(HTML_FILE, media_type="text/html")
    return {"service": "Sugan AI", "status": "ok", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}


@app.post("/v1/translate", response_model=TranslateResponse)
def translate_endpoint(req: TranslateRequest, _: str = Depends(require_api_key)):
    if req.source == req.target:
        raise HTTPException(400, "source and target must differ")
    result = translate(req.text, req.source, req.target)
    return TranslateResponse(translation=result, source=req.source, target=req.target, model=MODEL)


@app.post("/v1/translate/batch")
def translate_batch(req: BatchTranslateRequest, _: str = Depends(require_api_key)):
    if req.source == req.target:
        raise HTTPException(400, "source and target must differ")
    results = translate(req.texts, req.source, req.target)
    return {"translations": results, "source": req.source, "target": req.target, "model": MODEL}
