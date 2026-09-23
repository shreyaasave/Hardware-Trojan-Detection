clean = torch.load("results/llm/embeddings/AES_T100_clean_chunk.pt")
trojan = torch.load("results/llm/embeddings/AES_T100_trojan_chunk.pt")

# Compare the first few chunks — do the added Trojan modules produce a
# visibly different embedding pattern?
for i in range(min(clean.shape[0], trojan.shape[0])):
    sim = F.cosine_similarity(clean[i], trojan[i], dim=0)
    print(f"Chunk {i}: similarity = {sim.item():.3f}")