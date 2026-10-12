# Fine-tuning Sugaan on a rented GPU

Runbook for improving English ↔ Somali translation quality by fine-tuning
MADLAD-400 on the clean corpus. Written for Vast.ai, but nothing here is
Vast-specific beyond the instance setup.

Budget roughly **3 hours and $2**.

## Why MADLAD and not NLLB

`google/madlad400-3b-mt` is **Apache-2.0**. `facebook/nllb-200-*` is
**CC-BY-NC-4.0** — research use only, not licensed for commercial deployment,
and a fine-tune is a derivative work that inherits the term. NLLB's own model
card also puts most of the product's intended uses out of scope:

> "NLLB-200 is a research model and is not released for production
> deployment... not intended to be used with domain specific texts, such as
> medical domain or legal domain... not intended to be used for document
> translation... translations can not be used as certified translations."

So NLLB is fine to benchmark against and impossible to sell. MADLAD is the base
to build on. `scripts/eval_mt.py` and `scripts/train_mt.py` print a licence
warning whenever they load a non-commercial model, and so does the API server.

`Helsinki-NLP/opus-mt-synthetic-en-so` (CC-BY-4.0, attribution required) is the
third option: far smaller, far faster, and it scores BLEU 11.64 / chrF++ 41.07
on FLORES en→so.

## Why this run exists

The corpus behind every earlier result, `michsethowusu/english-somali_
sentence-pairs_mt560`, is Tanzil + bible-uedin: 93,844 Qur'an verses and 62,195
Bible verses out of 161,865 pairs, with 91% carrying pre-tokenized punctuation.
The shelved Gemma fine-tune scored BLEU 6.46 on it.

`scripts/build_corpus.py` replaces it with 27,688 human-translated pairs from
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

**2. Push.** The instance pulls from GitHub, so anything uncommitted locally
does not exist on the box.

## Pick an instance

MADLAD-3B is 2.94B parameters — 11.76 GB of fp32 weights before anything else.

| Card | VRAM | What fits |
|---|---|---|
| RTX 3090 / 4090 | 24 GB | LoRA. The default, and enough for this corpus. |
| A6000 | 48 GB | LoRA comfortably; full fine-tune with `--optim adafactor` is tight |
| A100 80 GB | 80 GB | Full fine-tune with AdamW |

A full fine-tune under AdamW needs roughly 47 GB for parameters, gradients and
optimiser state before activations. On 27,688 pairs LoRA is the right choice
anyway: there is not enough data to justify moving three billion parameters, and
a full fine-tune on a corpus this small is as likely to narrow the model as
improve it.

Filter for **≥100 GB disk** — the weights, the corpus and two checkpoints need
room.

## On the instance

```bash
git clone https://github.com/ahmadey267/suugaan-ai && cd suugaan-ai
pip install -r requirements.txt -r api/requirements.txt sacrebleu peft sentencepiece
hf auth login
```

### 1. Build the corpus

```bash
python scripts/build_corpus.py
```

Expect ~27,688 train / 1,000 dev. The per-corpus and rejection counts print; if
`duplicate` is not the largest rejection bucket, something upstream changed and
the output is worth inspecting before you train on it.

### 2. Get FLORES-200

The HF copy is gated. Meta's CDN is not:

```bash
curl -sL https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz | tar xz
mkdir -p data/flores && cp flores200_dataset/devtest/{eng_Latn,som_Latn}.devtest \
  flores200_dataset/dev/{eng_Latn,som_Latn}.dev data/flores/
```

### 3. Baseline first

Measure the base model before changing it. Without this the fine-tune cannot be
judged, and a fine-tune on a small corpus can easily come out worse.

```bash
python scripts/eval_mt.py --model google/madlad400-3b-mt \
  --testset flores --direction en-so --batch_size 16 --save base_enso.jsonl
python scripts/eval_mt.py --model google/madlad400-3b-mt \
  --testset flores --direction so-en --batch_size 16 --save base_soen.jsonl
```

**Write both numbers down.** Known reference points on this test set, en→so:

| Model | BLEU | chrF++ |
|---|---|---|
| `Helsinki-NLP/opus-mt-synthetic-en-so` | 11.64 | 41.07 |
| `google/madlad400-3b-mt` | *measure it* | |
| `facebook/nllb-200-distilled-1.3B` | *optional reference* | |

MADLAD is roughly twice the size of NLLB-1.3B, so if it does not beat 11.64
comfortably, stop and work out why before spending GPU hours on a fine-tune.

### 4. Fine-tune

```bash
python scripts/train_mt.py \
  --model google/madlad400-3b-mt \
  --epochs 3 --batch_size 8 --grad_accum 4 --lr 1e-4 --lora_r 16
```

Trains both directions from the same pairs (55,376 examples), so one model
serves en→so and so→en as the API expects. Watch the first 50 steps: if loss is
not falling, stop and check the data rather than paying for three epochs of it.
Output lands in `outputs/mt-ft/final` (LoRA is merged in, so it loads as a
plain model and the server needs no PEFT dependency).

On 80 GB, `--full --optim adafactor --lr 3e-5` is worth one run to compare.

### 5. Measure again

```bash
python scripts/eval_mt.py --model outputs/mt-ft/final \
  --testset flores --direction en-so --batch_size 16 --save tuned_enso.jsonl
python scripts/eval_mt.py --model outputs/mt-ft/final \
  --testset flores --direction so-en --batch_size 16
python scripts/eval_mt.py --model outputs/mt-ft/final --testset pontoon
```

`pontoon` is short imperative UI copy and is closer to product text than FLORES
news prose, so a model can legitimately win there and lose on FLORES. Decide in
advance which one you care about.

If the tuned model does not beat the baseline, **do not ship it**. Diff
`base_enso.jsonl` against `tuned_enso.jsonl` to see what actually changed.

### 6. Keep the result

```bash
hf upload <your-username>/sugaan-madlad-en-so outputs/mt-ft/final
```

The instance is ephemeral. Push the weights before you destroy it, or the run is
gone.

### 7. Serve it

```bash
SUGAN_MODEL=<your-username>/sugaan-madlad-en-so \
SUGAN_API_KEY=$(openssl rand -hex 32) \
uvicorn api.server:app --host 0.0.0.0 --port 10100
```

`SUGAN_MODEL` and `SUGAN_NUM_BEAMS` are read from the environment, so serving a
different model needs no code change. The server detects the model family and
steers the target language accordingly.

## How the families differ

`sugaan_mt.py` holds this in one place because getting it wrong fails silently —
the model returns fluent text in the wrong language.

| Family | How the target language is set |
|---|---|
| MADLAD | `<2so>` prefixed to the **source** text (Somali is token id 130) |
| NLLB | `forced_bos_token_id`, source set on the tokenizer |
| Marian | Not set; one direction per checkpoint |

## Known traps

- **`hf auth login` lies.** It reports "already logged in" for a revoked token.
  Verify with `whoami()`.
- **Vocabulary bounds batch size, not sequence length.** These models carry
  256k-token vocabularies, so the logits tensor is `batch × length × 256000`.
  Batch 8 at 400 tokens is ~3.3 GB in a single forward pass, and it OOMs a 20 GB
  allocator without warning.
- **Checkpoint saving failed on MPS** during local testing — `torch.save` of the
  optimiser state raised a zipfile error. Not expected on CUDA; `--save_strategy
  no` is the escape hatch.
- **These are sentence-level models.** Never feed one a paragraph. `api/server.py`
  segments first for this reason: measured on 60 FLORES paragraphs, whole-blob
  decoding scored BLEU 6.29 against 13.02 segmented, and took 13× longer.
- **Check the device.** `api/server.py` fell back to CPU on Apple Silicon for
  weeks because its device check only tested CUDA. The startup log names the
  device it chose; read it.
