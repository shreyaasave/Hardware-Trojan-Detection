flat = torch.load("results/llm/embeddings/AES_T100_clean.pt")       # [768]
chunked = torch.load("results/llm/embeddings/AES_T100_clean_chunk.pt")  # [28, 768]
mean_of_chunks = chunked.mean(dim=0)  # collapse chunks the "naive" way

sim = F.cosine_similarity(flat, mean_of_chunks, dim=0)
print("Similarity between old truncated embedding and mean-of-all-chunks:", sim.item())