from pathlib import Path
from urllib.parse import urljoin
import re

import pandas as pd
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_PATH = PROJECT_ROOT / "data" / "raw" / "jcm_mn" / "rules_and_guidelines.html"
OUT_PATH = PROJECT_ROOT / "data" / "processed" / "jcm_mn" / "rules_forms.csv"

SOURCE_URL = "https://www.jcm.go.jp/jc/mn-rules-and-guidelines"
BASE_URL = "https://www.jcm.go.jp"

FORM_NAME_MAP = {
    "F_PIN": "Project Idea Note",
    "F_MoC": "Modalities of Communication Statement Form",
    "F_Asst_Req": "Assessment of Reference Emissions Request Form",
    "F_Crd_Allc": "Percentage of Credit Allocation Form",
    "F_Reg_Req": "Project Registration Request Form",
    "F_Imp_Rep": "Project Implementation Report Form",
    "F_Iss_Req": "Credits Issuance Request Form",
    "F_Ren_Req": "Renewal of Crediting Period Request Form",
    "F_AMR_Req": "Approved Methodology Revision Request Form",
    "F_PRC_Req": "Post-Registration Change Request Form",
    "F_RW_Req": "Registration Request Withdrawal Form",
    "F_PW_Req": "Project Withdrawal Request Form",
    "F_IW_Req": "Issuance Request Withdrawal Form",
    "F_PM": "Proposed Methodology Form",
    "F_PMS": "Proposed Methodology Spreadsheet",
    "F_PDD": "Project Design Document Form",
    "F_SDIP": "Sustainable Development Implementation Plan Form",
    "F_SDIR": "Sustainable Development Implementation Report Form",
    "F_TPE": "Application Form for Designation as a Third-Party Entity",
    "F_Val_Rep": "Validation Report Form",
    "F_Vrf_Rep": "Verification Report Form",
}


def clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def infer_file_format(url: str) -> str:
    lower = url.lower().split("?")[0]

    if lower.endswith(".pdf"):
        return "PDF"
    if lower.endswith(".docx"):
        return "DOCX"
    if lower.endswith(".doc"):
        return "DOC"
    if lower.endswith(".xlsx"):
        return "XLSX"
    if lower.endswith(".xls"):
        return "XLS"
    if lower.endswith(".zip"):
        return "ZIP"

    return "HTML"


def infer_document_title(url: str, link_text: str) -> str:
    filename = Path(url.split("?")[0]).name

    if "bilateral_document" in filename:
        return "Bilateral Document"

    if "modification_bilat_doc" in filename:
        return "Modification of Bilateral Document"

    if "JCM_MN_RG" in filename:
        return "Rules and Guidelines"

    for code, title in FORM_NAME_MAP.items():
        if code in filename:
            return title

    if "Rules_and_Guidelines" in filename:
        return "Download All Rules and Guidelines"

    if "Forms_Mongolia" in filename:
        return "Download All Forms"

    text = clean_text(link_text)
    text = re.sub(r"\[(PDF|WORD|EXCEL|ZIP)\]", "", text, flags=re.IGNORECASE)
    text = clean_text(text)

    return text or filename


def infer_section(title: str, file_format: str) -> str:
    if file_format == "ZIP":
        return "Archive"

    if title in [
        "Bilateral Document",
        "Modification of Bilateral Document",
        "Rules and Guidelines",
    ]:
        return "Rules and Guidelines"

    return "Forms"


def parse_rules_forms():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Missing file: {RAW_PATH}")

    html = RAW_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    records = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if not href or href.startswith("#"):
            continue

        full_url = urljoin(BASE_URL, href)
        file_format = infer_file_format(full_url)

        if file_format == "HTML":
            continue

        link_text = a.get_text(" ", strip=True)
        title = infer_document_title(full_url, link_text)
        section = infer_section(title, file_format)

        category = "General" if title in [
            "Bilateral Document",
            "Modification of Bilateral Document",
        ] else "Project Cycle"

        records.append(
            {
                "standard": "JCM",
                "mechanism": "Joint Crediting Mechanism",
                "host_country": "Mongolia",
                "category": category,
                "section": section,
                "document_title": title,
                "file_format": file_format,
                "file_url": full_url,
                "source_url": SOURCE_URL,
            }
        )

    df = pd.DataFrame(records)

    df = df.drop_duplicates(
        subset=["document_title", "file_format", "file_url"]
    ).sort_values(
        ["category", "section", "document_title", "file_format"]
    ).reset_index(drop=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Parsed {len(df)} rules/forms records")
    print(f"Saved to: {OUT_PATH}")
    print("\nPreview:")
    print(df.head(30).to_string(index=False))


if __name__ == "__main__":
    parse_rules_forms()
