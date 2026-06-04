from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "unified" / "issuances.csv"

UNIFIED_COLUMNS = [
    "source_id",
    "source_name",
    "source_project_id",
    "project_name",
    "issuance_date",
    "issued_quantity",
    "credit_unit",
    "methodology_name",
    "durability",
    "country",
    "source_url",
]


def blank_series(df: pd.DataFrame) -> pd.Series:
    return pd.Series([""] * len(df), index=df.index)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Skipping missing source file: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def build_jcm_issuances() -> pd.DataFrame:
    df = read_csv_if_exists(PROCESSED_DIR / "jcm_mn" / "issuance_records.csv")
    if df.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    projects = read_csv_if_exists(PROCESSED_DIR / "jcm_mn" / "projects_mongolia.csv")
    if not projects.empty:
        df = df.merge(
            projects[["reference_no", "methodology_title"]],
            on="reference_no",
            how="left",
        )
    else:
        df["methodology_title"] = ""

    unified = pd.DataFrame(index=df.index)
    unified["source_id"] = "jcm_mn"
    unified["source_name"] = "JCM Mongolia-Japan"
    unified["source_project_id"] = df.get("reference_no", blank_series(df))
    unified["project_name"] = df.get("project_title", blank_series(df))
    unified["issuance_date"] = df.get("issuance_date", blank_series(df))
    unified["issued_quantity"] = df.get("issued_amount", blank_series(df))
    unified["credit_unit"] = "JCM credit"
    unified["methodology_name"] = df.get("methodology_title", blank_series(df))
    unified["durability"] = ""
    unified["country"] = df.get("country", blank_series(df))
    unified["source_url"] = df.get("source_url", blank_series(df))
    return unified[UNIFIED_COLUMNS]


def build_puro_issuances() -> pd.DataFrame:
    df = read_csv_if_exists(PROCESSED_DIR / "puro_earth" / "puro_issuances_all.csv")
    if df.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    projects = read_csv_if_exists(PROCESSED_DIR / "puro_earth" / "puro_projects_all.csv")
    if not projects.empty:
        df = df.merge(
            projects[["project_id", "country"]],
            on="project_id",
            how="left",
        )
    else:
        df["country"] = ""

    unified = pd.DataFrame(index=df.index)
    unified["source_id"] = "puro_earth"
    unified["source_name"] = "Puro Earth"
    unified["source_project_id"] = df.get("project_id", blank_series(df))
    unified["project_name"] = df.get("project_name", blank_series(df))
    unified["issuance_date"] = df.get("issued_date", blank_series(df))
    unified["issued_quantity"] = df.get("issued_qty", blank_series(df))
    unified["credit_unit"] = "CORC"
    unified["methodology_name"] = df.get("methodology", blank_series(df))
    unified["durability"] = df.get("durability", blank_series(df))
    unified["country"] = df.get("country", blank_series(df))
    unified["source_url"] = df.get("source_url", blank_series(df))
    return unified[UNIFIED_COLUMNS]


def build_unified_issuances() -> pd.DataFrame:
    frames = [
        build_jcm_issuances(),
        build_puro_issuances(),
    ]
    df = pd.concat(frames, ignore_index=True)
    df["issued_quantity"] = pd.to_numeric(df["issued_quantity"], errors="coerce")
    return df.fillna("")


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df = build_unified_issuances()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Built {len(df)} unified issuance rows")
    print(f"Saved to: {OUTPUT_CSV}")
    print("\nRows by source:")
    print(df["source_id"].value_counts().to_string())
    print("\nPreview:")
    print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
