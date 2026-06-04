from pathlib import Path
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[3]

HTML_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "jcm_mn"
    / "issuance.html"
)

html = HTML_FILE.read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(html, "lxml")

print("\nTITLE:")
print(soup.title)

tables = soup.find_all("table")

print("\nTABLES FOUND:")
print(len(tables))

for i, table in enumerate(tables):
    rows = table.find_all("tr")

    print("\n" + "=" * 80)
    print(f"TABLE {i}")
    print(f"ROWS: {len(rows)}")

    for row in rows[:20]:
        cols = row.find_all(["td", "th"])
        values = [c.get_text(" ", strip=True) for c in cols]
        print(values)