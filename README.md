# Carbon Registry Intelligence Database

Prototype database and Streamlit explorer for carbon registry methodology, project, issuance, and source-inventory data.

The project currently aggregates JCM Mongolia-Japan, Gold Standard project catalogue data, and Puro Earth registry data into unified project and issuance outputs.

## Current Source Status

The source parsers produce processed CSV outputs for:

- JCM Mongolia-Japan methodologies, projects, issuance allocation records, and rules/forms
- Gold Standard project catalogue export
- Puro Earth projects and issuances

Raw HTML snapshots are stored under `data/raw/jcm_mn/` when fetched locally. Processed outputs are stored under `data/processed/jcm_mn/`.

## Setup

Install the Python dependencies:

```powershell
pip install -r requirements.txt
```

## Run ETL

Fetch the current JCM Mongolia-Japan source pages:

```powershell
python -m etl.sources.jcm_mn.fetch_pages
```

Parse the fetched pages into processed CSVs:

```powershell
python -m etl.sources.jcm_mn.parse_methodologies
python -m etl.sources.jcm_mn.parse_projects
python -m etl.sources.jcm_mn.parse_issuance
python -m etl.sources.jcm_mn.parse_rules
```

Build unified CSVs across available sources:

```powershell
python -m etl.build_unified.build_projects
python -m etl.build_unified.build_issuances
```

Check expected processed outputs:

```powershell
python scripts/check_outputs.py
```

## Run Streamlit

Launch the local explorer:

```powershell
streamlit run app/streamlit_app.py
```

## Current Processed Outputs

Expected processed files:

- `data/processed/jcm_mn/methodologies.csv`
- `data/processed/jcm_mn/projects_mongolia.csv`
- `data/processed/jcm_mn/issuance_records.csv`
- `data/processed/jcm_mn/rules_forms.csv`
- `data/processed/source_inventory.csv`
- `data/processed/unified/projects.csv`
- `data/processed/unified/issuances.csv`

Unified outputs aggregate available project and issuance fields across JCM Mongolia-Japan, Gold Standard, and Puro Earth. Missing source-specific fields are left blank.

## Next-Source Roadmap

Use `data/processed/source_inventory.csv` to prioritize future sources after the current unified project and issuance explorer is reviewed.
