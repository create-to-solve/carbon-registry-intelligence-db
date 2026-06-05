from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "unified" / "evidence_requirements_seed.csv"

UNIFIED_COLUMNS = [
    "source_id",
    "source_name",
    "evidence_stage",
    "evidence_document_type",
    "document_title",
    "document_url",
    "relevance_note",
]


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Skipping missing source file: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def classify_jcm_stage(title) -> str:
    text = "" if pd.isna(title) else str(title).lower()

    if "sustainable development" in text or "sdip" in text:
        return "sustainable_development"
    if "methodology" in text or "reference emissions" in text:
        return "methodology_approval"
    if "validation" in text or "third-party entity" in text:
        return "validation"
    if "monitoring" in text:
        return "monitoring"
    if "verification" in text:
        return "verification"
    if "issuance" in text and "withdrawal" not in text:
        return "issuance"
    if "credit allocation" in text or "allocation" in text:
        return "credit_allocation"
    if (
        "withdrawal" in text
        or "change" in text
        or "revision" in text
        or "modalities of communication" in text
    ):
        return "withdrawal_or_change"
    if "project design document" in text or "pdd" in text or "registration" in text:
        return "project_design"
    return "other"


def evidence_document_type(title, file_format) -> str:
    title_text = "" if pd.isna(title) else str(title)
    format_text = "" if pd.isna(file_format) else str(file_format)
    if format_text:
        return f"{title_text} ({format_text})"
    return title_text


def build_jcm_evidence_seed() -> pd.DataFrame:
    rules = read_csv_if_exists(PROCESSED_DIR / "jcm_mn" / "rules_forms.csv")
    if rules.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    rules = rules.fillna("").copy()
    output = pd.DataFrame(index=rules.index)
    output["source_id"] = "jcm_mn"
    output["source_name"] = "JCM Mongolia-Japan"
    output["evidence_stage"] = rules["document_title"].apply(classify_jcm_stage)
    output["evidence_document_type"] = [
        evidence_document_type(title, file_format)
        for title, file_format in zip(rules["document_title"], rules["file_format"])
    ]
    output["document_title"] = rules["document_title"]
    output["document_url"] = rules["file_url"]
    output["relevance_note"] = (
        "Seeded from JCM rules/forms title; PDF/DOCX contents not parsed"
    )
    return output[UNIFIED_COLUMNS]


def build_puro_evidence_seed() -> pd.DataFrame:
    documents = read_csv_if_exists(PROCESSED_DIR / "unified" / "documents.csv")
    if documents.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    docs = documents.fillna("").copy()
    docs = docs[docs["source_id"] == "puro_earth"].copy()
    if docs.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    clear_mask = (
        docs["document_title"].str.contains("methodolog|document library", case=False, na=False)
        | docs["document_category"].str.contains("methodolog|document", case=False, na=False)
        | docs["document_url"].str.contains("document-library", case=False, na=False)
    )
    docs = docs[clear_mask].copy()
    if docs.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    output = pd.DataFrame(index=docs.index)
    output["source_id"] = "puro_earth"
    output["source_name"] = "Puro Earth"
    output["evidence_stage"] = "methodology_approval"
    output["evidence_document_type"] = docs["document_type"]
    output["document_title"] = docs["document_title"]
    output["document_url"] = docs["document_url"]
    output["relevance_note"] = (
        "Seeded from Puro document-library/reconnaissance title only; contents not parsed"
    )
    return output[UNIFIED_COLUMNS]


def build_evidence_requirements_seed() -> pd.DataFrame:
    frames = [
        build_jcm_evidence_seed(),
        build_puro_evidence_seed(),
    ]
    df = pd.concat(frames, ignore_index=True)
    return df.fillna("")


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    seed = build_evidence_requirements_seed()
    seed.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Built {len(seed)} evidence requirement seed rows")
    print(f"Saved to: {OUTPUT_CSV}")
    print("\nRows by stage:")
    if seed.empty:
        print("None")
    else:
        print(seed["evidence_stage"].value_counts().to_string())
    print("\nPreview:")
    print(seed.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
