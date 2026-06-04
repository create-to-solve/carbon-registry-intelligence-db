from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECTS_CSV = PROJECT_ROOT / "data" / "processed" / "unified" / "projects.csv"
ISSUANCES_CSV = PROJECT_ROOT / "data" / "processed" / "unified" / "issuances.csv"


def print_section(title: str) -> None:
    print(f"\n{'=' * 80}")
    print(title)
    print("=" * 80)


def print_series(series: pd.Series, empty_message: str = "None") -> None:
    if series.empty:
        print(empty_message)
    else:
        print(series.to_string())


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return pd.read_csv(path).fillna("")


def missing_values(df: pd.DataFrame) -> pd.Series:
    return df.eq("").sum().sort_values(ascending=False)


def duplicate_project_ids(projects: pd.DataFrame) -> pd.DataFrame:
    with_ids = projects[projects["source_project_id"] != ""].copy()
    duplicate_mask = with_ids.duplicated(
        subset=["source_id", "source_project_id"],
        keep=False,
    )
    duplicates = with_ids[duplicate_mask].copy()
    return duplicates.sort_values(["source_id", "source_project_id"])


def projects_without_methodology(projects: pd.DataFrame) -> pd.DataFrame:
    return projects[projects["methodology_name"] == ""].copy()


def issuances_without_matching_project(
    projects: pd.DataFrame,
    issuances: pd.DataFrame,
) -> pd.DataFrame:
    project_keys = set(
        zip(
            projects["source_id"].astype(str),
            projects["source_project_id"].astype(str),
        )
    )

    mask = [
        (source_id, project_id) not in project_keys
        for source_id, project_id in zip(
            issuances["source_id"].astype(str),
            issuances["source_project_id"].astype(str),
        )
    ]

    return issuances[mask].copy()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")

    projects = load_csv(PROJECTS_CSV)
    issuances = load_csv(ISSUANCES_CSV)
    issuances["issued_quantity"] = pd.to_numeric(
        issuances["issued_quantity"],
        errors="coerce",
    )

    print_section("Unified Files")
    print(f"Projects:  {PROJECTS_CSV}")
    print(f"Issuances: {ISSUANCES_CSV}")

    print_section("Project Row Counts by Source")
    print_series(projects["source_id"].value_counts())

    print_section("Issuance Row Counts by Source")
    print_series(issuances["source_id"].value_counts())

    print_section("Project Missing Values by Column")
    print_series(missing_values(projects))

    print_section("Issuance Missing Values by Column")
    print_series(missing_values(issuances.fillna("")))

    print_section("Duplicate source_project_id by Source")
    duplicates = duplicate_project_ids(projects)
    if duplicates.empty:
        print("None")
    else:
        counts = (
            duplicates
            .groupby(["source_id", "source_project_id"], as_index=False)
            .size()
            .rename(columns={"size": "duplicate_rows"})
            .sort_values(["source_id", "source_project_id"])
        )
        print(counts.to_string(index=False))

    print_section("Top Countries")
    top_countries = (
        projects[projects["country"] != ""]["country"]
        .value_counts()
        .head(20)
    )
    print_series(top_countries)

    print_section("Top Methodologies")
    top_methodologies = (
        projects[projects["methodology_name"] != ""]["methodology_name"]
        .value_counts()
        .head(20)
    )
    print_series(top_methodologies)

    print_section("Issued Quantity Totals by Source")
    issued_totals = (
        issuances
        .groupby("source_id")["issued_quantity"]
        .sum()
        .sort_values(ascending=False)
    )
    print_series(issued_totals)

    print_section("Projects with No Methodology")
    no_methodology = projects_without_methodology(projects)
    print(f"Count: {len(no_methodology)}")
    if not no_methodology.empty:
        print(
            no_methodology[
                [
                    "source_id",
                    "source_project_id",
                    "project_name",
                    "country",
                    "status",
                ]
            ].head(50).to_string(index=False)
        )

    print_section("Issuances with No Matching Unified Project")
    unmatched = issuances_without_matching_project(projects, issuances.fillna(""))
    print(f"Count: {len(unmatched)}")
    if not unmatched.empty:
        print(
            unmatched[
                [
                    "source_id",
                    "source_project_id",
                    "project_name",
                    "issuance_date",
                    "issued_quantity",
                ]
            ].head(50).to_string(index=False)
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
