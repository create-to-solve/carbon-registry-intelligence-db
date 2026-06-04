from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_CSV = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "gold_standard"
    / "GSF Registry Projects Export 2026-06-04.csv"
)
LEGACY_RAW_CSV = PROJECT_ROOT / "data" / "raw" / "GSF Registry Projects Export 2026-06-04.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "gold_standard" / "gs_projects.csv"


def clean_column_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def has_value(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().ne("")


def input_csv_path() -> Path:
    if RAW_CSV.exists():
        return RAW_CSV
    if LEGACY_RAW_CSV.exists():
        return LEGACY_RAW_CSV
    raise FileNotFoundError(f"Missing Gold Standard raw export: {RAW_CSV}")


def parse_projects_export(raw_csv: Path | None = None) -> pd.DataFrame:
    raw_csv = raw_csv or input_csv_path()
    df = pd.read_csv(raw_csv, dtype={"GSID": "string", "POA GSID": "string"})

    df.columns = [clean_column_name(column) for column in df.columns]

    if "gsid" not in df.columns:
        raise ValueError("Expected column not found: GSID")

    df = df.rename(columns={"gsid": "gs_id"})
    df["gs_id"] = df["gs_id"].astype(str).str.strip()

    if "estimated_annual_credits" in df.columns:
        df["estimated_annual_credits"] = pd.to_numeric(
            df["estimated_annual_credits"].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        )

    df["is_programme_of_activities"] = has_value(df.get("programme_of_activities", pd.Series(index=df.index)))
    df["has_methodology"] = has_value(df.get("methodology", pd.Series(index=df.index)))
    df["has_description"] = has_value(df.get("description", pd.Series(index=df.index)))

    return df


def print_summary(df: pd.DataFrame) -> None:
    print(f"Parsed {len(df)} Gold Standard projects")
    print("Columns:")
    print(", ".join(df.columns))

    if "status" in df.columns:
        print("\nStatus counts:")
        print(df["status"].fillna("Unknown").value_counts().to_string())

    if "country" in df.columns:
        print("\nTop countries:")
        print(df["country"].fillna("Unknown").value_counts().head(10).to_string())

    if "project_type" in df.columns:
        print("\nTop project types:")
        print(df["project_type"].fillna("Unknown").value_counts().head(10).to_string())


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df = parse_projects_export()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Saved to: {OUTPUT_CSV}")
    print_summary(df)


if __name__ == "__main__":
    main()
