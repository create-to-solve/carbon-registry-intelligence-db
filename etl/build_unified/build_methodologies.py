from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "unified" / "methodologies.csv"

UNIFIED_COLUMNS = [
    "source_id",
    "source_name",
    "methodology_id",
    "methodology_code",
    "methodology_name",
    "status",
    "version",
    "approval_date",
    "sectoral_scope",
    "project_count",
    "source_url",
    "notes",
]


def blank_series(df: pd.DataFrame) -> pd.Series:
    return pd.Series([""] * len(df), index=df.index)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Skipping missing source file: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def build_jcm_methodologies() -> pd.DataFrame:
    df = read_csv_if_exists(PROCESSED_DIR / "jcm_mn" / "methodologies.csv")
    if df.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    unified = pd.DataFrame(index=df.index)
    unified["source_id"] = "jcm_mn"
    unified["source_name"] = "JCM Mongolia-Japan"
    unified["methodology_id"] = df.get("methodology_code", blank_series(df))
    unified["methodology_code"] = df.get("methodology_code", blank_series(df))
    unified["methodology_name"] = df.get("title", blank_series(df))
    unified["status"] = df.get("status", blank_series(df))
    unified["version"] = df.get("latest_version", blank_series(df))
    unified["approval_date"] = df.get("approval_date", blank_series(df))
    unified["sectoral_scope"] = df.get("sectoral_scope", blank_series(df))
    unified["project_count"] = ""
    unified["source_url"] = df.get("source_url", blank_series(df))
    unified["notes"] = "Parsed from JCM Mongolia-Japan methodology listing"
    return unified[UNIFIED_COLUMNS]


def build_gold_standard_methodologies() -> pd.DataFrame:
    df = read_csv_if_exists(PROCESSED_DIR / "gold_standard" / "gs_projects.csv")
    if df.empty or "methodology" not in df.columns:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    methods = df.fillna("")
    methods = methods[methods["methodology"] != ""].copy()
    if methods.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    grouped = (
        methods.groupby("methodology", as_index=False)
        .size()
        .rename(columns={"methodology": "methodology_name", "size": "project_count"})
        .sort_values("methodology_name")
        .reset_index(drop=True)
    )

    unified = pd.DataFrame(index=grouped.index)
    unified["source_id"] = "gold_standard"
    unified["source_name"] = "Gold Standard"
    unified["methodology_id"] = grouped["methodology_name"]
    unified["methodology_code"] = ""
    unified["methodology_name"] = grouped["methodology_name"]
    unified["status"] = ""
    unified["version"] = ""
    unified["approval_date"] = ""
    unified["sectoral_scope"] = ""
    unified["project_count"] = grouped["project_count"]
    unified["source_url"] = ""
    unified["notes"] = "Distinct methodology labels from Gold Standard project export"
    return unified[UNIFIED_COLUMNS]


def build_puro_methodologies() -> pd.DataFrame:
    df = read_csv_if_exists(PROCESSED_DIR / "puro_earth" / "puro_projects_all.csv")
    if df.empty or "methodology" not in df.columns:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    methods = df.fillna("")
    methods = methods[methods["methodology"] != ""].copy()
    if methods.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    grouped = (
        methods.groupby("methodology", as_index=False)
        .agg(
            project_count=("project_id", "count"),
            source_url=("source_url", "first"),
        )
        .rename(columns={"methodology": "methodology_name"})
        .sort_values("methodology_name")
        .reset_index(drop=True)
    )

    unified = pd.DataFrame(index=grouped.index)
    unified["source_id"] = "puro_earth"
    unified["source_name"] = "Puro Earth"
    unified["methodology_id"] = grouped["methodology_name"]
    unified["methodology_code"] = ""
    unified["methodology_name"] = grouped["methodology_name"]
    unified["status"] = ""
    unified["version"] = ""
    unified["approval_date"] = ""
    unified["sectoral_scope"] = ""
    unified["project_count"] = grouped["project_count"]
    unified["source_url"] = grouped["source_url"]
    unified["notes"] = "Distinct methodology labels from Puro Earth registry projects"
    return unified[UNIFIED_COLUMNS]


def build_unified_methodologies() -> pd.DataFrame:
    frames = [
        build_jcm_methodologies(),
        build_gold_standard_methodologies(),
        build_puro_methodologies(),
    ]
    df = pd.concat(frames, ignore_index=True)
    return df.fillna("")


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df = build_unified_methodologies()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Built {len(df)} unified methodology rows")
    print(f"Saved to: {OUTPUT_CSV}")
    print("\nRows by source:")
    print(df["source_id"].value_counts().to_string())
    print("\nPreview:")
    print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
