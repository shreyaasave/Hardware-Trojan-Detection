"""
Matches each GNN graph (from results/gnn/features/manifest.json) to its
RTL embedding (from results/llm/embeddings/) and writes the matched list to
results/fusion/pairs.json.

Run from the repo root:
    python3 src/fusion/build_pairs.py
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]   # .../CAPSTONE
MANIFEST = REPO_ROOT / "results/gnn/features/manifest.json"
EMBED_DIR = REPO_ROOT / "results/llm/embeddings"
OUT_PATH = REPO_ROOT / "results/fusion/pairs.json"

# netlist-side name -> embedding-side name, where they differ
SIDE_MAP = {
    "tjfree": "clean",
    "tjin": "trojan",
}

# AES graphs where the Trojan RTL did not survive synthesis (same node/edge
# count as clean AES: 7705 nodes / 6528 edges). Excluded by default; set
# EXCLUDE_SUSPECT_AES = False to include them anyway for comparison.
SUSPECT_AES_TROJAN_VARIANTS = {
    "AES-T300", "AES-T500", "AES-T1300", "AES-T1400", "AES-T1500",
    "AES-T1800", "AES-T1900", "AES-T2000", "AES-T2100",
}

# RS232 90nm/180nm designs: the "RTL" is actually a pre-synthesized netlist.
# Excluded by default; set EXCLUDE_90_180NM = False to include them anyway.
EXCLUDE_90_180NM = True
EXCLUDE_SUSPECT_AES = True


def parse_graph_id(graph_id):
    """'AES/AES-T100/clean_netlist' -> ('AES', 'AES-T100', 'clean')"""
    family, variant, filename = graph_id.split("/")
    side = filename.replace("_netlist", "")
    return family, variant, side


def find_embedding(variant, side):
    """Return the embedding path for this (variant, side), or None."""
    embed_side = SIDE_MAP.get(side, side)
    candidate = EMBED_DIR / f"{variant}_{embed_side}_chunk.pt"
    if candidate.exists():
        return candidate
    return None


def main():
    manifest = json.loads(MANIFEST.read_text())

    pairs = []
    skipped = []

    for entry in manifest:
        family, variant, side = parse_graph_id(entry["graph_id"])

        embed_path = find_embedding(variant, side)
        if embed_path is None:
            skipped.append({"graph_id": entry["graph_id"], "reason": "no matching embedding file"})
            continue

        excluded = False
        exclude_reason = None
        if EXCLUDE_90_180NM and side in ("90nm", "180nm"):
            excluded = True
            exclude_reason = "90nm/180nm RS232 'RTL' is a pre-synthesized netlist"
        elif EXCLUDE_SUSPECT_AES and variant in SUSPECT_AES_TROJAN_VARIANTS and side == "trojan":
            excluded = True
            exclude_reason = "Trojan logic did not survive synthesis (same size as clean)"

        pairs.append({
            "graph_id": entry["graph_id"],
            "family": family,
            "variant": variant,
            "side": side,
            "label": entry["label"],
            "netlist_path": entry["data_path"],
            "embedding_path": str(embed_path),
            "num_nodes": entry["num_nodes"],
            "num_edges": entry["num_edges"],
            "excluded": excluded,
            "exclude_reason": exclude_reason,
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(pairs, indent=2))

    usable = [p for p in pairs if not p["excluded"]]
    by_family = {}
    for p in usable:
        d = by_family.setdefault(p["family"], {"total": 0, "y0": 0, "y1": 0})
        d["total"] += 1
        d[f"y{p['label']}"] += 1

    print(f"Matched {len(pairs)} netlist+embedding pairs, skipped {len(skipped)} with no embedding")
    if skipped:
        print("\nSkipped:")
        for s in skipped:
            print(f"   {s['graph_id']}: {s['reason']}")

    excluded = [p for p in pairs if p["excluded"]]
    print(f"\nExcluded (flagged, not deleted): {len(excluded)}")
    for p in excluded:
        print(f"   {p['graph_id']}: {p['exclude_reason']}")

    print(f"\nUsable pairs: {len(usable)}")
    for family, counts in by_family.items():
        print(f"   {family}: total={counts['total']}  y0={counts['y0']}  y1={counts['y1']}")

    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()