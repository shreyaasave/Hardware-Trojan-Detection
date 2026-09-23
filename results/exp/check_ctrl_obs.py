import torch
data = torch.load("results/gnn/features/data/AES/AES-T100/clean_netlist.pt")
# columns: [0:16] one-hot gate class, [16] in_deg, [17] out_deg, [18] controllability, [19] observability
controllability = data.x[:, 18]
observability = data.x[:, 19]

# find the gates hardest to control/observe — classic Trojan hiding spots
hardest_to_control = controllability.argsort(descending=True)[:10]
print(hardest_to_control)