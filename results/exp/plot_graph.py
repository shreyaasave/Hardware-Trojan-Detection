import networkx as nx
import matplotlib.pyplot as plt

with open("results/gnn/graphs/RS232/RS232-T2100/clean_netlist.gpickle", "rb") as f:
    G = pickle.load(f)

nx.draw(G, with_labels=True, node_size=200, font_size=6)
plt.savefig("rs232_t2100_graph.png")