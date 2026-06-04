from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "puro_earth"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "puro_earth"
OUTPUT_CSV = PROCESSED_DIR / "puro_source_recon.csv"

SOURCE = "Puro Earth"
PAGES = [
    {
        "page_name": "document_library",
        "url": "https://puro.earth/cdr-infrastructure/methodologies/document-library/",
        "raw_filename": "document_library.html",
        "possible_entities": "methodologies, methodology documents",
    },
    {
        "page_name": "registry_home",
        "url": "https://registry.puro.earth/",
        "raw_filename": "registry_home.html",
        "possible_entities": "registry overview",
    },
    {
        "page_name": "projects",
        "url": "https://registry.puro.earth/projects",
        "raw_filename": "projects.html",
        "possible_entities": "projects",
    },
    {
        "page_name": "issuances",
        "url": "https://registry.puro.earth/issuances",
        "raw_filename": "issuances.html",
        "possible_entities": "issuances, credit records",
    },
]


def useful_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    links = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = urljoin(base_url, href)
        if full_url not in links:
            links.append(full_url)

    return links


def infer_notes(soup: BeautifulSoup, links_count: int, tables_count: int) -> str:
    notes = []

    if tables_count:
        notes.append("HTML tables present")
    else:
        notes.append("No HTML tables found")

    if soup.find(attrs={"id": "__next"}) or soup.find(attrs={"id": "root"}):
        notes.append("page may be JavaScript-rendered")

    if links_count == 0:
        notes.append("no useful links found in static HTML")

    return "; ".join(notes)


def inspect_page(session: requests.Session, page: dict) -> dict:
    response = session.get(page["url"], timeout=30)
    html = response.text

    raw_path = RAW_DIR / page["raw_filename"]
    raw_path.write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "lxml")
    links = useful_links(soup, page["url"])
    tables_count = len(soup.find_all("table"))

    print(f"\n{page['page_name']}")
    print(f"Status code: {response.status_code}")
    print(f"Links: {len(links)}")
    print(f"Tables: {tables_count}")
    print("First 20 useful links:")
    for link in links[:20]:
        print(f"- {link}")

    return {
        "source": SOURCE,
        "page_name": page["page_name"],
        "url": page["url"],
        "http_status": response.status_code,
        "html_length": len(html),
        "tables_found": tables_count,
        "links_found": len(links),
        "possible_entities": page["possible_entities"],
        "notes": infer_notes(soup, len(links), tables_count),
    }


def inspect_registry() -> pd.DataFrame:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "global-carbon-method-db/0.1 (+source reconnaissance)",
        }
    )

    records = [inspect_page(session, page) for page in PAGES]
    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"\nSaved reconnaissance CSV to: {OUTPUT_CSV}")
    return df


if __name__ == "__main__":
    inspect_registry()
