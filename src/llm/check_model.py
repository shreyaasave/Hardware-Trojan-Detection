from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "microsoft/codebert-base"


def main():
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print("Loading model...")
    model = AutoModel.from_pretrained(MODEL_NAME)

    print("Tokenizer OK")
    print("Model OK")
    print("Model:", MODEL_NAME)
    print("Hidden size:", model.config.hidden_size)
    print("Max position embeddings:", model.config.max_position_embeddings)


if __name__ == "__main__":
    main()
