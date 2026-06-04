from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "unified" / "projects.csv"

CANONICAL_COLUMNS = [
    "source_id",
    "source_name",
    "source_project_id",
    "project_name",
    "country",
    "status",
    "project_type",
    "methodology_name",
    "developer_or_supplier",
    "estimated_annual_credits",
    "project_url",
]


def blank_series(df: pd.DataFrame) -> pd.Series:
    return pd.Series([""] * len(df), index=df.index)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Skipping missing source file: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def gold_standard_project_url(source_project_id) -> str:
    if pd.isna(source_project_id):
        return ""

    source_project_id = str(source_project_id).strip()
    if not source_project_id:
        return ""

    return f"https://registry.goldstandard.org/projects/details/{source_project_id}"


def build_jcm_projects() -> pd.DataFrame:
    df = read_csv_if_exists(PROCESSED_DIR / "jcm_mn" / "projects_mongolia.csv")
    if df.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    unified = pd.DataFrame(index=df.index)
    unified["source_id"] = "jcm_mn"
    unified["source_name"] = "JCM Mongolia-Japan"
    unified["source_project_id"] = df.get("reference_no", blank_series(df))
    unified["project_name"] = df.get("project_title", blank_series(df))
    unified["country"] = df.get("host_country", blank_series(df))
    unified["status"] = df.get("status", blank_series(df))
    unified["project_type"] = ""
    unified["methodology_name"] = df.get("methodology_title", blank_series(df))
    unified["developer_or_supplier"] = df.get("host_country_participant", blank_series(df))
    unified["estimated_annual_credits"] = ""
    unified["project_url"] = df.get("source_url", blank_series(df))
    return unified[CANONICAL_COLUMNS]


def build_gold_standard_projects() -> pd.DataFrame:
    df = read_csv_if_exists(PROCESSED_DIR / "gold_standard" / "gs_projects.csv")
    if df.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    unified = pd.DataFrame(index=df.index)
    unified["source_id"] = "gold_standard"
    unified["source_name"] = "Gold Standard"
    unified["source_project_id"] = df.get("gs_id", blank_series(df))
    unified["project_name"] = df.get("project_name", blank_series(df))
    unified["country"] = df.get("country", blank_series(df))
    unified["status"] = df.get("status", blank_series(df))
    unified["project_type"] = df.get("project_type", blank_series(df))
    unified["methodology_name"] = df.get("methodology", blank_series(df))
    unified["developer_or_supplier"] = df.get("project_developer_name", blank_series(df))
    unified["estimated_annual_credits"] = df.get(
        "estimated_annual_credits",
        blank_series(df),
    )
    unified["project_url"] = df.get("gs_id", blank_series(df)).apply(
        gold_standard_project_url
    )
    return unified[CANONICAL_COLUMNS]


def build_puro_projects() -> pd.DataFrame:
    df = read_csv_if_exists(PROCESSED_DIR / "puro_earth" / "puro_projects_all.csv")
    if df.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    unified = pd.DataFrame(index=df.index)
    unified["source_id"] = "puro_earth"
    unified["source_name"] = "Puro Earth"
    unified["source_project_id"] = df.get("project_id", blank_series(df))
    unified["project_name"] = df.get("project_name", blank_series(df))
    unified["country"] = df.get("country", blank_series(df))
    unified["status"] = ""
    unified["project_type"] = ""
    unified["methodology_name"] = df.get("methodology", blank_series(df))
    unified["developer_or_supplier"] = df.get("supplier", blank_series(df))
    unified["estimated_annual_credits"] = ""
    unified["project_url"] = df.get("project_url", blank_series(df))
    return unified[CANONICAL_COLUMNS]


def build_unified_projects() -> pd.DataFrame:
    frames = [
        build_jcm_projects(),
        build_gold_standard_projects(),
        build_puro_projects(),
    ]
    df = pd.concat(frames, ignore_index=True)
    return df.fillna("")


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df = build_unified_projects()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Built {len(df)} unified project rows")
    print(f"Saved to: {OUTPUT_CSV}")
    print("\nRows by source:")
    print(df["source_id"].value_counts().to_string())
    print("\nPreview:")
    print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
