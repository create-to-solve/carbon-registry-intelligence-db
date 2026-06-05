from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed" / "jcm_mn"
GLOBAL_DATA_DIR = PROJECT_ROOT / "data" / "processed"
GOLD_STANDARD_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "gold_standard"
PURO_EARTH_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "puro_earth"
UNIFIED_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "unified"

DATAFRAME_KWARGS = {"width": "stretch", "hide_index": True}


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data
def load_data():
    return {
        "methodologies": load_csv(DATA_DIR / "methodologies.csv"),
        "jcm_projects": load_csv(DATA_DIR / "projects_mongolia.csv"),
        "jcm_issuance": load_csv(DATA_DIR / "issuance_records.csv"),
        "rules": load_csv(DATA_DIR / "rules_forms.csv"),
        "source_inventory": load_csv(GLOBAL_DATA_DIR / "source_inventory.csv"),
        "gs_projects": load_csv(GOLD_STANDARD_DATA_DIR / "gs_projects.csv"),
        "puro_projects": load_csv(PURO_EARTH_DATA_DIR / "puro_projects_all.csv"),
        "puro_issuances": load_csv(PURO_EARTH_DATA_DIR / "puro_issuances_all.csv"),
        "unified_projects": load_csv(UNIFIED_DATA_DIR / "projects.csv"),
        "unified_issuances": load_csv(UNIFIED_DATA_DIR / "issuances.csv"),
        "unified_methodologies": load_csv(UNIFIED_DATA_DIR / "methodologies.csv"),
        "unified_documents": load_csv(UNIFIED_DATA_DIR / "documents.csv"),
        "methodology_project_links": load_csv(
            UNIFIED_DATA_DIR / "methodology_project_links.csv"
        ),
        "methodology_profiles": load_csv(UNIFIED_DATA_DIR / "methodology_profiles.csv"),
        "evidence_requirements_seed": load_csv(
            UNIFIED_DATA_DIR / "evidence_requirements_seed.csv"
        ),
    }


def safe_count_unique(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(df[column].replace("", pd.NA).dropna().nunique())


def numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if df.empty or column not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


def clean_unified_projects(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    cleaned = df.fillna("").copy()
    if "estimated_annual_credits" in cleaned.columns:
        cleaned["estimated_annual_credits"] = numeric_series(
            cleaned,
            "estimated_annual_credits",
        )
    return cleaned


def clean_unified_issuances(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    cleaned = df.fillna("").copy()
    if "issued_quantity" in cleaned.columns:
        cleaned["issued_quantity"] = numeric_series(cleaned, "issued_quantity")
    return cleaned


def clean_unified_methodologies(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    cleaned = df.fillna("").copy()
    for column in ["project_count", "related_projects_count"]:
        if column in cleaned.columns:
            cleaned[column] = numeric_series(cleaned, column)
    return cleaned


def clean_unified_documents(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    return df.fillna("").copy()


def clean_methodology_profiles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    cleaned = df.fillna("").copy()
    for column in [
        "related_projects_count",
        "related_documents_count",
        "countries_count",
    ]:
        if column in cleaned.columns:
            cleaned[column] = numeric_series(cleaned, column)
    return cleaned


def clean_methodology_project_links(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    return df.fillna("").copy()


def clean_evidence_requirements_seed(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    return df.fillna("").copy()


def clean_numeric_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df.copy()

    cleaned = df.fillna("").copy()
    cleaned[column] = numeric_series(cleaned, column)
    return cleaned


def non_empty_options(df: pd.DataFrame, column: str) -> list:
    if df.empty or column not in df.columns:
        return []
    return sorted(df[column].replace("", pd.NA).dropna().unique())


def missing_values(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["column", "missing_values"])

    return (
        df.fillna("")
        .eq("")
        .sum()
        .sort_values(ascending=False)
        .rename("missing_values")
        .reset_index()
        .rename(columns={"index": "column"})
    )


def apply_optional_multiselect_filter(
    df: pd.DataFrame,
    column: str,
    selected_values: list,
) -> pd.DataFrame:
    if df.empty or column not in df.columns or not selected_values:
        return df
    return df[df[column].isin(selected_values)].copy()


def apply_text_search(
    df: pd.DataFrame,
    columns: list[str],
    query: str,
) -> pd.DataFrame:
    if df.empty or not query.strip():
        return df

    searchable_columns = [column for column in columns if column in df.columns]
    if not searchable_columns:
        return df

    search = query.strip().lower()
    mask = pd.Series(False, index=df.index)
    for column in searchable_columns:
        mask = mask | df[column].astype(str).str.lower().str.contains(
            search,
            na=False,
            regex=False,
        )
    return df[mask].copy()


def show_download_button(df: pd.DataFrame, filename: str) -> None:
    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        file_name=filename,
        mime="text/csv",
    )


def show_missing_unified_warning(entity_name: str) -> None:
    builder_commands = {
        "projects": "`python -m etl.build_unified.build_projects`",
        "issuances": "`python -m etl.build_unified.build_issuances`",
        "methodologies": "`python -m etl.build_unified.build_methodologies`",
        "documents": "`python -m etl.build_unified.build_documents`",
        "methodology profiles": "`python -m etl.build_unified.build_methodology_profiles`",
        "evidence requirements": "`python -m etl.build_unified.build_evidence_requirements_seed`",
        "methodology project links": "`python -m etl.build_unified.build_methodology_project_links`",
    }
    command = builder_commands.get(entity_name, "`python -m etl.build_unified.<builder>`")
    st.warning(
        f"No unified {entity_name} CSV found. Run: {command}"
    )


def render_bar_chart(
    df: pd.DataFrame,
    index_column: str,
    value_column: str,
) -> None:
    if df.empty or index_column not in df.columns or value_column not in df.columns:
        st.info("No chart data available for the current selection.")
        return
    st.bar_chart(df[[index_column, value_column]].set_index(index_column), width="stretch")


def render_line_chart(
    df: pd.DataFrame,
    index_column: str,
    value_column: str,
) -> None:
    if df.empty or index_column not in df.columns or value_column not in df.columns:
        st.info("No chart data available for the current selection.")
        return
    st.line_chart(df[[index_column, value_column]].set_index(index_column), width="stretch")


def render_summary_card(title: str, value: str, note: str = "") -> None:
    st.markdown(f"#### {title}")
    st.metric(title, value, label_visibility="collapsed")
    if note:
        st.caption(note)


def projects_by_source(projects: pd.DataFrame) -> pd.DataFrame:
    if projects.empty:
        return pd.DataFrame(columns=["source_name", "projects"])
    return (
        projects.groupby("source_name", as_index=False)
        .size()
        .rename(columns={"size": "projects"})
        .sort_values("projects", ascending=False)
    )


def issuances_by_source(issuances: pd.DataFrame) -> pd.DataFrame:
    if issuances.empty:
        return pd.DataFrame(columns=["source_name", "issuance_rows"])
    return (
        issuances.groupby("source_name", as_index=False)
        .size()
        .rename(columns={"size": "issuance_rows"})
        .sort_values("issuance_rows", ascending=False)
    )


def rows_by_source(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty or "source_name" not in df.columns:
        return pd.DataFrame(columns=["source_name", label])
    return (
        df.groupby("source_name", as_index=False)
        .size()
        .rename(columns={"size": label})
        .sort_values(label, ascending=False)
    )


def issued_quantity_summary(
    issuances: pd.DataFrame,
    column: str,
    label: str = "issued_quantity",
) -> pd.DataFrame:
    if issuances.empty or column not in issuances.columns:
        return pd.DataFrame(columns=[column, label])
    return (
        issuances[issuances[column] != ""]
        .groupby(column, as_index=False)["issued_quantity"]
        .sum()
        .rename(columns={"issued_quantity": label})
        .sort_values(label, ascending=False)
    )


def source_names(projects: pd.DataFrame, issuances: pd.DataFrame) -> set:
    project_sources = set(projects.get("source_name", pd.Series(dtype=str)).replace("", pd.NA).dropna())
    issuance_sources = set(issuances.get("source_name", pd.Series(dtype=str)).replace("", pd.NA).dropna())
    return project_sources | issuance_sources


def duplicate_project_ids(projects: pd.DataFrame) -> pd.DataFrame:
    if projects.empty:
        return pd.DataFrame()
    with_ids = projects[projects["source_project_id"] != ""].copy()
    duplicate_mask = with_ids.duplicated(
        subset=["source_id", "source_project_id"],
        keep=False,
    )
    return with_ids[duplicate_mask].sort_values(["source_id", "source_project_id"])


def unmatched_issuances(projects: pd.DataFrame, issuances: pd.DataFrame) -> pd.DataFrame:
    if projects.empty or issuances.empty:
        return pd.DataFrame()

    project_keys = set(
        zip(
            projects["source_id"].astype(str),
            projects["source_project_id"].astype(str),
        )
    )
    unmatched_mask = [
        (source_id, project_id) not in project_keys
        for source_id, project_id in zip(
            issuances["source_id"].astype(str),
            issuances["source_project_id"].astype(str),
        )
    ]
    return issuances[unmatched_mask].copy()


def render_overview(data: dict) -> None:
    st.header("Overview")
    st.write(
        "This dashboard aggregates public carbon registry data into unified project "
        "and issuance tables."
    )
    st.info(
        "Use this page to understand database scope at a glance. The detailed pages "
        "separate unified exploration, source traceability, and known data gaps."
    )

    projects = clean_unified_projects(data["unified_projects"])
    issuances = clean_unified_issuances(data["unified_issuances"])
    methodologies = clean_unified_methodologies(data["unified_methodologies"])
    documents = clean_unified_documents(data["unified_documents"])
    methodology_profiles = clean_methodology_profiles(data["methodology_profiles"])
    evidence_seed = clean_evidence_requirements_seed(data["evidence_requirements_seed"])
    if projects.empty:
        show_missing_unified_warning("projects")
        return
    if issuances.empty:
        show_missing_unified_warning("issuances")
        return

    st.subheader("Current Coverage")
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Total projects", f"{len(projects):,}")
    metric2.metric("Total issuance rows", f"{len(issuances):,}")
    metric3.metric("Total sources", f"{len(source_names(projects, issuances)):,}")
    metric4.metric("Total documents", f"{len(documents):,}")

    metric5, metric6, metric7, metric8 = st.columns(4)
    metric5.metric("Total countries", f"{safe_count_unique(projects, 'country'):,}")
    metric6.metric("Total methodologies", f"{len(methodologies):,}")
    metric7.metric("Methodology profiles", f"{len(methodology_profiles):,}")
    metric8.metric("Evidence seed rows", f"{len(evidence_seed):,}")

    metric9, _metric10 = st.columns(2)
    metric9.metric("Total issued quantity", f"{issuances['issued_quantity'].sum():,.0f}")

    st.subheader("Source Contribution")
    source1, source2, source3 = st.columns(3)
    with source1:
        render_summary_card(
            "JCM Mongolia-Japan",
            f"{len(data['jcm_projects']):,} projects",
            (
                f"{len(data['methodologies']):,} methodologies, "
                f"{len(data['jcm_issuance']):,} issuance rows, "
                f"{len(data['rules']):,} rules/forms, "
                f"{len(documents[documents['source_name'] == 'JCM Mongolia-Japan']) if not documents.empty else 0:,} unified documents."
            ),
        )
    with source2:
        render_summary_card(
            "Gold Standard",
            f"{len(data['gs_projects']):,} projects",
            (
                f"{len(methodologies[methodologies['source_name'] == 'Gold Standard']) if not methodologies.empty else 0:,} "
                "unified methodology labels; no issuance or document layer yet."
            ),
        )
    with source3:
        render_summary_card(
            "Puro Earth",
            f"{len(data['puro_projects']):,} projects",
            (
                f"{len(data['puro_issuances']):,} issuance rows, "
                f"{len(methodologies[methodologies['source_name'] == 'Puro Earth']) if not methodologies.empty else 0:,} methodologies, "
                f"{len(documents[documents['source_name'] == 'Puro Earth']) if not documents.empty else 0:,} document/access-note rows."
            ),
        )

    st.subheader("What This Does / Does Not Yet Do")
    does, does_not = st.columns(2)
    with does:
        st.markdown("#### Does")
        st.write("- Combines source data into unified project and issuance tables.")
        st.write("- Adds a methodology intelligence layer with profiles and evidence seeds.")
        st.write("- Keeps source-specific views for traceability.")
        st.write("- Exposes data quality gaps.")
    with does_not:
        st.markdown("#### Does not yet")
        st.write("- Include Gold Standard issuance or retirement data.")
        st.write("- Include ACR, Verra, or CAR.")
        st.write("- Fully parse methodology PDFs or project evidence documents.")

    st.subheader("Quick Charts")
    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("#### Projects by source")
        render_bar_chart(projects_by_source(projects), "source_name", "projects")
    with chart2:
        st.markdown("#### Issued quantity by source")
        render_bar_chart(
            issued_quantity_summary(issuances, "source_name"),
            "source_name",
            "issued_quantity",
        )

    with st.expander("How to read this overview", expanded=False):
        st.write(
            "Projects and issuances are counted as rows in the unified outputs. "
            "Gold Standard currently contributes project catalogue records only, "
            "so source comparisons involving issuance volume are based on JCM and "
            "Puro Earth. The methodology intelligence layer links methodology labels "
            "to projects and seeds evidence requirements from existing document titles."
        )


def render_source_coverage(data: dict) -> None:
    st.header("Source Coverage")
    st.info(
        "This page explains which sources contribute project, issuance, methodology, "
        "rules, and document coverage. It is meant to make the current database scope "
        "easy to audit."
    )

    projects = clean_unified_projects(data["unified_projects"])
    issuances = clean_unified_issuances(data["unified_issuances"])
    methodologies = clean_unified_methodologies(data["unified_methodologies"])
    documents = clean_unified_documents(data["unified_documents"])
    methodology_profiles = clean_methodology_profiles(data["methodology_profiles"])
    evidence_seed = clean_evidence_requirements_seed(data["evidence_requirements_seed"])
    if projects.empty:
        show_missing_unified_warning("projects")
        return
    if issuances.empty:
        show_missing_unified_warning("issuances")
        return

    methodology_counts = rows_by_source(methodologies, "methodology_rows")
    document_counts = rows_by_source(documents, "document_rows")
    methodology_count_by_source = dict(
        zip(methodology_counts["source_name"], methodology_counts["methodology_rows"])
    )
    document_count_by_source = dict(
        zip(document_counts["source_name"], document_counts["document_rows"])
    )
    profile_counts = rows_by_source(methodology_profiles, "methodology_profile_rows")
    evidence_counts = rows_by_source(evidence_seed, "evidence_seed_rows")
    profile_count_by_source = dict(
        zip(profile_counts["source_name"], profile_counts["methodology_profile_rows"])
    )
    evidence_count_by_source = dict(
        zip(evidence_counts["source_name"], evidence_counts["evidence_seed_rows"])
    )

    coverage_matrix = pd.DataFrame(
        [
            {
                "source_name": "JCM Mongolia-Japan",
                "projects_available": "yes",
                "issuance_rows_available": "yes",
                "methodologies_available": "yes",
                "methodology_rows": int(methodology_count_by_source.get("JCM Mongolia-Japan", 0)),
                "methodology_profile_rows": int(profile_count_by_source.get("JCM Mongolia-Japan", 0)),
                "rules_or_forms_available": "yes",
                "documents_available": "yes, forms",
                "document_rows": int(document_count_by_source.get("JCM Mongolia-Japan", 0)),
                "evidence_seed_rows": int(evidence_count_by_source.get("JCM Mongolia-Japan", 0)),
                "credit_unit": "JCM credit",
                "current_gap": "country-specific small sample",
            },
            {
                "source_name": "Gold Standard",
                "projects_available": "yes",
                "issuance_rows_available": "no",
                "methodologies_available": "partial",
                "methodology_rows": int(methodology_count_by_source.get("Gold Standard", 0)),
                "methodology_profile_rows": int(profile_count_by_source.get("Gold Standard", 0)),
                "rules_or_forms_available": "no",
                "documents_available": "no",
                "document_rows": int(document_count_by_source.get("Gold Standard", 0)),
                "evidence_seed_rows": int(evidence_count_by_source.get("Gold Standard", 0)),
                "credit_unit": "not available",
                "current_gap": "project export lacks issuance and many methodology values",
            },
            {
                "source_name": "Puro Earth",
                "projects_available": "yes",
                "issuance_rows_available": "yes",
                "methodologies_available": "yes, from registry field",
                "methodology_rows": int(methodology_count_by_source.get("Puro Earth", 0)),
                "methodology_profile_rows": int(profile_count_by_source.get("Puro Earth", 0)),
                "rules_or_forms_available": "no",
                "documents_available": "partial, not yet extracted",
                "document_rows": int(document_count_by_source.get("Puro Earth", 0)),
                "evidence_seed_rows": int(evidence_count_by_source.get("Puro Earth", 0)),
                "credit_unit": "CORC",
                "current_gap": "project detail documents not yet fully extracted",
            },
        ]
    )

    st.subheader("Coverage Matrix")
    st.dataframe(coverage_matrix, **DATAFRAME_KWARGS)
    st.caption(
        "The matrix describes what is available today, not what each registry may "
        "publish in full. It is a quick trust layer for stakeholder conversations."
    )

    project_counts = projects_by_source(projects)
    issuance_counts = issuances_by_source(issuances)
    issued_totals = issued_quantity_summary(issuances, "source_name")

    card1, card2, card3, card4 = st.columns(4)
    with card1:
        render_summary_card("Sources with Projects", f"{len(project_counts):,}")
    with card2:
        render_summary_card("Sources with Issuances", f"{len(issuance_counts):,}")
    with card3:
        render_summary_card("Methodology Profiles", f"{len(methodology_profiles):,}")
    with card4:
        render_summary_card("Evidence Seed Rows", f"{len(evidence_seed):,}")

    table1, table2, table3, table4 = st.columns(4)
    with table1:
        st.subheader("Projects by Source")
        st.dataframe(project_counts, **DATAFRAME_KWARGS)
    with table2:
        st.subheader("Issuance Rows by Source")
        st.dataframe(issuance_counts, **DATAFRAME_KWARGS)
    with table3:
        st.subheader("Methodologies by Source")
        st.dataframe(methodology_counts, **DATAFRAME_KWARGS)
    with table4:
        st.subheader("Documents by Source")
        st.dataframe(document_counts, **DATAFRAME_KWARGS)

    table5, table6 = st.columns(2)
    with table5:
        st.subheader("Methodology Profiles by Source")
        st.dataframe(profile_counts, **DATAFRAME_KWARGS)
    with table6:
        st.subheader("Evidence Seed Rows by Source")
        st.dataframe(evidence_counts, **DATAFRAME_KWARGS)

    st.subheader("Issued Quantity by Source")
    st.dataframe(issued_totals, **DATAFRAME_KWARGS)

    chart1, chart2, chart3 = st.columns(3)
    with chart1:
        st.subheader("Projects by Source")
        render_bar_chart(project_counts, "source_name", "projects")
    with chart2:
        st.subheader("Methodologies by Source")
        render_bar_chart(methodology_counts, "source_name", "methodology_rows")
    with chart3:
        st.subheader("Issued Quantity by Source")
        render_bar_chart(issued_totals, "source_name", "issued_quantity")

    st.subheader("Source Completeness Notes")
    completeness = pd.DataFrame(
        [
            {
                "source_name": "JCM Mongolia-Japan",
                "strength": "Methodologies, projects, issuances, and rules/forms are linked.",
                "watch_item": "Small country-specific source, not a broad registry universe.",
            },
            {
                "source_name": "Gold Standard",
                "strength": "Large project catalogue export provides broad project coverage.",
                "watch_item": "No issuance/retirement data and many blank methodology fields.",
            },
            {
                "source_name": "Puro Earth",
                "strength": "Project and issuance records are available from registry extraction.",
                "watch_item": "Project detail documents are not fully extracted yet.",
            },
        ]
    )
    st.dataframe(completeness, **DATAFRAME_KWARGS)


def project_filters(projects: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.subheader("Project Filters")
    search = st.sidebar.text_input(
        "Text search",
        key="project_text_search",
        placeholder="Project, developer, country, methodology...",
    )
    source_filter = st.sidebar.multiselect(
        "source_name",
        non_empty_options(projects, "source_name"),
        default=non_empty_options(projects, "source_name"),
        key="project_source_filter",
    )
    country_filter = st.sidebar.multiselect(
        "country",
        non_empty_options(projects, "country"),
        default=[],
        key="project_country_filter",
    )
    project_type_filter = st.sidebar.multiselect(
        "project_type",
        non_empty_options(projects, "project_type"),
        default=[],
        key="project_type_filter",
    )
    methodology_filter = st.sidebar.multiselect(
        "methodology_name",
        non_empty_options(projects, "methodology_name"),
        default=[],
        key="project_methodology_filter",
    )
    status_filter = st.sidebar.multiselect(
        "status",
        non_empty_options(projects, "status"),
        default=[],
        key="project_status_filter",
    )

    filtered = apply_text_search(
        projects.copy(),
        [
            "project_name",
            "developer_or_supplier",
            "country",
            "methodology_name",
            "source_project_id",
        ],
        search,
    )
    filtered = apply_optional_multiselect_filter(filtered, "source_name", source_filter)
    filtered = apply_optional_multiselect_filter(filtered, "country", country_filter)
    filtered = apply_optional_multiselect_filter(filtered, "project_type", project_type_filter)
    filtered = apply_optional_multiselect_filter(filtered, "methodology_name", methodology_filter)
    filtered = apply_optional_multiselect_filter(filtered, "status", status_filter)
    return filtered


def render_explore_projects(data: dict) -> None:
    st.header("Explore Projects")
    st.caption(
        "Filter and search the unified project table, then switch analysis mode to "
        "summarize the current result set."
    )
    projects = clean_unified_projects(data["unified_projects"])
    if projects.empty:
        show_missing_unified_warning("projects")
        return

    filtered = project_filters(projects)
    analysis_mode = st.selectbox(
        "Analysis mode",
        [
            "Browse records",
            "Country comparison",
            "Methodology comparison",
            "Source comparison",
            "Missing methodology review",
        ],
    )

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Projects", f"{len(filtered):,}")
    metric2.metric("Sources", f"{safe_count_unique(filtered, 'source_name'):,}")
    metric3.metric("Countries", f"{safe_count_unique(filtered, 'country'):,}")
    metric4.metric("Methodologies", f"{safe_count_unique(filtered, 'methodology_name'):,}")
    st.caption(
        "Empty filters mean all values for that field. Text search scans project name, "
        "developer/supplier, country, methodology, and source project ID."
    )

    if analysis_mode == "Browse records":
        st.subheader("Filtered Project Records")
        if "project_url" in filtered.columns:
            st.dataframe(
                filtered,
                **DATAFRAME_KWARGS,
                column_config={"project_url": st.column_config.LinkColumn("project_url")},
            )
        else:
            st.dataframe(filtered, **DATAFRAME_KWARGS)
        show_download_button(filtered, "unified_projects_filtered.csv")
    elif analysis_mode == "Country comparison":
        st.subheader("Country Comparison")
        st.info("Shows where the currently filtered project set is concentrated.")
        summary = (
            filtered[filtered["country"] != ""]
            .groupby("country", as_index=False)
            .size()
            .rename(columns={"size": "projects"})
            .sort_values("projects", ascending=False)
            .head(25)
        )
        render_bar_chart(summary.head(15), "country", "projects")
        st.dataframe(summary, **DATAFRAME_KWARGS)
    elif analysis_mode == "Methodology comparison":
        st.subheader("Methodology Comparison")
        st.info("Ranks nonblank methodology names in the filtered project set.")
        summary = (
            filtered[filtered["methodology_name"] != ""]
            .groupby("methodology_name", as_index=False)
            .size()
            .rename(columns={"size": "projects"})
            .sort_values("projects", ascending=False)
            .head(25)
        )
        render_bar_chart(summary.head(15), "methodology_name", "projects")
        st.dataframe(summary, **DATAFRAME_KWARGS)
    elif analysis_mode == "Source comparison":
        st.subheader("Source Comparison")
        st.info("Shows each source's project contribution and share of the filtered result.")
        summary = projects_by_source(filtered)
        if not summary.empty:
            summary["share_pct"] = (summary["projects"] / summary["projects"].sum() * 100).round(1)
        render_bar_chart(summary, "source_name", "projects")
        st.dataframe(summary, **DATAFRAME_KWARGS)
    else:
        st.subheader("Missing Methodology Review")
        missing = filtered[filtered["methodology_name"] == ""].copy()
        st.caption(
            "This view isolates project rows where the unified methodology field is "
            "blank after source parsing."
        )
        st.metric("Projects missing methodology", f"{len(missing):,}")
        st.dataframe(missing, **DATAFRAME_KWARGS)
        show_download_button(missing, "projects_missing_methodology.csv")


def issuance_filters(issuances: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.subheader("Issuance Filters")
    search = st.sidebar.text_input(
        "Text search",
        key="issuance_text_search",
        placeholder="Project, methodology, country, ID...",
    )
    source_filter = st.sidebar.multiselect(
        "source_name",
        non_empty_options(issuances, "source_name"),
        default=non_empty_options(issuances, "source_name"),
        key="issuance_source_filter",
    )
    methodology_filter = st.sidebar.multiselect(
        "methodology_name",
        non_empty_options(issuances, "methodology_name"),
        default=[],
        key="issuance_methodology_filter",
    )
    durability_filter = st.sidebar.multiselect(
        "durability",
        non_empty_options(issuances, "durability"),
        default=[],
        key="issuance_durability_filter",
    )
    credit_unit_filter = st.sidebar.multiselect(
        "credit_unit",
        non_empty_options(issuances, "credit_unit"),
        default=[],
        key="issuance_credit_unit_filter",
    )

    filtered = apply_text_search(
        issuances.copy(),
        ["project_name", "methodology_name", "country", "source_project_id"],
        search,
    )
    filtered = apply_optional_multiselect_filter(filtered, "source_name", source_filter)
    filtered = apply_optional_multiselect_filter(filtered, "methodology_name", methodology_filter)
    filtered = apply_optional_multiselect_filter(filtered, "durability", durability_filter)
    filtered = apply_optional_multiselect_filter(filtered, "credit_unit", credit_unit_filter)
    return filtered


def render_explore_issuances(data: dict) -> None:
    st.header("Explore Issuances")
    st.info(
        "Issued quantities are not directly comparable across all systems unless "
        "credit_unit is considered."
    )
    st.caption(
        "Use filters and text search to define a subset, then choose an analysis mode "
        "to summarize issuance quantity, timing, or missing core fields."
    )

    issuances = clean_unified_issuances(data["unified_issuances"])
    if issuances.empty:
        show_missing_unified_warning("issuances")
        return

    filtered = issuance_filters(issuances)
    analysis_mode = st.selectbox(
        "Analysis mode",
        [
            "Browse records",
            "Issued quantity by source",
            "Issued quantity by methodology",
            "Issued quantity by country",
            "Issuance over time",
            "Missing issuance data review",
        ],
    )

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Issuance rows", f"{len(filtered):,}")
    metric2.metric("Issued quantity", f"{filtered['issued_quantity'].sum():,.0f}")
    metric3.metric("Sources", f"{safe_count_unique(filtered, 'source_name'):,}")
    metric4.metric("Credit units", f"{safe_count_unique(filtered, 'credit_unit'):,}")
    st.caption(
        "Empty filters mean all values for that field. Text search scans project name, "
        "methodology, country, and source project ID."
    )

    if analysis_mode == "Browse records":
        st.subheader("Filtered Issuance Records")
        st.dataframe(filtered, **DATAFRAME_KWARGS)
        show_download_button(filtered, "unified_issuances_filtered.csv")
    elif analysis_mode == "Issued quantity by source":
        st.subheader("Issued Quantity by Source")
        summary = issued_quantity_summary(filtered, "source_name")
        render_bar_chart(summary, "source_name", "issued_quantity")
        st.dataframe(summary, **DATAFRAME_KWARGS)
    elif analysis_mode == "Issued quantity by methodology":
        st.subheader("Issued Quantity by Methodology")
        summary = issued_quantity_summary(filtered, "methodology_name")
        render_bar_chart(summary.head(20), "methodology_name", "issued_quantity")
        st.dataframe(summary, **DATAFRAME_KWARGS)
    elif analysis_mode == "Issued quantity by country":
        st.subheader("Issued Quantity by Country")
        summary = issued_quantity_summary(filtered, "country")
        render_bar_chart(summary.head(20), "country", "issued_quantity")
        st.dataframe(summary, **DATAFRAME_KWARGS)
    elif analysis_mode == "Issuance over time":
        st.subheader("Issuance Over Time")
        dated = filtered.copy()
        dated["issuance_date_parsed"] = pd.to_datetime(
            dated["issuance_date"],
            errors="coerce",
        )
        missing_dates = int(dated["issuance_date_parsed"].isna().sum())
        dated = dated[dated["issuance_date_parsed"].notna()].copy()
        if dated.empty:
            st.warning("No parseable issuance dates are available for the current selection.")
            return
        dated["year"] = dated["issuance_date_parsed"].dt.year
        summary = (
            dated.groupby("year", as_index=False)["issued_quantity"]
            .sum()
            .sort_values("year")
        )
        st.caption(f"Rows with missing or unparseable dates excluded from this chart: {missing_dates:,}.")
        render_line_chart(summary, "year", "issued_quantity")
        st.dataframe(summary, **DATAFRAME_KWARGS)
    else:
        st.subheader("Missing Issuance Data Review")
        missing = filtered[
            (filtered["issuance_date"] == "") | (filtered["issued_quantity"].isna())
        ].copy()
        st.caption(
            "This view isolates issuance rows that cannot support date-based or "
            "quantity-based analysis without review."
        )
        st.metric("Rows missing date or quantity", f"{len(missing):,}")
        st.dataframe(missing, **DATAFRAME_KWARGS)
        show_download_button(missing, "issuances_missing_core_fields.csv")


def render_explore_methodologies(data: dict) -> None:
    st.header("Explore Methodologies")
    st.caption(
        "Browse the unified methodology index built from JCM methodology records and "
        "distinct methodology labels found in project registries."
    )

    methodologies = clean_unified_methodologies(data["unified_methodologies"])
    if methodologies.empty:
        show_missing_unified_warning("methodologies")
        return

    st.sidebar.subheader("Methodology Filters")
    source_filter = st.sidebar.multiselect(
        "source_name",
        non_empty_options(methodologies, "source_name"),
        default=non_empty_options(methodologies, "source_name"),
        key="methodology_source_filter",
    )
    search = st.sidebar.text_input(
        "Search methodology name",
        key="methodology_text_search",
        placeholder="Methodology name, code, scope...",
    )

    filtered = methodologies.copy()
    filtered = apply_optional_multiselect_filter(filtered, "source_name", source_filter)
    filtered = apply_text_search(
        filtered,
        ["methodology_name", "methodology_code", "methodology_id", "sectoral_scope"],
        search,
    )

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Total methodologies", f"{len(filtered):,}")
    metric2.metric("Sources", f"{safe_count_unique(filtered, 'source_name'):,}")
    metric3.metric(
        "Methodologies by source",
        f"{len(rows_by_source(filtered, 'methodologies')):,}",
    )

    source_summary = rows_by_source(filtered, "methodologies")
    st.subheader("Methodology Count by Source")
    render_bar_chart(source_summary, "source_name", "methodologies")
    st.dataframe(source_summary, **DATAFRAME_KWARGS)

    if "related_projects_count" in filtered.columns:
        st.subheader("Top Methodologies by Related Projects")
        top_related = (
            filtered[filtered["related_projects_count"].notna()]
            .sort_values("related_projects_count", ascending=False)
            .head(20)
        )
        render_bar_chart(
            top_related,
            "methodology_name",
            "related_projects_count",
        )
        st.dataframe(top_related, **DATAFRAME_KWARGS)
    elif "project_count" in filtered.columns:
        st.subheader("Top Methodologies by Project Count")
        top_related = (
            filtered[filtered["project_count"].notna()]
            .sort_values("project_count", ascending=False)
            .head(20)
        )
        render_bar_chart(top_related, "methodology_name", "project_count")
        st.dataframe(top_related, **DATAFRAME_KWARGS)

    st.subheader("Unified Methodology Records")
    st.dataframe(filtered, **DATAFRAME_KWARGS)
    show_download_button(filtered, "unified_methodologies_filtered.csv")


def render_explore_documents(data: dict) -> None:
    st.header("Explore Documents")
    st.caption(
        "Browse the unified document index built from JCM rules/forms and existing "
        "Puro Earth reconnaissance/access-note outputs."
    )

    documents = clean_unified_documents(data["unified_documents"])
    if documents.empty:
        show_missing_unified_warning("documents")
        return

    st.sidebar.subheader("Document Filters")
    source_filter = st.sidebar.multiselect(
        "source_name",
        non_empty_options(documents, "source_name"),
        default=non_empty_options(documents, "source_name"),
        key="document_source_filter",
    )
    if "document_type" in documents.columns:
        document_type_filter = st.sidebar.multiselect(
            "document_type",
            non_empty_options(documents, "document_type"),
            default=[],
            key="document_type_filter",
        )
    else:
        document_type_filter = []
    search = st.sidebar.text_input(
        "Search documents",
        key="document_text_search",
        placeholder="Title or URL...",
    )

    filtered = documents.copy()
    filtered = apply_optional_multiselect_filter(filtered, "source_name", source_filter)
    filtered = apply_optional_multiselect_filter(
        filtered,
        "document_type",
        document_type_filter,
    )
    filtered = apply_text_search(
        filtered,
        ["document_title", "document_url"],
        search,
    )

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Total documents", f"{len(filtered):,}")
    metric2.metric("Sources", f"{safe_count_unique(filtered, 'source_name'):,}")
    metric3.metric("Document types", f"{safe_count_unique(filtered, 'document_type'):,}")

    summary1, summary2 = st.columns(2)
    with summary1:
        st.subheader("Documents by Source")
        source_summary = rows_by_source(filtered, "documents")
        render_bar_chart(source_summary, "source_name", "documents")
        st.dataframe(source_summary, **DATAFRAME_KWARGS)
    with summary2:
        st.subheader("Documents by Type")
        if "document_type" in filtered.columns:
            type_summary = (
                filtered.groupby("document_type", as_index=False)
                .size()
                .rename(columns={"size": "documents"})
                .sort_values("documents", ascending=False)
            )
            render_bar_chart(type_summary, "document_type", "documents")
            st.dataframe(type_summary, **DATAFRAME_KWARGS)
        else:
            st.info("No document_type column is available.")

    st.subheader("Unified Document Records")
    if "document_url" in filtered.columns:
        st.dataframe(
            filtered,
            **DATAFRAME_KWARGS,
            column_config={"document_url": st.column_config.LinkColumn("document_url")},
        )
    else:
        st.dataframe(filtered, **DATAFRAME_KWARGS)
    show_download_button(filtered, "unified_documents_filtered.csv")


def render_methodology_profiles(data: dict) -> None:
    st.header("Methodology Profiles")
    st.caption(
        "Explore v1.1 methodology profiles: source methodology labels enriched with "
        "linked project counts, country counts, document match counts, and examples."
    )

    profiles = clean_methodology_profiles(data["methodology_profiles"])
    if profiles.empty:
        show_missing_unified_warning("methodology profiles")
        return

    st.sidebar.subheader("Profile Filters")
    source_filter = st.sidebar.multiselect(
        "source_name",
        non_empty_options(profiles, "source_name"),
        default=non_empty_options(profiles, "source_name"),
        key="profile_source_filter",
    )
    search = st.sidebar.text_input(
        "Search methodology name",
        key="profile_text_search",
        placeholder="Methodology name or code...",
    )

    filtered = profiles.copy()
    filtered = apply_optional_multiselect_filter(filtered, "source_name", source_filter)
    filtered = apply_text_search(
        filtered,
        ["methodology_name", "methodology_code", "notes"],
        search,
    )

    total_linked_projects = (
        filtered["related_projects_count"].sum()
        if "related_projects_count" in filtered.columns
        else 0
    )
    profiles_with_projects = (
        int((filtered["related_projects_count"] > 0).sum())
        if "related_projects_count" in filtered.columns
        else 0
    )

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Total methodology profiles", f"{len(filtered):,}")
    metric2.metric("Sources", f"{safe_count_unique(filtered, 'source_name'):,}")
    metric3.metric("Total linked projects", f"{total_linked_projects:,.0f}")
    metric4.metric("Profiles with linked projects", f"{profiles_with_projects:,}")

    st.subheader("Top Methodologies by Linked Projects")
    if "related_projects_count" in filtered.columns:
        top_profiles = (
            filtered.sort_values("related_projects_count", ascending=False)
            .head(25)
            .copy()
        )
        render_bar_chart(
            top_profiles.head(15),
            "methodology_name",
            "related_projects_count",
        )
        st.dataframe(top_profiles, **DATAFRAME_KWARGS)
    else:
        st.info("No related_projects_count column is available.")

    if "countries_count" in filtered.columns:
        st.subheader("Countries Count Summary")
        countries_summary = (
            filtered.groupby("countries_count", as_index=False)
            .size()
            .rename(columns={"size": "methodology_profiles"})
            .sort_values("countries_count", ascending=False)
        )
        render_bar_chart(
            countries_summary,
            "countries_count",
            "methodology_profiles",
        )
        st.dataframe(countries_summary, **DATAFRAME_KWARGS)

    st.subheader("Methodology Profiles Table")
    st.dataframe(filtered, **DATAFRAME_KWARGS)
    show_download_button(filtered, "methodology_profiles_filtered.csv")


def render_evidence_requirements(data: dict) -> None:
    st.header("Evidence Requirements")
    st.caption(
        "Explore v1.1 evidence requirement seed rows classified from existing "
        "document titles only. No PDF contents are parsed."
    )

    evidence = clean_evidence_requirements_seed(data["evidence_requirements_seed"])
    if evidence.empty:
        show_missing_unified_warning("evidence requirements")
        return

    st.sidebar.subheader("Evidence Filters")
    source_filter = st.sidebar.multiselect(
        "source_name",
        non_empty_options(evidence, "source_name"),
        default=non_empty_options(evidence, "source_name"),
        key="evidence_source_filter",
    )
    stage_filter = st.sidebar.multiselect(
        "evidence_stage",
        non_empty_options(evidence, "evidence_stage"),
        default=[],
        key="evidence_stage_filter",
    )
    if "evidence_document_type" in evidence.columns:
        document_type_filter = st.sidebar.multiselect(
            "evidence_document_type",
            non_empty_options(evidence, "evidence_document_type"),
            default=[],
            key="evidence_document_type_filter",
        )
    else:
        document_type_filter = []
    search = st.sidebar.text_input(
        "Search evidence rows",
        key="evidence_text_search",
        placeholder="Document title or relevance note...",
    )

    filtered = evidence.copy()
    filtered = apply_optional_multiselect_filter(filtered, "source_name", source_filter)
    filtered = apply_optional_multiselect_filter(filtered, "evidence_stage", stage_filter)
    filtered = apply_optional_multiselect_filter(
        filtered,
        "evidence_document_type",
        document_type_filter,
    )
    filtered = apply_text_search(
        filtered,
        ["document_title", "relevance_note"],
        search,
    )

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Evidence seed rows", f"{len(filtered):,}")
    metric2.metric("Sources", f"{safe_count_unique(filtered, 'source_name'):,}")
    metric3.metric("Evidence stages", f"{safe_count_unique(filtered, 'evidence_stage'):,}")
    metric4.metric(
        "Document types",
        f"{safe_count_unique(filtered, 'evidence_document_type'):,}",
    )

    summary1, summary2 = st.columns(2)
    with summary1:
        st.subheader("Evidence Stage Distribution")
        stage_summary = (
            filtered.groupby("evidence_stage", as_index=False)
            .size()
            .rename(columns={"size": "evidence_rows"})
            .sort_values("evidence_rows", ascending=False)
        )
        render_bar_chart(stage_summary, "evidence_stage", "evidence_rows")
        st.dataframe(stage_summary, **DATAFRAME_KWARGS)
    with summary2:
        st.subheader("Documents by Source")
        source_summary = rows_by_source(filtered, "evidence_rows")
        render_bar_chart(source_summary, "source_name", "evidence_rows")
        st.dataframe(source_summary, **DATAFRAME_KWARGS)

    st.subheader("Evidence Requirements Seed Table")
    if "document_url" in filtered.columns:
        st.dataframe(
            filtered,
            **DATAFRAME_KWARGS,
            column_config={"document_url": st.column_config.LinkColumn("document_url")},
        )
    else:
        st.dataframe(filtered, **DATAFRAME_KWARGS)
    show_download_button(filtered, "evidence_requirements_seed_filtered.csv")


def render_jcm_source_views(data: dict) -> None:
    methodologies = data["methodologies"]
    projects = data["jcm_projects"]
    issuance = clean_numeric_column(data["jcm_issuance"], "issued_amount")
    rules = data["rules"]

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Methodologies", f"{len(methodologies):,}")
    metric2.metric("Projects", f"{len(projects):,}")
    metric3.metric("Issuance rows", f"{len(issuance):,}")
    metric4.metric("Rules/forms", f"{len(rules):,}")

    with st.expander("Methodologies", expanded=False):
        st.dataframe(methodologies, **DATAFRAME_KWARGS)
    with st.expander("Projects", expanded=False):
        st.dataframe(projects, **DATAFRAME_KWARGS)
    with st.expander("Issuance records", expanded=False):
        st.dataframe(issuance, **DATAFRAME_KWARGS)
    with st.expander("Rules & Forms", expanded=False):
        st.dataframe(rules, **DATAFRAME_KWARGS)


def render_gold_standard_source_view(data: dict) -> None:
    projects = clean_numeric_column(data["gs_projects"], "estimated_annual_credits")
    if projects.empty:
        st.warning("No Gold Standard projects CSV found.")
        return

    missing_methodology = int((projects.get("methodology", pd.Series(dtype=str)).fillna("") == "").sum())
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Projects", f"{len(projects):,}")
    metric2.metric("Countries", f"{safe_count_unique(projects, 'country'):,}")
    metric3.metric("Statuses", f"{safe_count_unique(projects, 'status'):,}")
    metric4.metric("Missing methodology", f"{missing_methodology:,}")

    summary1, summary2 = st.columns(2)
    with summary1:
        st.subheader("Top Countries")
        country_summary = (
            projects[projects["country"] != ""]
            .groupby("country", as_index=False)
            .size()
            .rename(columns={"size": "projects"})
            .sort_values("projects", ascending=False)
            .head(20)
        )
        render_bar_chart(country_summary.head(10), "country", "projects")
        st.dataframe(country_summary, **DATAFRAME_KWARGS)
    with summary2:
        st.subheader("Top Project Types")
        type_summary = (
            projects[projects["project_type"] != ""]
            .groupby("project_type", as_index=False)
            .size()
            .rename(columns={"size": "projects"})
            .sort_values("projects", ascending=False)
            .head(20)
        )
        render_bar_chart(type_summary.head(10), "project_type", "projects")
        st.dataframe(type_summary, **DATAFRAME_KWARGS)

    with st.expander("Gold Standard project catalogue", expanded=True):
        st.dataframe(projects, **DATAFRAME_KWARGS)


def render_puro_source_view(data: dict) -> None:
    projects = data["puro_projects"].fillna("").copy()
    issuances = clean_numeric_column(data["puro_issuances"], "issued_qty")
    if projects.empty or issuances.empty:
        st.warning("No full Puro Earth registry outputs found.")
        return

    metric1, metric2, metric3, metric4, metric5 = st.columns(5)
    metric1.metric("Projects", f"{len(projects):,}")
    metric2.metric("Issuance rows", f"{len(issuances):,}")
    metric3.metric("Issued quantity", f"{issuances['issued_qty'].sum():,.0f}")
    metric4.metric("Methodologies", f"{safe_count_unique(projects, 'methodology'):,}")
    metric5.metric("Countries", f"{safe_count_unique(projects, 'country'):,}")

    summary1, summary2 = st.columns(2)
    with summary1:
        st.subheader("Issued Quantity by Methodology")
        methodology_summary = (
            issuances[issuances["methodology"] != ""]
            .groupby("methodology", as_index=False)["issued_qty"]
            .sum()
            .sort_values("issued_qty", ascending=False)
        )
        render_bar_chart(methodology_summary.head(10), "methodology", "issued_qty")
        st.dataframe(methodology_summary, **DATAFRAME_KWARGS)
    with summary2:
        st.subheader("Issued Quantity by Durability")
        durability_summary = (
            issuances[issuances["durability"] != ""]
            .groupby("durability", as_index=False)["issued_qty"]
            .sum()
            .sort_values("issued_qty", ascending=False)
        )
        render_bar_chart(durability_summary, "durability", "issued_qty")
        st.dataframe(durability_summary, **DATAFRAME_KWARGS)

    with st.expander("Puro Earth projects", expanded=False):
        st.dataframe(projects, **DATAFRAME_KWARGS)
    with st.expander("Puro Earth issuances", expanded=False):
        st.dataframe(issuances, **DATAFRAME_KWARGS)


def render_source_views(data: dict) -> None:
    st.header("Source Views")
    st.caption("Source-specific diagnostics are kept separate from unified explorer views.")

    source = st.selectbox(
        "Source",
        ["JCM Mongolia-Japan", "Gold Standard", "Puro Earth"],
    )
    if source == "JCM Mongolia-Japan":
        render_jcm_source_views(data)
    elif source == "Gold Standard":
        render_gold_standard_source_view(data)
    else:
        render_puro_source_view(data)


def render_data_quality(data: dict) -> None:
    st.header("Data Quality")
    st.write(
        "This page explains known data strengths and gaps in the unified outputs. "
        "Counts here are profiling checks, not transformations."
    )

    projects = clean_unified_projects(data["unified_projects"])
    issuances = clean_unified_issuances(data["unified_issuances"])
    methodologies = clean_unified_methodologies(data["unified_methodologies"])
    documents = clean_unified_documents(data["unified_documents"])
    methodology_project_links = clean_methodology_project_links(
        data["methodology_project_links"]
    )
    methodology_profiles = clean_methodology_profiles(data["methodology_profiles"])
    evidence_seed = clean_evidence_requirements_seed(data["evidence_requirements_seed"])
    if projects.empty:
        show_missing_unified_warning("projects")
        return
    if issuances.empty:
        show_missing_unified_warning("issuances")
        return

    duplicates = duplicate_project_ids(projects)
    unmatched = unmatched_issuances(projects, issuances)
    missing_project_methodology = projects[projects["methodology_name"] == ""].copy()
    missing_issuance_core = issuances[
        (issuances["issuance_date"] == "") | (issuances["issued_quantity"].isna())
    ].copy()

    st.subheader("Quality Summary")
    card1, card2, card3, card4 = st.columns(4)
    with card1:
        render_summary_card("Duplicate Project IDs", f"{len(duplicates):,}")
    with card2:
        render_summary_card("Unmatched Issuances", f"{len(unmatched):,}")
    with card3:
        render_summary_card("Projects Missing Methodology", f"{len(missing_project_methodology):,}")
    with card4:
        render_summary_card("Issuances Missing Core Fields", f"{len(missing_issuance_core):,}")

    st.subheader("A. Healthy Signals")
    if duplicates.empty:
        st.success("No duplicate source_project_id values within each source.")
    else:
        st.warning(f"Duplicate source project IDs found: {len(duplicates):,} rows.")
    if unmatched.empty:
        st.success("No unmatched issuances found.")
    else:
        st.warning(f"Unmatched issuance rows found: {len(unmatched):,}.")
    if "project_url" in projects.columns and int((projects["project_url"] == "").sum()) == 0:
        st.success("Project URLs are populated.")
    else:
        st.warning("Some project URLs are blank.")
    if "credit_unit" in issuances.columns and int((issuances["credit_unit"] == "").sum()) == 0:
        st.success("Credit unit is populated for issuance rows.")
    else:
        st.warning("Some issuance rows have blank credit_unit values.")

    st.subheader("B. Known Expected Gaps")
    st.info("Gold Standard project export has no issuance data loaded yet.")
    st.info("Gold Standard has missing methodology values for many Listed projects.")
    st.info("Puro durability is available, but JCM durability is not applicable.")
    st.info("JCM Mongolia-Japan is a small country-specific sample.")

    st.subheader("C. Profiling Tables")
    summary1, summary2 = st.columns(2)
    with summary1:
        st.markdown("#### Missing Values in Unified Projects")
        st.caption("Blank counts by column in data/processed/unified/projects.csv.")
        project_missing = missing_values(projects)
        render_bar_chart(project_missing.head(10), "column", "missing_values")
        st.dataframe(project_missing, **DATAFRAME_KWARGS)
    with summary2:
        st.markdown("#### Missing Values in Unified Issuances")
        st.caption("Blank counts by column in data/processed/unified/issuances.csv.")
        issuance_missing = missing_values(issuances)
        render_bar_chart(issuance_missing.head(10), "column", "missing_values")
        st.dataframe(issuance_missing, **DATAFRAME_KWARGS)

    if not methodologies.empty or not documents.empty:
        st.subheader("Optional Unified Index Layers")
        optional1, optional2 = st.columns(2)
        with optional1:
            st.markdown("#### Missing Values in Unified Methodologies")
            if methodologies.empty:
                st.info("Unified methodologies output is not present.")
            else:
                methodology_missing = missing_values(methodologies)
                render_bar_chart(
                    methodology_missing.head(10),
                    "column",
                    "missing_values",
                )
                st.dataframe(methodology_missing, **DATAFRAME_KWARGS)
        with optional2:
            st.markdown("#### Missing Values in Unified Documents")
            if documents.empty:
                st.info("Unified documents output is not present.")
            else:
                document_missing = missing_values(documents)
                render_bar_chart(document_missing.head(10), "column", "missing_values")
                st.dataframe(document_missing, **DATAFRAME_KWARGS)

    if (
        not methodology_project_links.empty
        or not methodology_profiles.empty
        or not evidence_seed.empty
    ):
        st.subheader("v1.1 Methodology Intelligence Layer")
        v11_col1, v11_col2, v11_col3 = st.columns(3)
        with v11_col1:
            st.markdown("#### Missing Values in Methodology Project Links")
            if methodology_project_links.empty:
                st.info("Methodology project links output is not present.")
            else:
                link_missing = missing_values(methodology_project_links)
                render_bar_chart(link_missing.head(10), "column", "missing_values")
                st.dataframe(link_missing, **DATAFRAME_KWARGS)
        with v11_col2:
            st.markdown("#### Missing Values in Methodology Profiles")
            if methodology_profiles.empty:
                st.info("Methodology profiles output is not present.")
            else:
                profile_missing = missing_values(methodology_profiles)
                render_bar_chart(profile_missing.head(10), "column", "missing_values")
                st.dataframe(profile_missing, **DATAFRAME_KWARGS)
        with v11_col3:
            st.markdown("#### Missing Values in Evidence Requirements")
            if evidence_seed.empty:
                st.info("Evidence requirements seed output is not present.")
            else:
                evidence_missing = missing_values(evidence_seed)
                render_bar_chart(evidence_missing.head(10), "column", "missing_values")
                st.dataframe(evidence_missing, **DATAFRAME_KWARGS)

    with st.expander("Projects Missing Methodology", expanded=False):
        st.caption(
            "Useful for parser follow-up and for explaining why some methodology "
            "comparisons undercount certain sources."
        )
        st.metric("Count", f"{len(missing_project_methodology):,}")
        st.dataframe(missing_project_methodology, **DATAFRAME_KWARGS)

    with st.expander("Issuances Missing Date or Quantity", expanded=False):
        st.caption(
            "Rows here cannot fully support time series or issued-volume analysis "
            "without additional review."
        )
        st.metric("Count", f"{len(missing_issuance_core):,}")
        st.dataframe(missing_issuance_core, **DATAFRAME_KWARGS)

    with st.expander("Unmatched Issuances", expanded=False):
        st.caption(
            "Compared by source_id and source_project_id between unified issuances "
            "and unified projects."
        )
        if unmatched.empty:
            st.success("No unmatched issuances.")
        else:
            st.metric("Count", f"{len(unmatched):,}")
            st.dataframe(unmatched, **DATAFRAME_KWARGS)


def render_admin(data: dict) -> None:
    st.header("Admin / Source Inventory")
    st.write("This page tracks possible future sources and parser priority.")

    source_inventory = data["source_inventory"].fillna("").copy()
    if source_inventory.empty:
        st.warning("No source_inventory.csv found.")
        return

    summary1, summary2 = st.columns(2)
    with summary1:
        if "priority" in source_inventory.columns:
            st.subheader("Priority Counts")
            priority_counts = (
                source_inventory.groupby("priority", as_index=False)
                .size()
                .rename(columns={"size": "sources"})
                .sort_values("sources", ascending=False)
            )
            render_bar_chart(priority_counts, "priority", "sources")
            st.dataframe(priority_counts, **DATAFRAME_KWARGS)
    with summary2:
        if "recommended_next_action" in source_inventory.columns:
            st.subheader("Recommended Action Counts")
            action_counts = (
                source_inventory.groupby("recommended_next_action", as_index=False)
                .size()
                .rename(columns={"size": "sources"})
                .sort_values("sources", ascending=False)
            )
            render_bar_chart(action_counts, "recommended_next_action", "sources")
            st.dataframe(action_counts, **DATAFRAME_KWARGS)

    st.subheader("Source Inventory")
    st.dataframe(source_inventory, **DATAFRAME_KWARGS)
    show_download_button(source_inventory, "source_inventory.csv")


st.set_page_config(
    page_title="Carbon Registry Intelligence Database",
    layout="wide",
)

st.title("Carbon Registry Intelligence Database")
st.caption("v0.4 prototype: source-specific parsers -> unified tables -> explorer")

DATA = load_data()

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Source Coverage",
        "Explore Projects",
        "Explore Issuances",
        "Explore Methodologies",
        "Explore Documents",
        "Methodology Profiles",
        "Evidence Requirements",
        "Source Views",
        "Data Quality",
        "Admin / Source Inventory",
    ],
)

if page == "Overview":
    render_overview(DATA)
elif page == "Source Coverage":
    render_source_coverage(DATA)
elif page == "Explore Projects":
    render_explore_projects(DATA)
elif page == "Explore Issuances":
    render_explore_issuances(DATA)
elif page == "Explore Methodologies":
    render_explore_methodologies(DATA)
elif page == "Explore Documents":
    render_explore_documents(DATA)
elif page == "Methodology Profiles":
    render_methodology_profiles(DATA)
elif page == "Evidence Requirements":
    render_evidence_requirements(DATA)
elif page == "Source Views":
    render_source_views(DATA)
elif page == "Data Quality":
    render_data_quality(DATA)
else:
    render_admin(DATA)
