from pathlib import Path
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_HTML = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "jcm_mn"
    / "methodologies.html"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jcm_mn"
)

OUTPUT_CSV = PROCESSED_DIR / "methodologies.csv"


def parse_jcm_short_date(value: str) -> str | None:
    """
    Convert dates like '20 Dec 24' into ISO format: '2024-12-20'.
    Returns None if parsing fails.
    """
    if not value:
        return None

    value = value.strip()

    try:
        return datetime.strptime(value, "%d %b %y").date().isoformat()
    except ValueError:
        return None


def parse_yyyymmdd(value: str) -> str | None:
    """
    Convert dates like '20240731' into ISO format: '2024-07-31'.
    Returns None if parsing fails.
    """
    if not value:
        return None

    value = value.strip()

    try:
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def parse_methodologies(html_path: Path = RAW_HTML) -> pd.DataFrame:
    """
    Parse the JCM Mongolia methodologies table into a clean DataFrame.
    """
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    table = soup.find("table")
    if table is None:
        raise ValueError(f"No table found in {html_path}")

    rows = []

    for tr in table.find_all("tr")[1:]:
        cells = [
            c.get_text(" ", strip=True)
            for c in tr.find_all(["td", "th"])
        ]

        if len(cells) < 8:
            continue

        row = {
            "standard": "JCM",
            "mechanism": "Mongolia-Japan JCM",
            "host_country": cells[1] if len(cells) > 1 else None,
            "methodology_code": cells[0] if len(cells) > 0 else None,
            "title": cells[2] if len(cells) > 2 else None,
            "status": cells[3] if len(cells) > 3 else None,
            "latest_version": cells[4] if len(cells) > 4 else None,
            "approval_date_raw": cells[5] if len(cells) > 5 else None,
            "approval_date": parse_jcm_short_date(cells[5]) if len(cells) > 5 else None,
            "proposed_methodology_code": cells[6] if len(cells) > 6 else None,
            "proponent": cells[7] if len(cells) > 7 else None,
            "sectoral_scope": cells[8] if len(cells) > 8 else None,
            "public_input_start_raw": cells[9] if len(cells) > 9 else None,
            "public_input_start": parse_yyyymmdd(cells[9]) if len(cells) > 9 else None,
            "public_input_end_raw": cells[10] if len(cells) > 10 else None,
            "public_input_end": parse_yyyymmdd(cells[10]) if len(cells) > 10 else None,
            "source_url": "https://www.jcm.go.jp/jc/mn-methodologies-proposed",
        }

        rows.append(row)

    return pd.DataFrame(rows)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = parse_methodologies()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Parsed {len(df)} methodologies")
    print(f"Saved to: {OUTPUT_CSV}")

    print("\nPreview:")
    print(
        df[
            [
                "methodology_code",
                "title",
                "status",
                "latest_version",
                "approval_date",
                "sectoral_scope",
            ]
        ]
    )


if __name__ == "__main__":
    main()