from pathlib import Path
from urllib.parse import urljoin
import re

import pandas as pd
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_HTML = PROJECT_ROOT / "data" / "raw" / "puro_earth" / "issuances.html"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "puro_earth" / "puro_issuances.csv"
SOURCE_URL = "https://registry.puro.earth/issuances"
BASE_URL = "https://registry.puro.earth"

OUTPUT_COLUMNS = [
    "issued_date",
    "issued_qty",
    "project_name",
    "supplier",
    "methodology",
    "durability",
    "project_url",
    "project_id",
    "source_url",
    "source_snapshot_path",
]


def clean_text(value: str | None) -> str:
    if value is None:
        return ""

    text = " ".join(str(value).split()).strip()
    text = text.replace("\uFFFD\u0080\u0093", "-")
    text = text.replace("\uFFFD\u0080\u0094", "-")

    # Some saved snapshots contain mojibake from the source response encoding.
    if any(marker in text for marker in ["Ã", "Â", "â", "\u0080", "\u0093", "\u0094"]):
        for _ in range(2):
            try:
                repaired = text.encode("latin1").decode("utf-8")
            except UnicodeError:
                break
            if repaired == text:
                break
            text = repaired

    return text.replace("\uFFFD", "-")


def parse_number(value: str | None):
    text = clean_text(value)
    if not text:
        return None
    return pd.to_numeric(text.replace(",", ""), errors="coerce")


def extract_project_id(project_url: str) -> str:
    match = re.search(r"/projects/([^/?#]+)", project_url)
    return match.group(1) if match else ""


def table_headers(table) -> list[str]:
    headers = []
    for th in table.find_all("th"):
        header = clean_text(th.get_text(" ", strip=True)).lower()
        header = re.sub(r"[^a-z0-9]+", "_", header).strip("_")
        headers.append(header)
    return headers


def parse_issuances(html_path: Path = RAW_HTML) -> pd.DataFrame:
    if not html_path.exists():
        raise FileNotFoundError(f"Missing file: {html_path}")

    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    table = soup.find("table")

    if table is None:
        print(f"No table found in {html_path}")
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    headers = table_headers(table)
    snapshot_path = html_path.relative_to(PROJECT_ROOT).as_posix()
    records = []

    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue

        values = {
            headers[index]: clean_text(cell.get_text(" ", strip=True))
            for index, cell in enumerate(cells)
            if index < len(headers) and headers[index]
        }

        project_cell_index = headers.index("project") if "project" in headers else 2
        project_cell = cells[project_cell_index] if project_cell_index < len(cells) else None
        project_link = project_cell.find("a", href=True) if project_cell else None
        project_url = urljoin(BASE_URL, project_link["href"]) if project_link else ""

        records.append(
            {
                "issued_date": clean_text(values.get("issued_date")),
                "issued_qty": parse_number(values.get("issued_qty")),
                "project_name": clean_text(values.get("project")),
                "supplier": clean_text(values.get("supplier")),
                "methodology": clean_text(values.get("methodology")),
                "durability": clean_text(values.get("durability")),
                "project_url": project_url,
                "project_id": extract_project_id(project_url),
                "source_url": SOURCE_URL,
                "source_snapshot_path": snapshot_path,
            }
        )

    df = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    if not df.empty:
        df["issued_qty"] = pd.to_numeric(df["issued_qty"], errors="coerce")

    return df


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df = parse_issuances()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Parsed {len(df)} Puro Earth issuances")
    print("Columns:")
    print(", ".join(df.columns))
    print("\nPreview:")
    print(df.head(10).to_string(index=False))
    print(f"\nSaved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
