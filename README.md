# Hardware Trojan Detection using GNN + LLM Fusion

## Overview

This project is a final-year capstone focused on pre-silicon Hardware Trojan Detection.

Our approach combines:

- Graph Neural Networks (GNNs) for structural reasoning
- Large Language Models (LLMs) for semantic reasoning
- Attention-based feature fusion
- Explainable AI for Trojan localization

The goal is to accurately detect malicious modifications in digital circuits using information extracted from gate-level netlists.

---

## Objectives

- Parse gate-level Verilog netlists
- Generate graph representations of circuits
- Train a Graph Neural Network for Trojan detection
- Generate semantic reasoning using an LLM
- Fuse structural and semantic information
- Detect Hardware Trojans
- Explain which region of the circuit is suspicious

---

## Project Structure

```
CAPSTONE/

├── dataset/
├── parser/
├── graph/
├── gnn/
├── llm/
├── fusion/
├── localization/
├── evaluation/
├── backend/
├── frontend/
├── models/
├── outputs/
├── papers/
├── presentations/
└── README.md
```

---

## Workflow

```
Verilog Netlist
        │
        ▼
Parser
        │
        ▼
Graph Generation
        │
        ▼
Graph Neural Network
        │
        ├───────────────┐
        ▼               │
Structural Features     │
                        │
LLM Semantic Reasoning──┘
        │
        ▼
Attention Fusion
        │
        ▼
Trojan Detection
        │
        ▼
Localization & Explanation
```

---

## Team Members

| Name |
|------|
| Shreya |
| Saher |
| Rohit |
| Samarth | 

---

## Current Status

- [x] Repository Created
- [x] GitHub Setup
- [ ] Dataset Preparation
- [ ] Parser Implementation
- [ ] Graph Generation
- [ ] GNN Development
- [ ] LLM Integration
- [ ] Fusion Module
- [ ] Evaluation
- [ ] Web Interface

---

## Technologies

- Python
- PyTorch
- PyTorch Geometric
- NetworkX
- PyVerilog
- Yosys
- Flask / FastAPI
- HTML
- CSS
- JavaScript

---

## Dataset

Primary Dataset:

- TrustHub Hardware Trojan Benchmarks

Target Circuits:

- AES
- DES
- RS232
- Other TrustHub benchmarks

---

## License

This project is developed for academic and research purposes.
