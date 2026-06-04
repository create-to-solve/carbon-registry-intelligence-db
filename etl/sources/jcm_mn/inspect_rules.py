from pathlib import Path
from bs4 import BeautifulSoup

RAW_PATH = Path("data/raw/jcm_mn/rules_and_guidelines.html")


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Missing file: {RAW_PATH}")

    html = RAW_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    print("\nTITLE:")
    print(soup.title)

    print("\nHEADINGS:")
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = tag.get_text(" ", strip=True)
        if text:
            print(f"{tag.name.upper()}: {text}")

    print("\nLINKS:")
    links = soup.find_all("a", href=True)
    print(f"Total links found: {len(links)}")

    for i, a in enumerate(links[:100], start=1):
        text = a.get_text(" ", strip=True)
        href = a["href"]
        print(f"{i}. {text} -> {href}")

    print("\nTABLES:")
    tables = soup.find_all("table")
    print(f"Tables found: {len(tables)}")

    for i, table in enumerate(tables):
        rows = table.find_all("tr")
        print(f"\nTABLE {i}")
        print(f"Rows: {len(rows)}")

        for row in rows[:5]:
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["th", "td"])]
            print(cells)


if __name__ == "__main__":
    main()