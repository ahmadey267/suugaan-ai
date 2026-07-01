#!/usr/bin/env python3
"""
Sugan AI — Translation API server.
Uses NLLB-200 for production-quality English ↔ Somali translation.

Start: uvicorn api.server:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from typing import Literal

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import pipeline

MODEL = "facebook/nllb-200-distilled-1.3B"

LANG_CODES = {
    "en": "eng_Latn",
    "so": "som_Latn",
}

translators: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    device = 0 if torch.cuda.is_available() else -1
    print(f"Loading {MODEL} on {'CUDA' if device == 0 else 'CPU'}...")

    # en → so
    translators["en-so"] = pipeline(
        "translation",
        model=MODEL,
        src_lang="eng_Latn",
        tgt_lang="som_Latn",
        device=device,
        max_length=400,
    )
    # so → en
    translators["so-en"] = pipeline(
        "translation",
        model=MODEL,
        src_lang="som_Latn",
        tgt_lang="eng_Latn",
        device=device,
        max_length=400,
    )
    print("Ready.")
    yield
    translators.clear()


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
    return {"service": "Sugan AI", "status": "ok", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": list(translators.keys())}


@app.post("/v1/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    if req.source == req.target:
        raise HTTPException(400, "source and target must differ")

    key = f"{req.source}-{req.target}"
    if key not in translators:
        raise HTTPException(400, f"Direction {key} not supported")

    result = translators[key](req.text)[0]["translation_text"]
    return TranslateResponse(
        translation=result,
        source=req.source,
        target=req.target,
        model=MODEL,
    )


@app.post("/v1/translate/batch")
def translate_batch(req: BatchTranslateRequest):
    if req.source == req.target:
        raise HTTPException(400, "source and target must differ")

    key = f"{req.source}-{req.target}"
    if key not in translators:
        raise HTTPException(400, f"Direction {key} not supported")

    results = translators[key](req.texts)
    return {
        "translations": [r["translation_text"] for r in results],
        "source": req.source,
        "target": req.target,
        "model": MODEL,
    }
