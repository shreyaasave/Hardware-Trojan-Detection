"""
Trains TrojanDetector on the pairs in results/fusion/pairs.json.

Run from the repo root:
    python3 src/fusion/train_fusion.py
"""
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
from torch_geometric.data import Batch

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cross_attention_fusion import TrojanDetector  # noqa: E402

PAIRS_PATH = REPO_ROOT / "results/fusion/pairs.json"
RUNS_DIR = REPO_ROOT / "results/fusion/runs"

SEED = 42
EPOCHS = 15
BATCH_SIZE = 2
LR = 1e-3
VAL_FRAC = 0.2


def set_seed(seed):
    random.seed(seed)
    torch.manual_seed(seed)


def load_samples():
    pairs = json.loads(PAIRS_PATH.read_text())
    return [p for p in pairs if not p["excluded"]]


class HWTrojanDataset(Dataset):
    def __init__(self, samples):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        graph = torch.load(s["netlist_path"], weights_only=False)
        rtl = torch.load(s["embedding_path"])  # (num_chunks, 768)
        return graph, rtl, s["label"]


def collate_fn(batch):
    graphs, rtls, labels = zip(*batch)
    pyg_batch = Batch.from_data_list(list(graphs))
    rtl_padded = pad_sequence(list(rtls), batch_first=True)
    lengths = [r.shape[0] for r in rtls]
    code_mask = torch.zeros(rtl_padded.shape[:2], dtype=torch.bool)
    for i, length in enumerate(lengths):
        code_mask[i, length:] = True
    labels = torch.tensor(labels, dtype=torch.long)
    return pyg_batch, rtl_padded, code_mask, labels


def variant_grouped_split(samples, val_frac, seed):
    groups = defaultdict(list)
    for s in samples:
        groups[(s["family"], s["variant"])].append(s)
    keys = list(groups.keys())
    random.Random(seed).shuffle(keys)
    n_val = max(1, int(len(keys) * val_frac))
    val_keys, train_keys = set(keys[:n_val]), set(keys[n_val:])
    train = [s for k in train_keys for s in groups[k]]
    val = [s for k in val_keys for s in groups[k]]
    return train, val


def balanced_accuracy(preds, labels):
    """Average of per-class recall. Robust to class imbalance, unlike plain accuracy."""
    preds, labels = torch.as_tensor(preds), torch.as_tensor(labels)
    recalls = []
    for c in (0, 1):
        mask = labels == c
        if mask.sum() == 0:
            continue
        recalls.append((preds[mask] == c).float().mean().item())
    return sum(recalls) / len(recalls) if recalls else float("nan")


def compute_class_weights(samples):
    counts = defaultdict(int)
    for s in samples:
        counts[s["label"]] += 1
    total = sum(counts.values())
    # inverse frequency, normalized so weights average to 1
    weights = {c: total / (2 * counts[c]) for c in (0, 1) if counts[c] > 0}
    return torch.tensor([weights.get(0, 1.0), weights.get(1, 1.0)], dtype=torch.float)


def run_epoch(model, loader, device, criterion, optimizer=None):
    is_train = optimizer is not None
    model.train() if is_train else model.eval()

    total_loss, all_preds, all_labels = 0.0, [], []
    context = torch.enable_grad() if is_train else torch.no_grad()
    with context:
        for pyg_batch, rtl_padded, code_mask, labels in loader:
            pyg_batch = pyg_batch.to(device)
            rtl_padded = rtl_padded.to(device)
            code_mask = code_mask.to(device)
            labels = labels.to(device)

            if is_train:
                optimizer.zero_grad()
            logits, _ = model(pyg_batch, rtl_padded, code_mask)
            loss = criterion(logits, labels)
            if is_train:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * labels.size(0)
            all_preds.extend(logits.argmax(dim=1).cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    avg_loss = total_loss / len(all_labels)
    bal_acc = balanced_accuracy(all_preds, all_labels)
    return avg_loss, bal_acc


def main():
    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    samples = load_samples()
    print(f"Loaded {len(samples)} usable samples")

    train_samples, val_samples = variant_grouped_split(samples, VAL_FRAC, SEED)
    print(f"Train: {len(train_samples)} | Val: {len(val_samples)}")

    train_loader = DataLoader(HWTrojanDataset(train_samples), batch_size=BATCH_SIZE,
                               shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(HWTrojanDataset(val_samples), batch_size=BATCH_SIZE,
                             shuffle=False, collate_fn=collate_fn)

    class_weights = compute_class_weights(train_samples).to(device)
    print(f"Class weights (0=clean, 1=trojan): {class_weights.tolist()}")

    model = TrojanDetector().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    run_dir = RUNS_DIR / time.strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    history = []

    best_val_bal_acc = -1.0
    for epoch in range(1, EPOCHS + 1):
        train_loss, train_bal_acc = run_epoch(model, train_loader, device, criterion, optimizer)
        val_loss, val_bal_acc = run_epoch(model, val_loader, device, criterion, optimizer=None)

        print(f"epoch {epoch:2d} | train_loss {train_loss:.4f} train_bal_acc {train_bal_acc:.3f} "
              f"| val_loss {val_loss:.4f} val_bal_acc {val_bal_acc:.3f}")
        history.append({"epoch": epoch, "train_loss": train_loss, "train_bal_acc": train_bal_acc,
                         "val_loss": val_loss, "val_bal_acc": val_bal_acc})

        if val_bal_acc > best_val_bal_acc:
            best_val_bal_acc = val_bal_acc
            torch.save(model.state_dict(), run_dir / "best_model.pt")

    (run_dir / "history.json").write_text(json.dumps(history, indent=2))
    (run_dir / "config.json").write_text(json.dumps({
        "seed": SEED, "epochs": EPOCHS, "batch_size": BATCH_SIZE, "lr": LR,
        "val_frac": VAL_FRAC, "n_train": len(train_samples), "n_val": len(val_samples),
        "class_weights": class_weights.cpu().tolist(),
    }, indent=2))
    print(f"\nBest val balanced accuracy: {best_val_bal_acc:.3f}")
    print(f"Saved to {run_dir}")


if __name__ == "__main__":
    main()