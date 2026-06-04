from pathlib import Path
import re

import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "puro_earth"

PAGES = [
    {
        "page_name": "projects",
        "url": "https://registry.puro.earth/projects",
        "output_csv": PROCESSED_DIR / "puro_projects_playwright_sample.csv",
    },
    {
        "page_name": "issuances",
        "url": "https://registry.puro.earth/issuances",
        "output_csv": PROCESSED_DIR / "puro_issuances_playwright_sample.csv",
    },
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


def clean_column_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def extract_table_rows(page, page_number: int) -> list[dict]:
    headers = [
        clean_column_name(header)
        for header in page.locator("table thead th").all_inner_texts()
    ]
    headers = [header for header in headers if header]

    records = []
    rows = page.locator("table tbody tr")

    for row_index in range(rows.count()):
        row = rows.nth(row_index)
        cells = row.locator("td").all_inner_texts()
        values = {
            headers[index]: " ".join(cells[index].split())
            for index in range(min(len(headers), len(cells)))
        }

        project_link = row.locator('a[href*="/projects/"]').first
        project_url = ""
        project_id = ""

        if project_link.count():
            href = project_link.get_attribute("href") or ""
            project_url = href if href.startswith("http") else f"https://registry.puro.earth{href}"
            match = re.search(r"/projects/([^/?#]+)", project_url)
            project_id = match.group(1) if match else ""

        values["project_url"] = project_url
        values["project_id"] = project_id
        values["page_number"] = page_number
        records.append(values)

    return records


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


def probe_page(browser, page_info: dict) -> None:
    page = browser.new_page()
    page.goto(page_info["url"], wait_until="networkidle", timeout=60000)
    page.wait_for_selector("table tbody tr", timeout=30000)

    before_url = page.url
    page_one_records = extract_table_rows(page, page_number=1)
    next_button = find_next_button(page)

    print(f"\n{page_info['page_name']}")
    print(f"Current URL before next: {before_url}")
    print(f"Rows captured on page 1: {len(page_one_records)}")
    print(f"Next button found: {next_button is not None}")

    page_two_records = []
    after_url = page.url

    if next_button is not None:
        first_row_before = page.locator("table tbody tr").first.inner_text()
        next_button.click()
        try:
            page.wait_for_function(
                """firstRowBefore => {
                    const firstRow = document.querySelector("table tbody tr");
                    return firstRow && firstRow.innerText !== firstRowBefore;
                }""",
                arg=first_row_before,
                timeout=30000,
            )
        except PlaywrightTimeoutError:
            page.wait_for_timeout(2000)

        after_url = page.url
        page_two_records = extract_table_rows(page, page_number=2)

    print(f"Current URL after next: {after_url}")
    print(f"Rows captured on page 2: {len(page_two_records)}")

    df = pd.DataFrame(page_one_records + page_two_records)
    page_info["output_csv"].parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(page_info["output_csv"], index=False, encoding="utf-8")
    print(f"Saved to: {page_info['output_csv']}")

    page.close()


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for page_info in PAGES:
                probe_page(browser, page_info)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
