from pathlib import Path
from datetime import datetime
import re
import html

import pandas as pd
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_HTML = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "jcm_mn"
    / "projects.html"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jcm_mn"
)

ALL_PROJECTS_CSV = PROCESSED_DIR / "projects_all_jcm.csv"
MN_PROJECTS_CSV = PROCESSED_DIR / "projects_mongolia.csv"


def parse_jcm_short_date(value: str) -> str | None:
    if not value:
        return None

    value = value.strip()

    if value == "":
        return None

    try:
        return datetime.strptime(value, "%d %b %y").date().isoformat()
    except ValueError:
        return None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(value.split()).strip()


def extract_href_from_text(value: str | None, base_url: str = "https://www.jcm.go.jp") -> str | None:
    if not value:
        return None

    match = re.search(r'href="([^"]+)"', str(value))

    if not match:
        return None

    href = match.group(1)

    if href.startswith("http"):
        return href

    return base_url + href


def parse_projects(html_path: Path = RAW_HTML) -> pd.DataFrame:
    html_text = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html_text, "lxml")

    table = soup.find("table")
    if table is None:
        raise ValueError(f"No table found in {html_path}")

    rows = []

    for tr in table.find_all("tr")[1:]:
        cells_raw = tr.find_all(["td", "th"])

        cells = [
            c.get_text(" ", strip=True)
            for c in cells_raw
        ]

        if len(cells) < 9:
            continue

        methodology_raw = cells[7]
        methodology_title_raw = cells[8]

        row = {
            "standard": "JCM",
            "reference_no": clean_text(cells[0]),
            "host_country": clean_text(cells[1]),
            "project_title": clean_text(cells[2]),
            "status": clean_text(cells[3]),
            "registration_date_raw": clean_text(cells[4]),
            "registration_date": parse_jcm_short_date(clean_text(cells[4])),
            "host_country_participant": clean_text(cells[5]),
            "japanese_participant": clean_text(cells[6]),
            "methodology_no_raw": methodology_raw,
            "methodology_no": clean_text(methodology_raw),
            "methodology_title_raw": methodology_title_raw,
            "methodology_title": clean_text(methodology_title_raw),
            "methodology_url": extract_href_from_text(methodology_raw),
            "source_url": "https://www.jcm.go.jp/jc/mn-projects/",
        }

        rows.append(row)

    return pd.DataFrame(rows)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_all = parse_projects()

    df_mn = df_all[
        df_all["reference_no"]
        .fillna("")
        .str.startswith("MN")
    ].copy()

    df_all.to_csv(ALL_PROJECTS_CSV, index=False, encoding="utf-8")
    df_mn.to_csv(MN_PROJECTS_CSV, index=False, encoding="utf-8")

    print(f"Parsed {len(df_all)} total JCM projects")
    print(f"Saved all projects to: {ALL_PROJECTS_CSV}")

    print(f"\nFiltered {len(df_mn)} Mongolia projects")
    print(f"Saved Mongolia projects to: {MN_PROJECTS_CSV}")

    print("\nMongolia preview:")
    print(
        df_mn[
            [
                "reference_no",
                "project_title",
                "status",
                "registration_date",
                "methodology_no",
                "methodology_url",
            ]
        ]
    )


if __name__ == "__main__":
    main()