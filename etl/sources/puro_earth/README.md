# Puro Earth Inspection

Inspection-only module for Puro Earth public methodology and registry pages.

This module saves raw HTML snapshots and writes a reconnaissance CSV with one row per inspected page. It does not parse project, methodology, or issuance entities yet.

## Inspected Pages

- `https://puro.earth/cdr-infrastructure/methodologies/document-library/`
- `https://registry.puro.earth/`
- `https://registry.puro.earth/projects`
- `https://registry.puro.earth/issuances`

## Outputs

Raw snapshots:

- `data/raw/puro_earth/document_library.html`
- `data/raw/puro_earth/registry_home.html`
- `data/raw/puro_earth/projects.html`
- `data/raw/puro_earth/issuances.html`

Processed reconnaissance:

- `data/processed/puro_earth/puro_source_recon.csv`

## Run

```powershell
python etl/sources/puro_earth/inspect_registry.py
```

The script prints each page name, HTTP status, link count, table count, and the first 20 useful links.

## Playwright Setup

Install the Chromium browser runtime before running Playwright probes:

```powershell
python -m playwright install chromium
```
