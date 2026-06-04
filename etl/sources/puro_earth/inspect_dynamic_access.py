from pathlib import Path
from urllib.parse import urljoin
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "puro_earth"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "puro_earth"
OUTPUT_CSV = PROCESSED_DIR / "puro_dynamic_access_notes.csv"

KEYWORDS = [
    "api",
    "project",
    "issuance",
    "transaction",
    "download",
    "page",
    "graphql",
    "json",
]

PAGES = [
    {
        "page_name": "projects",
        "url": "https://registry.puro.earth/projects",
        "snapshot": RAW_DIR / "projects.html",
    },
    {
        "page_name": "issuances",
        "url": "https://registry.puro.earth/issuances",
        "snapshot": RAW_DIR / "issuances.html",
    },
]

QUERY_TESTS = ["", "?page=2", "?page=2&limit=10", "?limit=100"]


def contains_keyword(value: str) -> bool:
    lower = value.lower()
    return any(keyword in lower for keyword in KEYWORDS)


def useful_urls_from_html(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    urls = []

    for tag in soup.find_all(["a", "script", "link"], href=True):
        url = urljoin(base_url, tag["href"].strip())
        if contains_keyword(url) and url not in urls:
            urls.append(url)

    for tag in soup.find_all("script", src=True):
        url = urljoin(base_url, tag["src"].strip())
        if contains_keyword(url) and url not in urls:
            urls.append(url)

    patterns = [
        r'https?://[^"\'<>\s]+',
        r'/(?:api|projects?|issuances?|transactions?|downloads?|graphql|[^"\'<>\s]*\.json)[^"\'<>\s]*',
    ]

    for pattern in patterns:
        for match in re.findall(pattern, html, flags=re.IGNORECASE):
            url = urljoin(base_url, match.rstrip("\\"))
            if contains_keyword(url) and url not in urls:
                urls.append(url)

    return urls


def rows_detected(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        return 0
    return len(table.find_all("tr")) - 1


def inspect_saved_snapshot(page: dict) -> dict:
    if not page["snapshot"].exists():
        html = ""
        notes = f"Missing saved snapshot: {page['snapshot']}"
    else:
        html = page["snapshot"].read_text(encoding="utf-8", errors="ignore")
        notes = "saved snapshot scan"

    urls = useful_urls_from_html(html, page["url"]) if html else []

    print(f"\nSaved snapshot: {page['page_name']}")
    print(f"Rows detected: {rows_detected(html)}")
    print(f"Useful href/src/API-like URLs: {len(urls)}")
    for url in urls:
        print(f"- {url}")

    return {
        "page_name": page["page_name"],
        "test_url": str(page["snapshot"].relative_to(PROJECT_ROOT)),
        "status_code": "",
        "html_length": len(html),
        "rows_detected": rows_detected(html),
        "useful_links_detected": len(urls),
        "notes": notes,
    }


def inspect_url(session: requests.Session, page_name: str, test_url: str) -> dict:
    response = session.get(test_url, timeout=30)
    html = response.text
    urls = useful_urls_from_html(html, test_url)

    note_parts = ["query probe"]
    if rows_detected(html) > 10:
        note_parts.append("more than first 10 table rows detected")
    else:
        note_parts.append("did not expose more than first 10 table rows in static HTML")

    print(f"\nProbe: {page_name} {test_url}")
    print(f"Status code: {response.status_code}")
    print(f"HTML length: {len(html)}")
    print(f"Rows detected: {rows_detected(html)}")
    print(f"Useful href/src/API-like URLs: {len(urls)}")
    for url in urls:
        print(f"- {url}")

    return {
        "page_name": page_name,
        "test_url": test_url,
        "status_code": response.status_code,
        "html_length": len(html),
        "rows_detected": rows_detected(html),
        "useful_links_detected": len(urls),
        "notes": "; ".join(note_parts),
    }


def inspect_dynamic_access() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    records = [inspect_saved_snapshot(page) for page in PAGES]

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "global-carbon-method-db/0.1 (+dynamic access reconnaissance)",
        }
    )

    for page in PAGES:
        for query in QUERY_TESTS:
            records.append(inspect_url(session, page["page_name"], f"{page['url']}{query}"))

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"\nSaved dynamic access notes to: {OUTPUT_CSV}")
    return df


if __name__ == "__main__":
    inspect_dynamic_access()
