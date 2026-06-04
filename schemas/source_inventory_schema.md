# Source Inventory Schema

This schema describes carbon methodology and registry sources for Module B.

## Fields

- source_id: short machine-readable ID
- source_name: human-readable source name
- standard_or_program: carbon standard or programme
- official_url: official source URL
- source_type: methodology catalogue, registry, rules/forms, mixed
- has_methodology_catalogue: yes/no/unknown
- has_methodology_detail_pages: yes/no/unknown
- has_downloadable_documents: yes/no/unknown
- has_project_registry: yes/no/unknown
- has_issuance_data: yes/no/unknown
- primary_formats: HTML, PDF, CSV, XLSX, API, JavaScript app
- access_status: public, login required, partial, unknown
- parser_difficulty: easy, moderate, hard
- priority: high, medium, low
- recommended_next_action: inspect, parse, defer, needs API
- notes: short explanation
- last_checked: date checked