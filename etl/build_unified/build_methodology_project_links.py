from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "unified" / "methodology_project_links.csv"

UNIFIED_COLUMNS = [
    "source_id",
    "source_name",
    "methodology_name",
    "methodology_code",
    "source_project_id",
    "project_name",
    "country",
    "project_url",
]


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Skipping missing source file: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def extract_jcm_methodology_code(methodology_name) -> str:
    if pd.isna(methodology_name):
        return ""

    match = re.search(r"\bMN_AM\d+\b", str(methodology_name))
    if not match:
        return ""
    return match.group(0)


def build_methodology_project_links() -> pd.DataFrame:
    projects = read_csv_if_exists(PROCESSED_DIR / "unified" / "projects.csv")
    if projects.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    projects = projects.fillna("").copy()
    projects = projects[projects["methodology_name"].astype(str).str.strip() != ""].copy()
    if projects.empty:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    links = pd.DataFrame(index=projects.index)
    links["source_id"] = projects["source_id"]
    links["source_name"] = projects["source_name"]
    links["methodology_name"] = projects["methodology_name"]
    links["methodology_code"] = ""
    jcm_mask = projects["source_id"] == "jcm_mn"
    links.loc[jcm_mask, "methodology_code"] = projects.loc[
        jcm_mask,
        "methodology_name",
    ].apply(extract_jcm_methodology_code)
    links["source_project_id"] = projects["source_project_id"]
    links["project_name"] = projects["project_name"]
    links["country"] = projects["country"]
    links["project_url"] = projects["project_url"]
    return links[UNIFIED_COLUMNS].fillna("")


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    links = build_methodology_project_links()
    links.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Built {len(links)} methodology-project link rows")
    print(f"Saved to: {OUTPUT_CSV}")
    print("\nTop methodologies:")
    if links.empty:
        print("None")
    else:
        top = links["methodology_name"].value_counts().head(20)
        print(top.to_string())


if __name__ == "__main__":
    main()
