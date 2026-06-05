from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "unified" / "methodology_profiles.csv"

UNIFIED_COLUMNS = [
    "source_id",
    "source_name",
    "methodology_name",
    "methodology_code",
    "version",
    "related_projects_count",
    "related_documents_count",
    "countries_count",
    "example_project_name",
    "example_project_url",
    "notes",
]


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Skipping missing source file: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def count_related_documents(methodology_row: pd.Series, documents: pd.DataFrame) -> int:
    if documents.empty:
        return 0

    methodology_name = normalize_text(methodology_row.get("methodology_name", ""))
    methodology_code = normalize_text(methodology_row.get("methodology_code", ""))
    if not methodology_name and not methodology_code:
        return 0

    source_docs = documents[
        documents["source_id"].astype(str) == str(methodology_row.get("source_id", ""))
    ].copy()
    if source_docs.empty or "document_title" not in source_docs.columns:
        return 0

    titles = source_docs["document_title"].fillna("").astype(str).str.lower()
    mask = pd.Series(False, index=source_docs.index)
    if methodology_code:
        mask = mask | titles.str.contains(methodology_code, regex=False, na=False)
    if methodology_name and len(methodology_name) >= 10:
        mask = mask | titles.str.contains(methodology_name, regex=False, na=False)
    return int(mask.sum())


def build_methodology_profiles() -> pd.DataFrame:
    methodologies = read_csv_if_exists(PROCESSED_DIR / "unified" / "methodologies.csv")
    if methodologies.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    links = read_csv_if_exists(
        PROCESSED_DIR / "unified" / "methodology_project_links.csv"
    )
    documents = read_csv_if_exists(PROCESSED_DIR / "unified" / "documents.csv")

    methodologies = methodologies.fillna("").copy()
    if links.empty:
        link_counts_by_name = pd.DataFrame(
            columns=[
                "source_id",
                "methodology_name",
                "related_projects_count",
                "countries_count",
                "example_project_name",
                "example_project_url",
            ]
        )
        link_counts_by_code = pd.DataFrame(
            columns=[
                "source_id",
                "methodology_code",
                "related_projects_count_by_code",
                "countries_count_by_code",
                "example_project_name_by_code",
                "example_project_url_by_code",
            ]
        )
    else:
        links = links.fillna("").copy()
        link_counts_by_name = (
            links.groupby(["source_id", "methodology_name"], as_index=False)
            .agg(
                related_projects_count=("source_project_id", "count"),
                countries_count=("country", lambda values: values.replace("", pd.NA).nunique()),
                example_project_name=("project_name", "first"),
                example_project_url=("project_url", "first"),
            )
        )
        links_with_code = links[links["methodology_code"] != ""].copy()
        if links_with_code.empty:
            link_counts_by_code = pd.DataFrame(
                columns=[
                    "source_id",
                    "methodology_code",
                    "related_projects_count_by_code",
                    "countries_count_by_code",
                    "example_project_name_by_code",
                    "example_project_url_by_code",
                ]
            )
        else:
            link_counts_by_code = (
                links_with_code.groupby(["source_id", "methodology_code"], as_index=False)
                .agg(
                    related_projects_count_by_code=("source_project_id", "count"),
                    countries_count_by_code=(
                        "country",
                        lambda values: values.replace("", pd.NA).nunique(),
                    ),
                    example_project_name_by_code=("project_name", "first"),
                    example_project_url_by_code=("project_url", "first"),
                )
            )

    profiles = methodologies.merge(
        link_counts_by_name,
        on=["source_id", "methodology_name"],
        how="left",
    )
    profiles = profiles.merge(
        link_counts_by_code,
        on=["source_id", "methodology_code"],
        how="left",
    )
    if documents.empty:
        documents = pd.DataFrame(columns=["source_id", "document_title"])
    else:
        documents = documents.fillna("").copy()

    profiles["related_documents_count"] = profiles.apply(
        lambda row: count_related_documents(row, documents),
        axis=1,
    )
    profiles["related_projects_count"] = profiles["related_projects_count"].fillna(
        profiles["related_projects_count_by_code"]
    )
    profiles["countries_count"] = profiles["countries_count"].fillna(
        profiles["countries_count_by_code"]
    )
    profiles["example_project_name"] = profiles["example_project_name"].fillna(
        profiles["example_project_name_by_code"]
    )
    profiles["example_project_url"] = profiles["example_project_url"].fillna(
        profiles["example_project_url_by_code"]
    )
    profiles["related_projects_count"] = profiles["related_projects_count"].fillna(0).astype(int)
    profiles["countries_count"] = profiles["countries_count"].fillna(0).astype(int)
    profiles["example_project_name"] = profiles["example_project_name"].fillna("")
    profiles["example_project_url"] = profiles["example_project_url"].fillna("")
    profiles["notes"] = profiles.get("notes", "")
    profiles.loc[
        profiles["related_documents_count"] == 0,
        "notes",
    ] = profiles.loc[
        profiles["related_documents_count"] == 0,
        "notes",
    ].astype(str).str.strip() + "; no clear methodology-specific document match"
    profiles["notes"] = profiles["notes"].astype(str).str.strip("; ")

    output = pd.DataFrame()
    output["source_id"] = profiles["source_id"]
    output["source_name"] = profiles["source_name"]
    output["methodology_name"] = profiles["methodology_name"]
    output["methodology_code"] = profiles.get("methodology_code", "")
    output["version"] = profiles.get("version", "")
    output["related_projects_count"] = profiles["related_projects_count"]
    output["related_documents_count"] = profiles["related_documents_count"]
    output["countries_count"] = profiles["countries_count"]
    output["example_project_name"] = profiles["example_project_name"]
    output["example_project_url"] = profiles["example_project_url"]
    output["notes"] = profiles["notes"]
    return output[UNIFIED_COLUMNS].fillna("")


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    profiles = build_methodology_profiles()
    profiles.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Built {len(profiles)} methodology profile rows")
    print(f"Saved to: {OUTPUT_CSV}")
    print("\nPreview:")
    print(profiles.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
