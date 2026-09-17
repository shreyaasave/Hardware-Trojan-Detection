from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

AES_ROOT = PROJECT_ROOT / "dataset" / "AES-T100" / "src"
OUTPUT_DIR = PROJECT_ROOT / "results" / "llm"


def read_rtl(directory, filenames):
    combined = []

    for filename in filenames:
        path = directory / filename

        if not path.exists():
            print(f"WARNING: {path} not found")
            continue

        print(f"Reading: {path}")

        text = path.read_text(errors="ignore")

        combined.append(
            f"\n// ===== FILE: {filename} =====\n\n{text}"
        )

    return "\n".join(combined)


def main():

    clean_files = [
        "aes_128.v",
        "round.v",
        "table.v",
    ]

    trojan_files = [
        "top.v",
        "aes_128.v",
        "round.v",
        "table.v",
        "lfsr.v",
        "TSC.v",
    ]

    clean_rtl = read_rtl(
        AES_ROOT / "TjFree",
        clean_files
    )

    trojan_rtl = read_rtl(
        AES_ROOT / "TjIn",
        trojan_files
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    clean_output = OUTPUT_DIR / "AES_T100_clean_rtl.v"
    trojan_output = OUTPUT_DIR / "AES_T100_trojan_rtl.v"

    clean_output.write_text(clean_rtl)
    trojan_output.write_text(trojan_rtl)

    print("\nCreated:")
    print(clean_output)
    print(trojan_output)


if __name__ == "__main__":
    main()
