import os
import re
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# --------------------------------------------------
# Parse Gate-Level Netlist
# --------------------------------------------------

def parse_netlist_to_graph(netlist_path):

    G = nx.DiGraph()

    with open(netlist_path, "r") as f:
        content = f.read()

    # Remove single-line comments
    content = re.sub(r"//.*", "", content)

    # Matches:
    # AND2 U1 (.A(a), .B(b), .Y(n1));
    gate_pattern = re.compile(
        r'(\w+)\s+(\w+)\s*\((.*?)\)\s*;',
        re.DOTALL
    )

    # Output port names used by different libraries
    output_ports = {
        "Y", "Q", "Z", "ZN", "O", "OUT", "QB"
    }

    for match in gate_pattern.finditer(content):

        gate_type = match.group(1)
        gate_name = match.group(2)
        port_str = match.group(3)

        # Ignore non-gate statements
        if gate_type in {
            "module",
            "endmodule",
            "wire",
            "input",
            "output",
            "reg",
            "assign",
            "parameter"
        }:
            continue

        # Add gate node
        G.add_node(gate_name, gate_type=gate_type)

        # Match ports
        # Handles:
        # .A(a)
        # .B(data[3])
        # .Y(n1)
        port_pattern = re.compile(r'\.(\w+)\(([^)]+)\)')

        for port in port_pattern.finditer(port_str):

            port_name = port.group(1)
            signal_name = port.group(2).strip()

            G.add_node(signal_name, gate_type="WIRE")

            if port_name in output_ports:
                G.add_edge(gate_name, signal_name)
            else:
                G.add_edge(signal_name, gate_name)

    return G


# --------------------------------------------------
# Graph Statistics
# --------------------------------------------------

def print_graph_stats(G, name):

    print("\n" + "=" * 60)
    print(f"Graph : {name}")
    print(f"Nodes : {G.number_of_nodes()}")
    print(f"Edges : {G.number_of_edges()}")

    gate_count = {}

    for _, data in G.nodes(data=True):
        gt = data.get("gate_type", "UNKNOWN")
        gate_count[gt] = gate_count.get(gt, 0) + 1

    print("\nGate Type Breakdown:")

    for gt, count in sorted(
            gate_count.items(),
            key=lambda x: x[1],
            reverse=True):

        print(f"{gt:20s} : {count}")

    indegrees = dict(G.in_degree())
    outdegrees = dict(G.out_degree())

    print("\nGraph Metrics")

    print(f"Average Fan-in  : {sum(indegrees.values())/len(indegrees):.2f}")
    print(f"Average Fan-out : {sum(outdegrees.values())/len(outdegrees):.2f}")

    print(f"Maximum Fan-in  : {max(indegrees.values())}")
    print(f"Maximum Fan-out : {max(outdegrees.values())}")

    print("=" * 60)


# --------------------------------------------------
# Visualize Graph
# --------------------------------------------------

def visualize_subgraph(G, name, n_nodes=60):

    os.makedirs("../graphs", exist_ok=True)

    sample_nodes = list(G.nodes())[:n_nodes]
    sub = G.subgraph(sample_nodes)

    plt.figure(figsize=(14, 10))

    pos = nx.spring_layout(sub, seed=42)

    colors = []

    for node in sub.nodes():

        gt = sub.nodes[node]["gate_type"]

        if gt == "WIRE":
            colors.append("#9ecae1")

        elif "DFF" in gt or "FF" in gt:
            colors.append("#fdae6b")

        else:
            colors.append("#a1d99b")

    nx.draw_networkx(
        sub,
        pos,
        node_color=colors,
        node_size=350,
        font_size=6,
        arrows=True,
        edge_color="gray",
        width=0.6
    )

    plt.title(f"{name} (Sample of {n_nodes} Nodes)")

    output_file = f"../graphs/{name}_graph.png"

    plt.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"\nGraph image saved to:")
    print(output_file)


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    netlist_path = "../Dataset/trojan/AES-T100/src/TjFree/aes_clean_netlist.v"

    G = parse_netlist_to_graph(netlist_path)

    print_graph_stats(G, "AES-T100-Clean")

    visualize_subgraph(G, "AES-T100-Clean")