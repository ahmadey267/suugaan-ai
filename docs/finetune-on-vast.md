# Fine-tuning Sugaan on a rented GPU

Runbook for improving English ↔ Somali translation quality by fine-tuning
NLLB-200 on the clean corpus. Written for Vast.ai, but nothing here is
Vast-specific beyond the instance setup.

Budget roughly **2 hours and $1**.

## Why this run exists

The model currently served, `facebook/nllb-200-distilled-1.3B`, is off the
shelf — no Somali-specific training at all. The earlier fine-tune attempt
(`scripts/train.py`, Gemma-3-1B) scored BLEU 6.46 because it was trained on
`mt560`, which is Tanzil + bible-uedin: 93,844 Qur'an verses and 62,195 Bible
verses out of 161,865 pairs, 91% of it with pre-tokenized punctuation.

`scripts/build_corpus.py` replaces that with 27,688 human-translated pairs from
infopankki (civic), translatewiki (UI), tico-19 (health), TED2020 and wikimedia.
No scripture, no tokenization artefacts.

## Before you start

**1. Fix the Hugging Face token.** The stored one was revoked in July. The CLI
reports "already logged in" even when the token is dead, so verify rather than
trust it.

```bash
./venv/bin/hf auth login --force      # token from hf.co/settings/tokens
./venv/bin/python -c "from huggingface_hub import whoami; print(whoami()['name'])"
```

**2. Push the scripts.** The instance pulls from GitHub, so anything uncommitted
locally does not exist on the box.

```bash
git push origin master
```

## Pick an instance

| Card | VRAM | What fits |
|---|---|---|
| RTX 3090 / 4090 | 24 GB | 1.3B with `--optim adafactor`, or LoRA on anything |
| A6000 / A100 | 48 / 40 GB | 1.3B full fine-tune with plain AdamW |

A full fine-tune of the 1.3B under AdamW needs about 18 GB of parameters,
gradients and optimiser state before activations, so on a 24 GB card use
`--optim adafactor` (or `adamw_bnb_8bit`). Filter for ≥60 GB disk — the 1.3B
weights, the corpus and two checkpoints need room.

## On the instance

```bash
git clone https://github.com/ahmadey267/suugaan-ai && cd suugaan-ai
pip install -r requirements.txt -r api/requirements.txt sacrebleu peft
hf auth login                                   # same token
```

### 1. Build the corpus

```bash
python scripts/build_corpus.py
```

Expect ~27,688 train / 1,000 dev pairs. The per-corpus and rejection counts are
printed; if `duplicate` is not the largest rejection bucket, something upstream
changed and the output is worth inspecting before training on it.

### 2. Get FLORES-200

The HF copy is gated. Meta's CDN is not:

```bash
curl -sL https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz | tar xz
mkdir -p data/flores && cp flores200_dataset/devtest/{eng_Latn,som_Latn}.devtest \
  flores200_dataset/dev/{eng_Latn,som_Latn}.dev data/flores/
```

### 3. Baseline — measure before you change anything

```bash
python scripts/eval_nllb.py --model facebook/nllb-200-distilled-1.3B \
  --testset flores --direction en-so --batch_size 32 --save baseline_enso.jsonl
python scripts/eval_nllb.py --model facebook/nllb-200-distilled-1.3B \
  --testset flores --direction so-en --batch_size 32 --save baseline_soen.jsonl
```

**Write both numbers down.** Without them the fine-tune cannot be judged, and a
fine-tune on a small corpus can easily come out worse than the base model.

For reference, `Helsinki-NLP/opus-mt-synthetic-en-so` scores BLEU 11.64 /
chrF++ 41.07 on this test set, measured on a laptop.

### 4. Fine-tune

```bash
python scripts/train_nllb.py \
  --model facebook/nllb-200-distilled-1.3B \
  --full --optim adafactor \
  --epochs 3 --batch_size 16 --grad_accum 2 --lr 3e-5
```

Trains both directions from the same pairs (55,376 examples). Watch the first
50 steps: if loss is not falling, stop and check the data rather than paying for
three epochs of it. Output lands in `outputs/nllb-ft/final`.

Drop `--full --optim adafactor` for LoRA if memory is tight.

### 5. Measure again

```bash
python scripts/eval_nllb.py --model outputs/nllb-ft/final \
  --testset flores --direction en-so --batch_size 32 --save tuned_enso.jsonl
python scripts/eval_nllb.py --model outputs/nllb-ft/final \
  --testset flores --direction so-en --batch_size 32
```

Also check `--testset pontoon`, which is short imperative UI copy and closer to
product text than FLORES news prose.

If the tuned model does not beat the baseline on FLORES, **do not ship it** —
that means the corpus narrowed the model rather than improving it. Compare the
saved `.jsonl` files side by side to see what changed.

### 6. Keep the result

```bash
hf upload <your-username>/sugaan-nllb-en-so outputs/nllb-ft/final
```

The instance is ephemeral. Push the weights before you destroy it, or the run is
gone.

### 7. Serve it

```bash
SUGAN_MODEL=<your-username>/sugaan-nllb-en-so \
SUGAN_API_KEY=$(openssl rand -hex 32) \
uvicorn api.server:app --host 0.0.0.0 --port 10100
```

`SUGAN_MODEL` and `SUGAN_NUM_BEAMS` are both read from the environment, so no
code change is needed to serve a different model.

## Known traps

- **`hf auth login` lies.** It reports "already logged in" for a revoked token.
  Always verify with `whoami()`.
- **Checkpoint saving failed on MPS** during local testing — `torch.save` of the
  optimiser state raised a zipfile error. Not expected on CUDA, but if it
  happens, `--save_strategy no` trains without intermediate checkpoints.
- **Batch size is bounded by the vocabulary, not the sequence.** NLLB has a
  256k vocab, so the logits tensor is `batch × length × 256206`. Batch 8 at 400
  tokens is ~3.3 GB in a single forward pass.
- **NLLB is sentence-level.** Never feed it a paragraph; `api/server.py` splits
  on sentences for this reason. Measured on 60 FLORES paragraphs, whole-blob
  decoding scored BLEU 6.29 against 13.02 for sentence-split, and took 13×
  longer.
