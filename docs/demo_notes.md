# Dashboard Demo Notes

## What the dashboard does

The Carbon Registry Intelligence Database dashboard aggregates public carbon registry data into unified project and issuance tables. It gives users a single place to inspect project coverage, issuance records, source contribution, and known data gaps across the currently loaded sources.

## Who it is for

This dashboard is for analysts, product leads, climate data researchers, and stakeholders evaluating whether public registry data can support a unified carbon project and issuance explorer.

## Included sources

- JCM Mongolia-Japan
- Gold Standard project export
- Puro Earth registry

## Unified data layer

The unified data layer normalizes overlapping fields from source-specific outputs into two cross-source tables:

- `data/processed/unified/projects.csv`
- `data/processed/unified/issuances.csv`

Source-specific files remain available for traceability, while the unified tables support cross-source filtering, comparison, and quality checks.

## Dashboard pages

- **Overview**: executive summary of current coverage, source contributions, and quick charts.
- **Source Coverage**: explains which sources contribute projects, issuances, methodologies, rules/forms, documents, and credit units.
- **Explore Projects**: filters, searches, and analyzes unified project records by country, methodology, source, and missing methodology status.
- **Explore Issuances**: filters, searches, and analyzes unified issuance records by source, methodology, country, credit unit, and time.
- **Source Views**: keeps source-specific diagnostic tables available for inspection and traceability.
- **Data Quality**: summarizes healthy signals, expected gaps, missing values, missing methodologies, missing issuance fields, and unmatched issuance checks.
- **Admin / Source Inventory**: planning view for possible future sources and parser priorities.

## Current scale

- Projects: 4,227
- Issuance rows: 583
- Sources: 3
- Countries: 121
- Methodologies: 93
- Total issued quantity: 1,881,351

## Known limitations

- Gold Standard currently includes project catalogue data only, with no issuance or retirement records.
- Gold Standard has many missing methodology values in the project export.
- JCM Mongolia-Japan is a small country-specific pilot source, not a global registry.
- Puro Earth project and issuance records are extracted, but project detail documents are not fully extracted yet.
- Methodology PDFs, project evidence documents, and registry-specific document libraries are not fully parsed.
- Issued quantities should be interpreted with `credit_unit`; quantities are not always directly comparable across systems.
- The dashboard depends on processed CSV outputs already present in the repository.

## Suggested next steps

- Add Gold Standard issuance and retirement data if a reliable public path is available.
- Expand source coverage to additional registries such as ACR, Verra, or CAR.
- Improve document extraction for methodology PDFs, project design documents, and evidence files.
- Add source refresh metadata so users can see when each dataset was last collected.
- Add deeper validation checks for duplicate projects, methodology normalization, date parsing, and credit unit comparability.
- Package a repeatable demo flow for stakeholders using Overview, Source Coverage, Explore Projects, Explore Issuances, and Data Quality.
