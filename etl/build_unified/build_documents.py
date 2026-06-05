from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "unified" / "documents.csv"

UNIFIED_COLUMNS = [
    "source_id",
    "source_name",
    "document_id",
    "document_title",
    "document_category",
    "document_type",
    "file_format",
    "document_url",
    "source_url",
    "related_entity",
    "notes",
]


def blank_series(df: pd.DataFrame) -> pd.Series:
    return pd.Series([""] * len(df), index=df.index)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Skipping missing source file: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def build_jcm_documents() -> pd.DataFrame:
    df = read_csv_if_exists(PROCESSED_DIR / "jcm_mn" / "rules_forms.csv")
    if df.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    unified = pd.DataFrame(index=df.index)
    unified["source_id"] = "jcm_mn"
    unified["source_name"] = "JCM Mongolia-Japan"
    unified["document_id"] = (
        "jcm_mn:"
        + df.index.astype(str)
        + ":"
        + df.get("document_title", blank_series(df)).astype(str)
    )
    unified["document_title"] = df.get("document_title", blank_series(df))
    unified["document_category"] = df.get("category", blank_series(df))
    unified["document_type"] = df.get("section", blank_series(df))
    unified["file_format"] = df.get("file_format", blank_series(df))
    unified["document_url"] = df.get("file_url", blank_series(df))
    unified["source_url"] = df.get("source_url", blank_series(df))
    unified["related_entity"] = df.get("host_country", blank_series(df))
    unified["notes"] = "Parsed from JCM Mongolia-Japan rules/forms listing"
    return unified[UNIFIED_COLUMNS]


def build_puro_recon_documents() -> pd.DataFrame:
    recon = read_csv_if_exists(PROCESSED_DIR / "puro_earth" / "puro_source_recon.csv")
    if recon.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    records = recon.fillna("").copy()
    records = records[
        records["page_name"].isin(["document_library", "registry_home"])
        | records["possible_entities"].astype(str).str.contains(
            "methodolog|document",
            case=False,
            na=False,
        )
    ].copy()
    if records.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    unified = pd.DataFrame(index=records.index)
    unified["source_id"] = "puro_earth"
    unified["source_name"] = "Puro Earth"
    unified["document_id"] = "puro_earth:recon:" + records["page_name"].astype(str)
    unified["document_title"] = records["page_name"].astype(str).str.replace("_", " ").str.title()
    unified["document_category"] = records.get("possible_entities", blank_series(records))
    unified["document_type"] = "source reconnaissance page"
    unified["file_format"] = "HTML"
    unified["document_url"] = records.get("url", blank_series(records))
    unified["source_url"] = records.get("url", blank_series(records))
    unified["related_entity"] = "Puro Earth"
    unified["notes"] = records.get("notes", blank_series(records))
    return unified[UNIFIED_COLUMNS]


def build_puro_access_note_documents() -> pd.DataFrame:
    notes = read_csv_if_exists(
        PROCESSED_DIR / "puro_earth" / "puro_dynamic_access_notes.csv"
    )
    if notes.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    records = notes.fillna("").copy()
    records = records[records["page_name"].isin(["projects", "issuances"])].copy()
    if records.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    unified = pd.DataFrame(index=records.index)
    unified["source_id"] = "puro_earth"
    unified["source_name"] = "Puro Earth"
    unified["document_id"] = (
        "puro_earth:access_note:"
        + records.index.astype(str)
        + ":"
        + records["page_name"].astype(str)
    )
    unified["document_title"] = (
        "Dynamic access note: " + records["page_name"].astype(str)
    )
    unified["document_category"] = "registry access notes"
    unified["document_type"] = "access note"
    unified["file_format"] = "CSV note"
    unified["document_url"] = records.get("test_url", blank_series(records))
    unified["source_url"] = records.get("test_url", blank_series(records))
    unified["related_entity"] = records.get("page_name", blank_series(records))
    unified["notes"] = records.get("notes", blank_series(records))
    return unified[UNIFIED_COLUMNS]


def build_unified_documents() -> pd.DataFrame:
    frames = [
        build_jcm_documents(),
        build_puro_recon_documents(),
        build_puro_access_note_documents(),
    ]
    df = pd.concat(frames, ignore_index=True)
    return df.fillna("")


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df = build_unified_documents()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Built {len(df)} unified document rows")
    print(f"Saved to: {OUTPUT_CSV}")
    print("\nRows by source:")
    print(df["source_id"].value_counts().to_string())
    print("\nPreview:")
    print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
