from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer


MODEL_NAME = "codesage/codesage-small"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RTL_DIR = PROJECT_ROOT / "results" / "llm"
EMBEDDING_DIR = RTL_DIR / "embeddings"

EMBEDDING_DIR.mkdir(parents=True, exist_ok=True)


def load_rtl(path):
    return path.read_text(errors="ignore")


def generate_embedding(model, tokenizer, rtl):

    inputs = tokenizer(
        rtl,
        return_tensors="pt",
        truncation=True,
        max_length=2048,
        add_special_tokens=True
    )

    with torch.no_grad():
        outputs = model(**inputs)

    # CodeSage returns a code representation.
    embedding = outputs[0]

    # Mean-pool token representations
    embedding = embedding.mean(dim=1)

    return embedding.squeeze(0)


def process_file(model, tokenizer, input_file, output_file):

    print(f"\nProcessing:")
    print(input_file)

    rtl = load_rtl(input_file)

    print("RTL characters:", len(rtl))

    embedding = generate_embedding(
        model,
        tokenizer,
        rtl
    )

    torch.save(
        embedding,
        output_file
    )

    print("Embedding shape:", embedding.shape)
    print("Saved:", output_file)


def main():

    print("Using CPU")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        add_eos_token=True
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True
    )

    model.eval()

    clean_input = RTL_DIR / "AES_T100_clean_rtl.v"
    trojan_input = RTL_DIR / "AES_T100_trojan_rtl.v"

    clean_output = (
        EMBEDDING_DIR /
        "AES_T100_clean_embedding.pt"
    )

    trojan_output = (
        EMBEDDING_DIR /
        "AES_T100_trojan_embedding.pt"
    )

    process_file(
        model,
        tokenizer,
        clean_input,
        clean_output
    )

    process_file(
        model,
        tokenizer,
        trojan_input,
        trojan_output
    )


if __name__ == "__main__":
    main()