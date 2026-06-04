# Unified Schema

This schema documents the cross-source unified outputs built from processed source-specific files.

Unified builders do not scrape or parse raw source pages. They normalize already-processed source CSVs into shared project and issuance tables.

## `data/processed/unified/projects.csv`

- `source_id`: machine-readable source identifier, such as `jcm_mn`, `gold_standard`, or `puro_earth`
- `source_name`: human-readable source name
- `source_project_id`: project identifier from the source system
- `project_name`: project title or name
- `country`: host country when available
- `status`: source project status when available
- `project_type`: source project type or category when available
- `methodology_name`: methodology name, code, or source-provided methodology label when available
- `developer_or_supplier`: project developer, supplier, participant, or analogous entity when available
- `estimated_annual_credits`: estimated annual credits when available
- `project_url`: project detail or source URL when available

## `data/processed/unified/issuances.csv`

- `source_id`: machine-readable source identifier
- `source_name`: human-readable source name
- `source_project_id`: project identifier from the source system
- `project_name`: project title or name
- `issuance_date`: issuance date when available
- `issued_quantity`: issued quantity as a numeric value when available
- `credit_unit`: source credit unit label when known
- `methodology_name`: methodology name or source-provided methodology label when available
- `durability`: durability label when available
- `country`: country associated with the issuance record when available
- `source_url`: source page or registry URL for the record set

## Source-Specific Limitations

- JCM Mongolia-Japan project records do not currently provide a project-specific detail URL in the processed project CSV, so unified `project_url` uses the source projects page.
- JCM Mongolia-Japan issuance rows are country allocation rows. Some allocation rows have blank issuance dates or issued quantities in the source table.
- JCM Mongolia-Japan issuance methodology is joined from processed project records using `reference_no`.
- Gold Standard unified projects are built from the registry project export. The export does not include processed issuance records in this repository, so Gold Standard contributes no unified issuance rows yet.
- Gold Standard project URLs are derived from `source_project_id` as `https://registry.goldstandard.org/projects/details/{source_project_id}`.
- Gold Standard methodology values are only populated when present in the export. Missing methodology values are left blank and are not inferred.
- Puro Earth projects and issuances are built from Playwright registry outputs. Puro Earth issuance country is joined from Puro Earth projects using `project_id`.
- Puro Earth credit unit is set to `CORC`.

## Known Missingness

- Gold Standard has many blank `methodology_name` values because the exported `methodology` field is often empty. These gaps are preserved.
- Gold Standard has no unified issuance data until a Gold Standard issuance/export source is added.
- JCM and Puro Earth do not provide `estimated_annual_credits` in the current processed project files.
- JCM and Puro Earth do not provide unified `project_type` in the current processed project files.
- JCM issuance `durability` is blank because JCM does not provide a durability field analogous to Puro Earth.
