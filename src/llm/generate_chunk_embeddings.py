"""
Generates sliding-window chunked CodeBERT embeddings for RTL files.

This is the CURRENT STANDARD semantic embedding method for this project.
It replaces the older flat mean-pooled approach (generate_embeddings.py,
now deprecated), which silently truncated RTL at 512 tokens.

Core method: split each RTL file into overlapping 512-token windows
(stride=50), masked-mean-pool each window separately, and stack the
results into a single (num_chunks, 768) tensor per file.
"""

import os
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer


# --------------------------------------------------
# Config — adjust these paths for your local setup
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Where the consolidated RTL text files live (from preprocess.py)
INPUT_DIR = PROJECT_ROOT / "results" / "llm"

# Where chunked embeddings will be saved
OUTPUT_DIR = INPUT_DIR / "embeddings"

CHECKPOINT = "microsoft/codebert-base"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# --------------------------------------------------
# Load model + tokenizer once
# --------------------------------------------------

print(f"Loading {CHECKPOINT} on {DEVICE}...")
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
model = AutoModel.from_pretrained(CHECKPOINT).to(DEVICE)
model.eval()


# --------------------------------------------------
# Core function — the actual fix
# --------------------------------------------------

def get_chunk_embeddings(code_text, max_length=512, stride=50):
    """
    Splits code_text into overlapping token windows and returns one
    masked-mean-pooled 768-d embedding per chunk.

    Returns: tensor of shape (num_chunks, 768)
    """
    encoding = tokenizer(
        code_text,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
        stride=stride,
        return_overflowing_tokens=True,
        padding="max_length",   # pads every chunk to the same length
    )

    num_chunks = encoding["input_ids"].shape[0]
    chunk_embeddings = []

    with torch.no_grad():
        for i in range(num_chunks):
            input_ids = encoding["input_ids"][i].unsqueeze(0).to(DEVICE)
            attention_mask = encoding["attention_mask"][i].unsqueeze(0).to(DEVICE)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)

            # Masked mean pool — ignore padded positions so the last
            # (shorter) chunk isn't diluted by pad-token embeddings.
            hidden = outputs.last_hidden_state.squeeze(0)          # (max_length, 768)
            mask = attention_mask.squeeze(0).unsqueeze(-1).float()  # (max_length, 1)
            chunk_emb = (hidden * mask).sum(dim=0) / mask.sum()

            chunk_embeddings.append(chunk_emb.cpu())

    return torch.stack(chunk_embeddings)  # (num_chunks, 768)


# --------------------------------------------------
# Read RTL
# --------------------------------------------------

def read_rtl(path):
    print(f"Reading: {path}")
    return path.read_text(errors="ignore")


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    designs = {
        "AES_T100_clean": INPUT_DIR / "AES_T100_clean_rtl.v",
        "AES_T100_trojan": INPUT_DIR / "AES_T100_trojan_rtl.v",
    }

    for name, rtl_path in designs.items():
        if not rtl_path.exists():
            print(f"ERROR: {rtl_path} not found")
            continue

        rtl = read_rtl(rtl_path)

        print(f"Generating chunked embeddings for {name}...")
        embedding = get_chunk_embeddings(rtl)

        output_path = OUTPUT_DIR / f"{name}_chunk.pt"
        torch.save(embedding, output_path)

        print(f"Saved: {output_path}")
        print(f"Shape: {tuple(embedding.shape)}")

    print("\nDone.")


if __name__ == "__main__":
    main()