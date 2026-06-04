from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_OUTPUTS = [
    PROJECT_ROOT / "data" / "processed" / "jcm_mn" / "methodologies.csv",
    PROJECT_ROOT / "data" / "processed" / "jcm_mn" / "projects_mongolia.csv",
    PROJECT_ROOT / "data" / "processed" / "jcm_mn" / "issuance_records.csv",
    PROJECT_ROOT / "data" / "processed" / "jcm_mn" / "rules_forms.csv",
    PROJECT_ROOT / "data" / "processed" / "source_inventory.csv",
]

OPTIONAL_OUTPUTS = [
    PROJECT_ROOT / "data" / "processed" / "gold_standard" / "gs_projects.csv",
    PROJECT_ROOT / "data" / "processed" / "puro_earth" / "puro_projects.csv",
    PROJECT_ROOT / "data" / "processed" / "puro_earth" / "puro_issuances.csv",
    PROJECT_ROOT / "data" / "processed" / "puro_earth" / "puro_projects_all.csv",
    PROJECT_ROOT / "data" / "processed" / "puro_earth" / "puro_issuances_all.csv",
    PROJECT_ROOT / "data" / "processed" / "unified" / "projects.csv",
    PROJECT_ROOT / "data" / "processed" / "unified" / "issuances.csv",
]


def main() -> int:
    missing = []

    for path in EXPECTED_OUTPUTS:
        relative_path = path.relative_to(PROJECT_ROOT)

        if not path.exists():
            print(f"MISSING {relative_path}")
            missing.append(path)
            continue

        df = pd.read_csv(path)
        print(f"OK      {relative_path}: {len(df)} rows")

    for path in OPTIONAL_OUTPUTS:
        if not path.exists():
            continue

        relative_path = path.relative_to(PROJECT_ROOT)
        df = pd.read_csv(path)
        print(f"OK      {relative_path}: {len(df)} rows")

    if missing:
        print(f"\nMissing {len(missing)} expected processed output(s).")
        return 1

    print("\nAll expected processed outputs are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
