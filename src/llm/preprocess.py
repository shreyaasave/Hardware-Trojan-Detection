from pathlib import Path


# Point at the already-downloaded TrustHub dataset (shared with the GNN
# pipeline) instead of duplicating it inside CAPSTONE.
TRUSTHUB_ROOT = Path("/home/shreya/HT_detection_GNN/trusthub/AES_unzipped")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "results" / "llm" / "rtl"

# Folder-name -> label tag, matching 03_parse_netlists.py's convention
# (clean=0, trojan=1). "standard"/"90nm"/"180nm" designs have no separate
# clean variant, per the RS232-T100 README.
VARIANT_FOLDERS = {
    "TjFree": "clean",
    "TjIn": "trojan",
    "TnIn": "trojan",   # AES-T600: Trojan folder misnamed in the raw dataset
    "clean": "clean",
    "trojan": "trojan",
    "standard": "standard",
    "90nm": "90nm",
    "180nm": "180nm",
}

# Benchmarks whose source is already a pre-synthesized gate-level netlist,
# not behavioral RTL - same exception the GNN synthesis pipeline applies
# (02_synthesize_aes.py explicitly skips these with "SKIPPED (pre-synthesized
# netlist, not RTL)"). Including them here would feed gate-level text into
# CodeBERT, producing enormous file sizes (20MB+) and exhausting memory.
SKIP_BENCHMARKS = {"AES-T2200"}


def read_rtl_files(directory):
    """Read every .v file in a directory and concatenate them."""
    combined = []
    v_files = sorted(directory.glob("*.v"))

    if not v_files:
        return None

    for path in v_files:
        print(f"    Reading: {path.name}")
        text = path.read_text(errors="ignore")
        combined.append(f"\n// ===== FILE: {path.name} =====\n\n{text}")

    return "\n".join(combined)


def find_benchmark_dirs(root):
    """
    Mirrors the benchmark discovery used by 02_synthesize_aes.py /
    02_synthesize_rs232.py: each benchmark lives at ROOT/<name>/<name>/src/
    """
    benchmarks = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name in SKIP_BENCHMARKS:
            print(f"SKIP {entry.name}: known pre-synthesized netlist, not RTL")
            continue
        src_dir = entry / entry.name / "src"
        if src_dir.exists():
            benchmarks.append((entry.name, src_dir))
    return benchmarks


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    benchmarks = find_benchmark_dirs(TRUSTHUB_ROOT)
    print(f"\nFound {len(benchmarks)} benchmarks to process\n")

    success = 0
    skipped = 0

    for name, src_dir in benchmarks:
        print("=" * 60)
        print(name)

        found_any = False

        for folder_name, tag in VARIANT_FOLDERS.items():
            variant_dir = src_dir / folder_name
            if not variant_dir.exists():
                continue

            rtl_text = read_rtl_files(variant_dir)
            if rtl_text is None:
                print(f"  SKIP ({folder_name}): no .v files found")
                continue

            out_path = OUTPUT_DIR / f"{name}_{tag}_rtl.v"
            out_path.write_text(rtl_text)
            print(f"  Saved: {out_path.name}")
            found_any = True
            success += 1

        if not found_any:
            print(f"  SKIP: no known variant folder found under {src_dir}")
            skipped += 1

    print("\n" + "=" * 60)
    print("RTL consolidation complete")
    print(f"Variants written  : {success}")
    print(f"Benchmarks skipped: {skipped}")
    print(f"Output folder     : {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()