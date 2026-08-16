from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModel


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = PROJECT_ROOT / "results" / "llm"
OUTPUT_DIR = INPUT_DIR / "embeddings"

MODEL_NAME = "microsoft/codebert-base"


# --------------------------------------------------
# Read RTL
# --------------------------------------------------

def read_rtl(path):
    print(f"Reading: {path}")
    return path.read_text(errors="ignore")


# --------------------------------------------------
# Generate embedding
# --------------------------------------------------

def generate_embedding(text, tokenizer, model):

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model(**inputs)

    # Remove the token dimension by averaging
    # the hidden representation of all tokens.
    embedding = outputs.last_hidden_state.mean(dim=1)

    return embedding.squeeze(0)


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print("Loading model...")
    model = AutoModel.from_pretrained(MODEL_NAME)

    model.eval()

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

        print(f"Generating embedding for {name}...")

        embedding = generate_embedding(
            rtl,
            tokenizer,
            model
        )

        output_path = OUTPUT_DIR / f"{name}.pt"

        torch.save(embedding, output_path)

        print(f"Saved: {output_path}")
        print(f"Shape: {embedding.shape}")

    print("\nDone.")


if __name__ == "__main__":
    main()
