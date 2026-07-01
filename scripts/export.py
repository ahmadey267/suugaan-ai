#!/usr/bin/env python3
"""
Merge LoRA adapters into the base model and save a full checkpoint.
Optionally converts to GGUF for use with Ollama (requires llama.cpp).
"""

import argparse
import subprocess
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_MODEL = "google/gemma-3-1b-it"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter_dir", type=str, default="outputs/checkpoint",
                        help="Path to LoRA adapter directory")
    parser.add_argument("--output_dir", type=str, default="outputs/merged",
                        help="Where to save the merged HF model")
    parser.add_argument("--base_model", type=str, default=BASE_MODEL)
    parser.add_argument("--gguf", action="store_true",
                        help="Convert merged model to GGUF (requires llama.cpp cloned to ./llama.cpp)")
    parser.add_argument("--gguf_quant", type=str, default="q4_k_m",
                        help="Quantisation type for GGUF export")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Loading base model {args.base_model} on CPU...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16,
        device_map="cpu",
    )

    print(f"Loading adapter from {args.adapter_dir}...")
    model = PeftModel.from_pretrained(base_model, args.adapter_dir)

    print("Merging...")
    model = model.merge_and_unload()

    print(f"Saving merged model to {out}...")
    model.save_pretrained(out)
    tokenizer.save_pretrained(out)
    print("Merge complete.")

    if args.gguf:
        llama_cpp = Path("llama.cpp")
        convert_script = llama_cpp / "convert_hf_to_gguf.py"
        if not convert_script.exists():
            print(
                "llama.cpp not found. Clone it first:\n"
                "  git clone https://github.com/ggerganov/llama.cpp\n"
                "  pip install -r llama.cpp/requirements.txt"
            )
            return

        gguf_path = out / f"suugaan-{args.gguf_quant}.gguf"
        print(f"Converting to GGUF ({args.gguf_quant}) → {gguf_path}...")
        result = subprocess.run(
            [
                "python", str(convert_script),
                str(out),
                "--outfile", str(gguf_path),
                "--outtype", args.gguf_quant,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("GGUF conversion failed:\n", result.stderr)
        else:
            print(f"GGUF saved to {gguf_path}")
            print("Run with Ollama:\n  ollama create suugaan -f Modelfile")


if __name__ == "__main__":
    main()
