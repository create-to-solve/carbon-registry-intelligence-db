from pathlib import Path
import re

import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "puro_earth" / "puro_issuances_all.csv"
SOURCE_URL = "https://registry.puro.earth/issuances"
MAX_PAGES = 100

OUTPUT_COLUMNS = [
    "issued_date",
    "issued_qty",
    "project_name",
    "supplier",
    "methodology",
    "durability",
    "project_url",
    "project_id",
    "page_number",
    "source_url",
]

NEXT_BUTTON_SELECTORS = [
    'button[aria-label*="next" i]',
    'a[aria-label*="next" i]',
    'button:has-text("Next")',
    'a:has-text("Next")',
    "xpath=//button[not(ancestor::table) and .//*[contains(@class, 'lucide-arrow-right')]]",
    "xpath=//a[not(ancestor::table) and .//*[contains(@class, 'lucide-arrow-right')]]",
    "xpath=//button[not(ancestor::table) and .//*[contains(@class, 'lucide-chevron-right')]]",
    "xpath=//a[not(ancestor::table) and .//*[contains(@class, 'lucide-chevron-right')]]",
]


def clean_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def parse_number(value: str | None):
    text = clean_text(value)
    if not text:
        return None
    return pd.to_numeric(text.replace(",", ""), errors="coerce")


def extract_project_id(project_url: str) -> str:
    match = re.search(r"/projects/([^/?#]+)", project_url)
    return match.group(1) if match else ""


def find_next_button(page):
    for selector in NEXT_BUTTON_SELECTORS:
        locator = page.locator(selector).last
        if not locator.count():
            continue

        try:
            if locator.is_visible() and locator.is_enabled():
                return locator
        except PlaywrightTimeoutError:
            continue

    return None


def extract_rows(page, page_number: int) -> list[dict]:
    records = []
    rows = page.locator("table tbody tr")

    for row_index in range(rows.count()):
        row = rows.nth(row_index)
        cells = [clean_text(value) for value in row.locator("td").all_inner_texts()]
        if len(cells) < 6:
            continue

        project_link = row.locator('a[href*="/projects/"]').first
        project_url = ""
        if project_link.count():
            href = project_link.get_attribute("href") or ""
            project_url = href if href.startswith("http") else f"https://registry.puro.earth{href}"

        records.append(
            {
                "issued_date": cells[0],
                "issued_qty": parse_number(cells[1]),
                "project_name": cells[2],
                "supplier": cells[3],
                "methodology": cells[4],
                "durability": cells[5],
                "project_url": project_url,
                "project_id": extract_project_id(project_url),
                "page_number": page_number,
                "source_url": SOURCE_URL,
            }
        )

    return records


def row_signature(record: dict) -> tuple:
    return (
        record.get("issued_date", ""),
        record.get("issued_qty", ""),
        record.get("project_id", ""),
        record.get("project_name", ""),
        record.get("supplier", ""),
        record.get("methodology", ""),
        record.get("durability", ""),
    )


def click_next(page, current_first_row: str) -> bool:
    next_button = find_next_button(page)
    if next_button is None:
        print("Next button not found or disabled.")
        return False

    next_button.click()
    try:
        page.wait_for_function(
            """firstRowBefore => {
                const firstRow = document.querySelector("table tbody tr");
                return firstRow && firstRow.innerText !== firstRowBefore;
            }""",
            arg=current_first_row,
            timeout=30000,
        )
    except PlaywrightTimeoutError:
        page.wait_for_timeout(2000)

    return True


def parse_issuances() -> pd.DataFrame:
    records = []
    seen_page_signatures = set()
    seen_row_signatures = set()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(SOURCE_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("table tbody tr", timeout=30000)

            for page_number in range(1, MAX_PAGES + 1):
                current_url = page.url
                current_first_row = page.locator("table tbody tr").first.inner_text()
                page_records = extract_rows(page, page_number)
                page_signature = tuple(row_signature(record) for record in page_records)

                print(f"Page {page_number}: {len(page_records)} rows ({current_url})")

                if not page_records:
                    print("Stopping: no rows detected.")
                    break

                if page_signature in seen_page_signatures:
                    print("Stopping: pagination loop detected.")
                    break
                seen_page_signatures.add(page_signature)

                new_rows = 0
                for record in page_records:
                    signature = row_signature(record)
                    if signature in seen_row_signatures:
                        continue
                    seen_row_signatures.add(signature)
                    records.append(record)
                    new_rows += 1

                if new_rows == 0:
                    print("Stopping: no new rows detected.")
                    break

                if not click_next(page, current_first_row):
                    break
            else:
                print(f"Stopping: reached MAX_PAGES={MAX_PAGES}.")
        finally:
            page.close()
            browser.close()

    df = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    if not df.empty:
        df["issued_qty"] = pd.to_numeric(df["issued_qty"], errors="coerce")

    return df


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df = parse_issuances().drop_duplicates(
        subset=[
            "issued_date",
            "issued_qty",
            "project_id",
            "project_name",
            "supplier",
            "methodology",
            "durability",
        ]
    )
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"\nParsed {len(df)} Puro Earth issuances")
    print(f"Saved to: {OUTPUT_CSV}")
    print("\nPreview:")
    print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
