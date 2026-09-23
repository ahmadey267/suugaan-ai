# Sugan AI — English ↔ Somali Translation

A translation API and chat demo for English ↔ Somali, plus the training code from an
attempt to fine-tune a small model for the same job.

**Status: prototype.** Nothing is currently deployed. The API below runs anywhere you can
give it a GPU (or enough patience on CPU); it was last run on a rented Vast.ai RTX 3090 Ti.

## What actually serves translations

`facebook/nllb-200-distilled-1.3B`, off the shelf. No fine-tuning. It is the only thing here
that produces usable Somali today.

```bash
pip install -r api/requirements.txt
export SUGAN_API_KEY=$(openssl rand -hex 32)   # omit and auth is DISABLED — see below
export ANTHROPIC_API_KEY=...                   # only needed for /v1/chat
uvicorn api.server:app --host 0.0.0.0 --port 10100
```

First start downloads ~5.5 GB of model weights.

### Endpoints

| Method | Path | What it does |
|---|---|---|
| `GET` | `/` | Serves `api/index.html`, the chat UI |
| `GET` | `/health` | Liveness + which model is loaded |
| `POST` | `/v1/translate` | One string, `en`↔`so` |
| `POST` | `/v1/translate/batch` | Up to 50 strings per call |
| `POST` | `/v1/chat` | Conversational replies in Somali (Claude Haiku, not NLLB) |

All endpoints read an `X-API-Key` header.

```bash
curl -s http://localhost:10100/v1/translate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SUGAN_API_KEY" \
  -d '{"text":"Good morning","source":"en","target":"so"}'
# {"translation":"Subax wanaagsan","source":"en","target":"so",...}
```

> **Auth is opt-in, and fails open.** If `SUGAN_API_KEY` is unset the server accepts every
> request unauthenticated. Set it before exposing the port to the internet.

`/v1/chat` does not use NLLB at all — it calls Claude Haiku with a system prompt telling it
to answer in Somali. It exists because round-tripping a chat reply through a sentence-level
translation model produced poor conversational Somali.

## The fine-tuning attempt (did not work)

`scripts/` contains a QLoRA pipeline that fine-tunes `google/gemma-3-1b-it` on English-Somali
parallel text. It was trained and evaluated:

**BLEU 6.46, chrF++ 35.98** — and worse than the numbers suggest on real input. "I love you"
came back as "Waa inoo jeclaa"; "Please send the invoice by Friday" as a sentence about
Saturday. The serving path was switched to NLLB-200 and the fine-tune was shelved.

Two likely reasons, both unaddressed:

1. **The corpus is mostly Bible text.** MT560/OPUS en-so is dominated by scripture, so the
   model learned archaic register and had almost no exposure to modern, practical sentences.
2. **1B parameters is small** for a low-resource pair, against a 1.3B model already trained
   on 200 languages.

If this is picked back up, fine-tuning NLLB-200 itself is a better bet than continuing with
Gemma.

| Script | What it does |
|---|---|
| `scripts/prepare_data.py` | Builds `data/train.jsonl` + `data/eval.jsonl` from HF corpus + Pontoon TM |
| `scripts/train.py` | QLoRA fine-tune (CUDA required) |
| `scripts/evaluate.py` | BLEU + chrF++ on the eval set; runs on CPU/MPS |
| `scripts/export.py` | Merges the adapter into the base model; optional GGUF for Ollama |
| `scripts/translate_nllb.py` | Standalone NLLB translation, no server |

### Data

- [`michsethowusu/english-somali_sentence-pairs_mt560`](https://huggingface.co/datasets/michsethowusu/english-somali_sentence-pairs_mt560)
  — 161k pairs, CC-BY 4.0. After filtering and capping, a run produces ~28k train / 500 eval.
- [Mozilla Pontoon Common Voice TM](https://pontoon.mozilla.org/so/common-voice/) — 115
  human-reviewed en-so UI strings, oversampled 5x so they survive the bulk corpus.

Generated data files are gitignored; run `scripts/prepare_data.py` to rebuild them.

Training needs a CUDA GPU with ≥16 GB VRAM. Data prep and eval run on CPU or Apple Silicon.

## `landing/`

A marketing page mockup, built with Lovable and never deployed. **Its copy is aspirational,
not descriptive** — it advertises SDKs, streaming, a 99.9% uptime SLA, SOC 2 compliance,
`api.sugan.ai`, and $29/mo pricing. None of that exists. Treat it as a design artifact.
