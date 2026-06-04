from pathlib import Path
from datetime import datetime
import re

import pandas as pd
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_HTML = PROJECT_ROOT / "data" / "raw" / "jcm_mn" / "issuance.html"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "jcm_mn"
OUTPUT_CSV = PROCESSED_DIR / "issuance_records.csv"


def clean_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def parse_jcm_short_date(value: str | None) -> str | None:
    value = clean_text(value)
    if not value or value == "N/A":
        return None
    try:
        return datetime.strptime(value, "%d %b %y").date().isoformat()
    except ValueError:
        return None


def parse_number(value: str | None) -> int | None:
    value = clean_text(value)
    if not value or value == "N/A":
        return None
    try:
        return int(value.replace(",", ""))
    except ValueError:
        return None


def parse_monitoring_period(value: str | None) -> tuple[str | None, str | None]:
    value = clean_text(value)
    if not value or " - " not in value:
        return None, None

    start_raw, end_raw = value.split(" - ", 1)
    return parse_jcm_short_date(start_raw), parse_jcm_short_date(end_raw)


def is_reference_no(value: str | None) -> bool:
    value = clean_text(value)
    return bool(re.match(r"^MN\d{3}$", value))


def is_country(value: str | None) -> bool:
    return clean_text(value) in {"Mongolia", "Japan"}


def make_record(
    project_title,
    reference_no,
    monitoring_period_raw,
    decision_date_raw,
    total_notified,
    country,
    notified_amount,
    issuance_date_raw,
    issued_amount,
):
    monitoring_start, monitoring_end = parse_monitoring_period(monitoring_period_raw)

    return {
        "standard": "JCM",
        "mechanism": "Mongolia-Japan JCM",
        "project_title": project_title,
        "reference_no": reference_no,
        "monitoring_period_raw": monitoring_period_raw,
        "monitoring_start": monitoring_start,
        "monitoring_end": monitoring_end,
        "decision_date_raw": decision_date_raw,
        "decision_date": parse_jcm_short_date(decision_date_raw),
        "total_notified": parse_number(total_notified),
        "country": country,
        "notified_amount": parse_number(notified_amount),
        "issuance_date_raw": issuance_date_raw,
        "issuance_date": parse_jcm_short_date(issuance_date_raw),
        "issued_amount": parse_number(issued_amount),
        "source_url": "https://www.jcm.go.jp/jc/mn-projects-issues",
    }


def parse_issuance(html_path: Path = RAW_HTML) -> pd.DataFrame:
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    tables = soup.find_all("table")
    if not tables:
        raise ValueError(f"No tables found in {html_path}")

    table = tables[0]

    rows = []

    current_project_title = ""
    current_reference_no = ""
    current_monitoring_period_raw = ""
    current_decision_date_raw = ""
    current_total_notified = ""

    for tr in table.find_all("tr"):
        cells = [
            clean_text(c.get_text(" ", strip=True))
            for c in tr.find_all(["td", "th"])
        ]

        if not cells:
            continue

        first = cells[0]

        if first in {"Project title", "Reference number"}:
            continue

        # Project title row
        if len(cells) == 1 and not is_reference_no(first) and not is_country(first):
            current_project_title = first
            continue

        # Full row:
        # MN006 | period | decision | total | country | notified | issuance date | issued
        if is_reference_no(first):
            current_reference_no = cells[0]
            current_monitoring_period_raw = cells[1] if len(cells) > 1 else ""
            current_decision_date_raw = cells[2] if len(cells) > 2 else ""
            current_total_notified = cells[3] if len(cells) > 3 else ""

            country = cells[4] if len(cells) > 4 else ""
            notified_amount = cells[5] if len(cells) > 5 else ""
            issuance_date_raw = cells[6] if len(cells) > 6 else ""
            issued_amount = cells[7] if len(cells) > 7 else ""

            rows.append(
                make_record(
                    current_project_title,
                    current_reference_no,
                    current_monitoring_period_raw,
                    current_decision_date_raw,
                    current_total_notified,
                    country,
                    notified_amount,
                    issuance_date_raw,
                    issued_amount,
                )
            )
            continue

        # Continuation row with blank reference number:
        # blank | new period | decision | country | notified | issuance date | issued
        if first == "" and len(cells) >= 7 and " - " in cells[1]:
            current_monitoring_period_raw = cells[1]
            current_decision_date_raw = cells[2]

            country = cells[3]
            notified_amount = cells[4]
            issuance_date_raw = cells[5]
            issued_amount = cells[6]

            rows.append(
                make_record(
                    current_project_title,
                    current_reference_no,
                    current_monitoring_period_raw,
                    current_decision_date_raw,
                    current_total_notified,
                    country,
                    notified_amount,
                    issuance_date_raw,
                    issued_amount,
                )
            )
            continue

        # Country allocation row:
        # Japan | notified | issuance date | issued
        if is_country(first):
            country = cells[0]
            notified_amount = cells[1] if len(cells) > 1 else ""
            issuance_date_raw = cells[2] if len(cells) > 2 else ""
            issued_amount = cells[3] if len(cells) > 3 else ""

            rows.append(
                make_record(
                    current_project_title,
                    current_reference_no,
                    current_monitoring_period_raw,
                    current_decision_date_raw,
                    current_total_notified,
                    country,
                    notified_amount,
                    issuance_date_raw,
                    issued_amount,
                )
            )
            continue

    df = pd.DataFrame(rows)

    # Remove completely empty country rows if any slipped through.
    if not df.empty:
        df = df[df["country"].isin(["Mongolia", "Japan"])].copy()

    return df


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = parse_issuance()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Parsed {len(df)} issuance allocation rows")
    print(f"Saved to: {OUTPUT_CSV}")

    print("\nPreview:")
    print(
        df[
            [
                "reference_no",
                "monitoring_period_raw",
                "country",
                "notified_amount",
                "issuance_date",
                "issued_amount",
            ]
        ].head(30)
    )


if __name__ == "__main__":
    main()