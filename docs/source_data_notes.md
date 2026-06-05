# Source Data Notes

## JCM Mongolia-Japan

### How data was obtained

JCM Mongolia-Japan data is collected from public JCM Mongolia-Japan web pages. The repo includes source-specific scripts for fetching and parsing methodologies, projects, issuance allocation records, and rules/forms.

### Files and scripts involved

Processed files:

- `data/processed/jcm_mn/methodologies.csv`
- `data/processed/jcm_mn/projects_mongolia.csv`
- `data/processed/jcm_mn/issuance_records.csv`
- `data/processed/jcm_mn/rules_forms.csv`

Scripts:

- `etl/sources/jcm_mn/fetch_pages.py`
- `etl/sources/jcm_mn/parse_methodologies.py`
- `etl/sources/jcm_mn/parse_projects.py`
- `etl/sources/jcm_mn/parse_issuance.py`
- `etl/sources/jcm_mn/parse_rules.py`

### Fields available

- Methodology code, title, status, latest version, approval date, and sectoral scope.
- Project reference number, title, status, registration date, host country, participants, methodology details, and source URL.
- Issuance allocation rows with project reference, project title, issuance date, issued amount, country allocation, and source URL.
- Rules/forms metadata including section, document title, file format, and file URL.

### Known gaps

- This is a country-specific JCM sample focused on Mongolia-Japan, not the full JCM universe.
- Durability is not applicable to JCM credit rows in the current unified issuance schema.
- Some issuance rows may have blank dates or quantities because of source table structure.

### Extraction type

Sample/pilot extraction for a country-specific source.

## Gold Standard

### How data was obtained

Gold Standard data is imported from a public project export CSV. The current scope is project catalogue data only.

### Files and scripts involved

Raw/export file:

- `data/raw/GSF Registry Projects Export 2026-06-04.csv`

Processed file:

- `data/processed/gold_standard/gs_projects.csv`

Script:

- `etl/sources/gold_standard/parse_projects_export.py`

### Fields available

- Gold Standard project ID.
- Project name.
- Country.
- Status.
- Project type.
- Methodology where available.
- Project developer name.
- Estimated annual credits.
- Generated project detail URL.

### Known gaps

- No issuance data is included yet.
- No retirement data is included yet.
- Many Listed projects have blank methodology values in the export.
- Rules/forms and project evidence documents are not parsed.
- Credit unit is not available from the current project catalogue import.

### Extraction type

Export import.

## Puro Earth

### How data was obtained

Puro Earth data is extracted from the public registry. The repo includes static inspection scripts and Playwright-based extraction scripts for paginated project and issuance registry views.

### Files and scripts involved

Processed files:

- `data/processed/puro_earth/puro_projects_all.csv`
- `data/processed/puro_earth/puro_issuances_all.csv`
- `data/processed/puro_earth/puro_projects.csv`
- `data/processed/puro_earth/puro_issuances.csv`
- `data/processed/puro_earth/puro_source_recon.csv`
- `data/processed/puro_earth/puro_dynamic_access_notes.csv`

Scripts:

- `etl/sources/puro_earth/inspect_registry.py`
- `etl/sources/puro_earth/inspect_dynamic_access.py`
- `etl/sources/puro_earth/parse_projects.py`
- `etl/sources/puro_earth/parse_projects_playwright.py`
- `etl/sources/puro_earth/parse_issuances.py`
- `etl/sources/puro_earth/parse_issuances_playwright.py`

### Fields available

- Project ID.
- Project name.
- Supplier.
- Country.
- Methodology.
- Project URL.
- Issuance project ID.
- Issuance project name.
- Issued date.
- Issued quantity.
- Credit unit, represented as CORC in the unified issuance output.
- Durability.
- Source URL.

### Known gaps

- Project detail documents are not fully extracted yet.
- Rules/forms are not parsed in the current source-specific output.
- Document availability is partial and should be expanded in a future document extraction pass.

### Extraction type

Full registry project extraction and full issuance extraction via Playwright pagination.
