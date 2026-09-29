# Hardware Trojan Detection via GNN–LLM Cross-Attention Fusion

Pre-silicon detection and localization of hardware Trojans by fusing **gate-level structural analysis** (Graph Neural Networks) with **RTL semantic analysis** (a pretrained code language model) through cross-attention.

---

## Overview

Hardware Trojans are malicious modifications inserted into a chip's design, built to stay dormant through normal verification. This project targets **design-stage logic Trojans**, detected **before fabrication** from two representations of the same circuit:

- **Structural** — the synthesized gate-level netlist, modeled as a graph and processed by a GNN
- **Semantic** — the original RTL (Verilog) source, encoded by CodeBERT

The two representations are fused with cross-attention, where gate-level node embeddings attend over RTL embeddings. The goal is a model that:

1. Classifies whether a design contains a Trojan
2. Localizes suspicious regions at gate/node granularity
3. Produces an explanation grounded in both structural and semantic evidence

**Scope:** digital circuits, logic (functional) Trojans only. Parametric Trojans and post-silicon techniques (side-channel measurement, physical testing) are out of scope.

---

## Architecture

```
                    TrustHub RTL (Verilog)
                   /                      \
        Structural branch              Semantic branch
                 |                            |
      Synthesis (Yosys)              RTL consolidation
                 |                            |
      Netlist parsing → JSON        CodeBERT, sliding-window
                 |                  chunking (512 tokens, stride 50)
      Graph construction                      |
                 |                  RTL chunk embeddings
      Node features (20-dim)          [num_chunks, 768]
                 |                            |
      GNN encoder (2-layer GCN)               |
                  \                          /
                   Cross-attention fusion
             (node embeddings query RTL embeddings)
                            |
                  Classification (clean / Trojan)
                            |
              Localization and explanation
```

**Node features (20-dim):** one-hot gate class (16, collapsed into functional families such as AND/OR/XOR/MUX/DFF) + in-degree + out-degree + SCOAP-style controllability and observability.

**Semantic encoder:** `microsoft/codebert-base`, used in inference mode only (not fine-tuned). Sliding-window chunking covers full-length RTL files that exceed CodeBERT's 512-token input limit.

---

## Current Status

**Data engineering — complete**
- [x] Synthesis with Yosys — 53 AES and 40 RS232 variants
- [x] Netlist parsing to structured JSON — 93/93
- [x] Graph construction — 93/93
- [x] Structural feature extraction — 93/93
- [x] Dataset QA (isolated nodes, class leakage, netlist/RTL pairing)

**Semantic pipeline — complete**
- [x] RTL consolidation across all AES and RS232 variants — 92 variants
- [x] Chunked CodeBERT embeddings per variant

**Modeling — in progress**
- [x] Cross-attention fusion architecture (shape-validated)
- [x] Obfuscated RTL variants for robustness testing (20 variants)
- [ ] Module-level alignment of gates to RTL
- [ ] Classifier head and training loop
- [ ] Class-imbalance handling (weighted / focal loss)
- [ ] Train / validation / test split
- [ ] Evaluation (balanced accuracy, F1, AUROC)
- [ ] Localization and explanation extraction

**Planned**
- [ ] Deployment interface

---

## Repository Structure

```
CAPSTONE/
├── architecture/        System architecture diagram (PlantUML)
├── dataset/             Sample TrustHub benchmarks
├── docs/                Reference papers and presentations
├── graphs/              Graph visualizations
├── results/
│   ├── gnn/             Netlists, parsed JSON, graphs, node features
│   └── llm/
│       ├── rtl/         Consolidated RTL per variant
│       └── embeddings/  Chunked CodeBERT embeddings
├── src/
│   ├── gnn/             Structural pipeline and QA scripts
│   ├── llm/             Semantic pipeline
│   ├── fusion/          Cross-attention fusion (in progress)
│   └── experiments/     Exploratory analysis scripts
├── requirements.txt
└── README.md
```

---

### Requirements

| | Ubuntu / Linux | macOS | Windows |
|---|---|---|---|
| **Status** | Tested (Ubuntu 22.04) | Untested | Tested (synthesis pipeline) |
| **Python** | 3.10+ | 3.10+ | 3.10+ |
| **Yosys** | OSS CAD Suite | OSS CAD Suite | OSS CAD Suite |
| **Perl** | Usually preinstalled | Preinstalled | [Strawberry Perl](https://strawberryperl.com/) |

Download the OSS CAD Suite build for your platform from the [releases page](https://github.com/YosysHQ/oss-cad-suite-build/releases). Avoid the Ubuntu `apt` Yosys package — it is too old.

**Ubuntu / Linux**
```bash
tar -xzf oss-cad-suite-linux-x64-*.tgz
source oss-cad-suite/environment        # run in every new terminal
yosys --version
pip install -r requirements.txt
```

**macOS**
```bash
tar -xzf oss-cad-suite-darwin-*.tgz     # choose x64 or arm64 to match your Mac
source oss-cad-suite/environment        # run in every new terminal
yosys --version
pip3 install -r requirements.txt
```
> macOS may block the unsigned OSS CAD Suite binaries on first launch. See the OSS CAD Suite installation notes if Yosys fails to open.

**Windows**
```bat
:: Extract the Windows OSS CAD Suite archive, then from its folder:
environment.bat                          :: run in every new Command Prompt
yosys --version
pip install -r requirements.txt
```
> On Windows, use `python` instead of `python3` in the commands below, and use Windows-style paths (e.g. `C:/Users/<name>/...`) when editing the `ROOT` variables in each script. Python's `Path` accepts forward slashes on Windows.

### Dataset

The full TrustHub AES and RS232 benchmark set is not stored in this repository. Download it separately and update the dataset path variables (`ROOT`, `TRUSTHUB_ROOT`) at the top of each script before running.

> Several scripts use absolute paths. Check them before running on a new machine:
> ```bash
> grep -n "ROOT\s*=" src/gnn/*.py src/llm/*.py
> ```

### Running the pipeline

**Structural branch**
```bash
source ~/oss-cad-suite/environment      # activate Yosys in each new terminal
cd src/gnn
python3 02_synthesize_aes.py
python3 02_synthesize_rs232.py
python3 03_parse_netlists.py
python3 04_build_graph.py
python3 05_feature_extractor.py
```

**Quality checks**
```bash
python3 check_graph.py
python3 check_leakage.py
perl check_dataset_consistency.pl --root ../../results/gnn/features --verbose
python3 verify_semantic_coverage.py
```

**Semantic branch**
```bash
cd src/llm
python3 preprocess_all.py
python3 check_model.py
python3 generate_chunk_embeddings_all.py
```

---

## Dataset

**Source:** [TrustHub](https://trust-hub.org/) hardware Trojan benchmarks

| Family | Function |
|---|---|
| AES | 128-bit encryption core |
| RS232 | UART serial communication |

**Known dataset notes**
- **AES-T2200** is excluded — its source is already a gate-level netlist, not RTL
- **AES-T600** stores its Trojan variant in a folder named `TnIn` rather than `TjIn`
- Most RS232 benchmarks have no clean variant (`standard`, `90nm`, `180nm` variants are labeled Trojan); only T2100–T2400 have clean/Trojan pairs
- QA found **class imbalance** (31 clean vs 62 Trojan graphs) and **gate types present only in Trojan-labeled graphs** — both must be controlled for during training to avoid shortcut learning

---

## Technologies

- **Languages:** Python, Verilog, Perl
- **Synthesis:** Yosys (OSS CAD Suite)
- **Graphs:** NetworkX, PyTorch Geometric
- **Deep learning:** PyTorch
- **Language model:** HuggingFace Transformers (CodeBERT)

---

## Team

- Shreya Save
- Rohit Patil
- Saher Sharf
- Samarth Somashekar

---

## License

Developed for academic and research purposes                        .
