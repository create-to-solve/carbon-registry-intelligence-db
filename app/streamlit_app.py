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


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data
def load_data():
    methodologies = read_csv_if_exists(DATA_DIR / "methodologies.csv")
    projects = read_csv_if_exists(DATA_DIR / "projects_mongolia.csv")
    issuance = read_csv_if_exists(DATA_DIR / "issuance_records.csv")
    rules = read_csv_if_exists(DATA_DIR / "rules_forms.csv")
    source_inventory = read_csv_if_exists(GLOBAL_DATA_DIR / "source_inventory.csv")
    gs_projects = read_csv_if_exists(GOLD_STANDARD_DATA_DIR / "gs_projects.csv")
    puro_projects = read_csv_if_exists(PURO_EARTH_DATA_DIR / "puro_projects_all.csv")
    puro_issuances = read_csv_if_exists(PURO_EARTH_DATA_DIR / "puro_issuances_all.csv")
    unified_projects = read_csv_if_exists(UNIFIED_DATA_DIR / "projects.csv")
    unified_issuances = read_csv_if_exists(UNIFIED_DATA_DIR / "issuances.csv")

    return (
        methodologies,
        projects,
        issuance,
        rules,
        source_inventory,
        gs_projects,
        puro_projects,
        puro_issuances,
        unified_projects,
        unified_issuances,
    )


def clean_methodology_code(value):
    if pd.isna(value):
        return ""

    text = str(value)
    for part in text.split():
        if part.startswith("MN_AM"):
            return part
    return text


def clean_unified_projects(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    cleaned = df.fillna("").copy()
    if "estimated_annual_credits" in cleaned.columns:
        cleaned["estimated_annual_credits"] = pd.to_numeric(
            cleaned["estimated_annual_credits"],
            errors="coerce",
        )
    return cleaned


def clean_unified_issuances(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    cleaned = df.fillna("").copy()
    if "issued_quantity" in cleaned.columns:
        cleaned["issued_quantity"] = pd.to_numeric(
            cleaned["issued_quantity"],
            errors="coerce",
        )
    return cleaned


def clean_numeric_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df

    cleaned = df.copy()
    cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
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


def apply_text_search(
    df: pd.DataFrame,
    search_text: str,
    columns: list[str],
) -> pd.DataFrame:
    if df.empty or not search_text.strip():
        return df

    searchable_columns = [column for column in columns if column in df.columns]
    if not searchable_columns:
        return df

    search = search_text.strip().lower()
    mask = pd.Series(False, index=df.index)
    for column in searchable_columns:
        mask = mask | df[column].astype(str).str.lower().str.contains(
            search,
            na=False,
            regex=False,
        )
    return df[mask].copy()


def apply_multiselect_filter(
    df: pd.DataFrame,
    column: str,
    selected_values: list,
) -> pd.DataFrame:
    if df.empty or column not in df.columns or not selected_values:
        return df
    return df[df[column].isin(selected_values)].copy()


def show_missing_unified_warning(entity_name: str) -> None:
    st.warning(
        f"No unified {entity_name} CSV found. Run: "
        "`python -m etl.build_unified.build_projects` and "
        "`python -m etl.build_unified.build_issuances`"
    )


def render_bar_chart(
    df: pd.DataFrame,
    index_column: str,
    value_column: str,
) -> None:
    if df.empty or index_column not in df.columns or value_column not in df.columns:
        st.info("No chart data available for the current selection.")
        return

    chart_data = df[[index_column, value_column]].set_index(index_column)
    st.bar_chart(chart_data, width="stretch")


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


def issued_quantity_summary(
    issuances: pd.DataFrame,
    column: str,
    label: str,
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


def render_overview(unified_projects: pd.DataFrame, unified_issuances: pd.DataFrame) -> None:
    st.header("Overview")

    if unified_projects.empty:
        show_missing_unified_warning("projects")
        return
    if unified_issuances.empty:
        show_missing_unified_warning("issuances")
        return

    projects = clean_unified_projects(unified_projects)
    issuances = clean_unified_issuances(unified_issuances)

    project_methods = set(projects["methodology_name"].replace("", pd.NA).dropna())
    issuance_methods = set(issuances["methodology_name"].replace("", pd.NA).dropna())
    source_names = set(projects["source_name"].replace("", pd.NA).dropna()) | set(
        issuances["source_name"].replace("", pd.NA).dropna()
    )

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Total projects", f"{len(projects):,}")
    metric2.metric("Total issuance rows", f"{len(issuances):,}")
    metric3.metric("Sources", f"{len(source_names):,}")

    metric4, metric5, metric6 = st.columns(3)
    metric4.metric("Countries", f"{projects['country'].replace('', pd.NA).nunique():,}")
    metric5.metric("Methodologies", f"{len(project_methods | issuance_methods):,}")
    metric6.metric("Total issued quantity", f"{issuances['issued_quantity'].sum():,.0f}")

    st.subheader("Source Coverage")
    summary1, summary2, summary3 = st.columns(3)
    with summary1:
        st.markdown("#### Projects by source")
        st.dataframe(projects_by_source(projects), **DATAFRAME_KWARGS)
    with summary2:
        st.markdown("#### Issuances by source")
        st.dataframe(issuances_by_source(issuances), **DATAFRAME_KWARGS)
    with summary3:
        st.markdown("#### Issued quantity by source")
        st.dataframe(
            issued_quantity_summary(issuances, "source_name", "issued_quantity"),
            **DATAFRAME_KWARGS,
        )

    st.subheader("Data Model")
    st.write(
        "Source-specific extraction -> unified tables -> explorer. "
        "Source parsers preserve registry-specific fields while the unified project "
        "and issuance tables normalize overlapping fields for cross-source analysis."
        )


def render_source_coverage(
    unified_projects: pd.DataFrame,
    unified_issuances: pd.DataFrame,
) -> None:
    st.header("Source Coverage")

    if unified_projects.empty:
        show_missing_unified_warning("projects")
        return
    if unified_issuances.empty:
        show_missing_unified_warning("issuances")
        return

    projects = clean_unified_projects(unified_projects)
    issuances = clean_unified_issuances(unified_issuances)

    source_filter = st.multiselect(
        "Filter sources",
        sorted(
            set(projects["source_name"].replace("", pd.NA).dropna())
            | set(issuances["source_name"].replace("", pd.NA).dropna())
        ),
        default=sorted(
            set(projects["source_name"].replace("", pd.NA).dropna())
            | set(issuances["source_name"].replace("", pd.NA).dropna())
        ),
    )
    projects = apply_multiselect_filter(projects, "source_name", source_filter)
    issuances = apply_multiselect_filter(issuances, "source_name", source_filter)

    project_counts = projects_by_source(projects)
    issuance_counts = issuances_by_source(issuances)
    issued_totals = issued_quantity_summary(
        issuances,
        "source_name",
        "issued_quantity",
    )

    coverage = project_counts.merge(issuance_counts, on="source_name", how="outer")
    coverage = coverage.merge(issued_totals, on="source_name", how="outer")
    coverage = coverage.fillna(0).sort_values("projects", ascending=False)
    coverage["has_projects"] = coverage["projects"] > 0
    coverage["has_issuances"] = coverage["issuance_rows"] > 0

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Sources", f"{coverage['source_name'].nunique():,}")
    metric2.metric("Project rows", f"{int(coverage['projects'].sum()):,}")
    metric3.metric("Issuance rows", f"{int(coverage['issuance_rows'].sum()):,}")
    metric4.metric("Issued quantity", f"{coverage['issued_quantity'].sum():,.0f}")

    st.subheader("Coverage Matrix")
    st.dataframe(coverage, **DATAFRAME_KWARGS)

    chart1, chart2, chart3 = st.columns(3)
    with chart1:
        st.subheader("Projects")
        render_bar_chart(project_counts, "source_name", "projects")
    with chart2:
        st.subheader("Issuance Rows")
        render_bar_chart(issuance_counts, "source_name", "issuance_rows")
    with chart3:
        st.subheader("Issued Quantity")
        render_bar_chart(issued_totals, "source_name", "issued_quantity")

    st.subheader("Field Completeness by Source")
    completeness_rows = []
    for source_name, group in projects.groupby("source_name"):
        completeness_rows.append(
            {
                "source_name": source_name,
                "table": "projects",
                "rows": len(group),
                "missing_methodology": int((group["methodology_name"] == "").sum()),
                "missing_country": int((group["country"] == "").sum()),
                "missing_url": int((group["project_url"] == "").sum()),
            }
        )
    for source_name, group in issuances.groupby("source_name"):
        completeness_rows.append(
            {
                "source_name": source_name,
                "table": "issuances",
                "rows": len(group),
                "missing_methodology": int((group["methodology_name"] == "").sum()),
                "missing_country": int((group["country"] == "").sum()),
                "missing_url": int((group["source_url"] == "").sum()),
                "missing_issuance_date": int((group["issuance_date"] == "").sum()),
                "missing_issued_quantity": int(group["issued_quantity"].isna().sum()),
            }
        )
    st.dataframe(pd.DataFrame(completeness_rows).fillna(""), **DATAFRAME_KWARGS)


def render_explore_projects(unified_projects: pd.DataFrame) -> None:
    st.header("Explore Projects")

    if unified_projects.empty:
        show_missing_unified_warning("projects")
        return

    projects = clean_unified_projects(unified_projects)
    search_text = st.sidebar.text_input(
        "Search projects",
        key="project_text_search",
        placeholder="Name, country, methodology, developer...",
    )

    st.sidebar.subheader("Project Filters")
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

    filtered = projects.copy()
    filtered = apply_text_search(
        filtered,
        search_text,
        [
            "project_name",
            "country",
            "project_type",
            "methodology_name",
            "developer_or_supplier",
            "source_project_id",
            "status",
        ],
    )
    filtered = apply_multiselect_filter(filtered, "source_name", source_filter)
    filtered = apply_multiselect_filter(filtered, "country", country_filter)
    filtered = apply_multiselect_filter(filtered, "project_type", project_type_filter)
    filtered = apply_multiselect_filter(filtered, "methodology_name", methodology_filter)
    filtered = apply_multiselect_filter(filtered, "status", status_filter)

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Projects", f"{len(filtered):,}")
    metric2.metric("Sources", f"{filtered['source_name'].replace('', pd.NA).nunique():,}")
    metric3.metric("Countries", f"{filtered['country'].replace('', pd.NA).nunique():,}")
    metric4.metric(
        "Methodologies",
        f"{filtered['methodology_name'].replace('', pd.NA).nunique():,}",
    )

    st.dataframe(
        filtered,
        **DATAFRAME_KWARGS,
        column_config={"project_url": st.column_config.LinkColumn("project_url")},
    )
    st.download_button(
        "Download filtered projects CSV",
        filtered.to_csv(index=False),
        file_name="unified_projects_filtered.csv",
        mime="text/csv",
    )

    summary1, summary2, summary3 = st.columns(3)
    with summary1:
        st.subheader("Top Countries")
        top_countries = (
            filtered[filtered["country"] != ""]
            .groupby("country", as_index=False)
            .size()
            .rename(columns={"size": "projects"})
            .sort_values("projects", ascending=False)
            .head(20)
        )
        render_bar_chart(top_countries.head(10), "country", "projects")
        st.dataframe(top_countries, **DATAFRAME_KWARGS)
    with summary2:
        st.subheader("Top Methodologies")
        top_methodologies = (
            filtered[filtered["methodology_name"] != ""]
            .groupby("methodology_name", as_index=False)
            .size()
            .rename(columns={"size": "projects"})
            .sort_values("projects", ascending=False)
            .head(20)
        )
        render_bar_chart(top_methodologies.head(10), "methodology_name", "projects")
        st.dataframe(top_methodologies, **DATAFRAME_KWARGS)
    with summary3:
        st.subheader("Projects by Source")
        source_counts = projects_by_source(filtered)
        render_bar_chart(source_counts, "source_name", "projects")
        st.dataframe(source_counts, **DATAFRAME_KWARGS)


def render_explore_issuances(unified_issuances: pd.DataFrame) -> None:
    st.header("Explore Issuances")

    if unified_issuances.empty:
        show_missing_unified_warning("issuances")
        return

    issuances = clean_unified_issuances(unified_issuances)
    search_text = st.sidebar.text_input(
        "Search issuances",
        key="issuance_text_search",
        placeholder="Project, methodology, source project ID...",
    )

    st.sidebar.subheader("Issuance Filters")
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

    filtered = issuances.copy()
    filtered = apply_text_search(
        filtered,
        search_text,
        [
            "project_name",
            "methodology_name",
            "source_project_id",
            "country",
            "credit_unit",
            "durability",
        ],
    )
    filtered = apply_multiselect_filter(filtered, "source_name", source_filter)
    filtered = apply_multiselect_filter(filtered, "methodology_name", methodology_filter)
    filtered = apply_multiselect_filter(filtered, "durability", durability_filter)
    filtered = apply_multiselect_filter(filtered, "credit_unit", credit_unit_filter)

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Issuance rows", f"{len(filtered):,}")
    metric2.metric("Issued quantity", f"{filtered['issued_quantity'].sum():,.0f}")
    metric3.metric("Sources", f"{filtered['source_name'].replace('', pd.NA).nunique():,}")
    metric4.metric(
        "Credit units",
        f"{filtered['credit_unit'].replace('', pd.NA).nunique():,}",
    )

    st.dataframe(filtered, **DATAFRAME_KWARGS)
    st.download_button(
        "Download filtered issuances CSV",
        filtered.to_csv(index=False),
        file_name="unified_issuances_filtered.csv",
        mime="text/csv",
    )

    summary1, summary2, summary3 = st.columns(3)
    with summary1:
        st.subheader("Issued Quantity by Source")
        source_totals = issued_quantity_summary(
            filtered,
            "source_name",
            "issued_quantity",
        )
        render_bar_chart(source_totals, "source_name", "issued_quantity")
        st.dataframe(source_totals, **DATAFRAME_KWARGS)
    with summary2:
        st.subheader("Issued Quantity by Methodology")
        methodology_totals = issued_quantity_summary(
            filtered,
            "methodology_name",
            "issued_quantity",
        )
        render_bar_chart(
            methodology_totals.head(10),
            "methodology_name",
            "issued_quantity",
        )
        st.dataframe(methodology_totals, **DATAFRAME_KWARGS)
    with summary3:
        st.subheader("Issued Quantity by Credit Unit")
        credit_unit_totals = issued_quantity_summary(
            filtered,
            "credit_unit",
            "issued_quantity",
        )
        render_bar_chart(credit_unit_totals, "credit_unit", "issued_quantity")
        st.dataframe(credit_unit_totals, **DATAFRAME_KWARGS)


def render_jcm_source_views(
    methodologies: pd.DataFrame,
    projects: pd.DataFrame,
    issuance: pd.DataFrame,
    rules: pd.DataFrame,
) -> None:
    with st.expander("Methodologies", expanded=True):
        st.metric("Methodologies", f"{len(methodologies):,}")
        st.dataframe(methodologies, **DATAFRAME_KWARGS)

    with st.expander("Projects", expanded=True):
        st.metric("Projects", f"{len(projects):,}")
        st.dataframe(projects, **DATAFRAME_KWARGS)

    with st.expander("Issuance", expanded=True):
        issuance_display = clean_numeric_column(issuance, "issued_amount")
        st.metric("Issuance rows", f"{len(issuance_display):,}")
        if "issued_amount" in issuance_display.columns:
            st.metric(
                "Issued amount",
                f"{issuance_display['issued_amount'].sum():,.0f}",
            )
        st.dataframe(issuance_display, **DATAFRAME_KWARGS)

    with st.expander("Rules / Forms", expanded=False):
        st.metric("Rules / forms", f"{len(rules):,}")
        st.dataframe(rules, **DATAFRAME_KWARGS)


def render_gold_standard_source_view(gs_projects: pd.DataFrame) -> None:
    if gs_projects.empty:
        st.warning("No Gold Standard projects CSV found.")
        return

    projects = clean_numeric_column(gs_projects.fillna(""), "estimated_annual_credits")
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Projects", f"{len(projects):,}")
    metric2.metric("Countries", f"{projects['country'].replace('', pd.NA).nunique():,}")
    metric3.metric("Statuses", f"{projects['status'].replace('', pd.NA).nunique():,}")
    metric4.metric(
        "Estimated annual credits",
        f"{projects['estimated_annual_credits'].sum():,.0f}"
        if "estimated_annual_credits" in projects.columns
        else "0",
    )
    st.dataframe(projects, **DATAFRAME_KWARGS)


def render_puro_source_view(
    puro_projects: pd.DataFrame,
    puro_issuances: pd.DataFrame,
) -> None:
    if puro_projects.empty or puro_issuances.empty:
        st.warning("No full Puro Earth registry outputs found.")
        return

    projects = puro_projects.fillna("").copy()
    issuances = clean_numeric_column(puro_issuances.fillna(""), "issued_qty")
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Projects", f"{len(projects):,}")
    metric2.metric("Issuance rows", f"{len(issuances):,}")
    metric3.metric(
        "Issued quantity",
        f"{issuances['issued_qty'].sum():,.0f}" if "issued_qty" in issuances.columns else "0",
    )
    metric4.metric("Countries", f"{projects['country'].replace('', pd.NA).nunique():,}")

    st.subheader("Puro Projects")
    st.dataframe(projects, **DATAFRAME_KWARGS)
    st.subheader("Puro Issuances")
    st.dataframe(issuances, **DATAFRAME_KWARGS)


def render_source_views(
    methodologies: pd.DataFrame,
    projects: pd.DataFrame,
    issuance: pd.DataFrame,
    rules: pd.DataFrame,
    gs_projects: pd.DataFrame,
    puro_projects: pd.DataFrame,
    puro_issuances: pd.DataFrame,
) -> None:
    st.header("Source Views")
    source = st.selectbox(
        "Source",
        ["JCM Mongolia-Japan", "Gold Standard", "Puro Earth"],
    )

    if source == "JCM Mongolia-Japan":
        render_jcm_source_views(methodologies, projects, issuance, rules)
    elif source == "Gold Standard":
        render_gold_standard_source_view(gs_projects)
    else:
        render_puro_source_view(puro_projects, puro_issuances)


def render_data_quality(
    unified_projects: pd.DataFrame,
    unified_issuances: pd.DataFrame,
) -> None:
    st.header("Data Quality")
    st.write(
        "These checks are lightweight profiling views over the unified outputs. "
        "They do not change source data; they highlight where registry exports are "
        "incomplete, where a parser may need review, or where a source simply does "
        "not publish a field."
    )

    if unified_projects.empty:
        show_missing_unified_warning("projects")
        return
    if unified_issuances.empty:
        show_missing_unified_warning("issuances")
        return

    projects = clean_unified_projects(unified_projects)
    issuances = clean_unified_issuances(unified_issuances)

    summary1, summary2 = st.columns(2)
    with summary1:
        st.subheader("Project Missing Values")
        st.caption(
            "Blank counts by unified project column. High counts can be normal when "
            "a source does not publish that field, such as project type or estimated "
            "annual credits."
        )
        st.dataframe(missing_values(projects), **DATAFRAME_KWARGS)
    with summary2:
        st.subheader("Issuance Missing Values")
        st.caption(
            "Blank counts by unified issuance column. Missing dates or quantities are "
            "more operationally important than optional attributes like durability."
        )
        st.dataframe(missing_values(issuances), **DATAFRAME_KWARGS)

    st.subheader("Projects Missing Methodology")
    st.caption(
        "Projects listed here have no methodology name in the unified projects table. "
        "This often reflects catalogue exports where methodology details are not yet "
        "available, rather than a failed row."
    )
    projects_missing_methodology = projects[projects["methodology_name"] == ""].copy()
    st.metric("Count", f"{len(projects_missing_methodology):,}")
    st.dataframe(projects_missing_methodology, **DATAFRAME_KWARGS)

    st.subheader("Issuances Missing Date or Issued Quantity")
    st.caption(
        "These rows are less useful for time series or volume analysis. They should be "
        "reviewed before building totals by period or issuance-date charts."
    )
    issuances_missing_core = issuances[
        (issuances["issuance_date"] == "") | (issuances["issued_quantity"].isna())
    ].copy()
    st.metric("Count", f"{len(issuances_missing_core):,}")
    st.dataframe(issuances_missing_core, **DATAFRAME_KWARGS)

    st.subheader("Unmatched Issuances")
    st.caption(
        "This compares each issuance row's source_id and source_project_id with the "
        "unified projects table. A nonzero count means issuance records exist without "
        "a corresponding unified project row."
    )
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
    unmatched = issuances[unmatched_mask].copy()
    st.metric("Count", f"{len(unmatched):,}")
    st.dataframe(unmatched, **DATAFRAME_KWARGS)


def render_admin(source_inventory: pd.DataFrame) -> None:
    st.header("Admin / Source Inventory")

    if source_inventory.empty:
        st.warning("No source_inventory.csv found.")
        return

    st.write(
        "Planning view for candidate carbon methodology and registry sources. "
        "Use it to prioritize future parser work."
    )

    priority_filter = st.multiselect(
        "Filter by priority",
        non_empty_options(source_inventory.fillna(""), "priority"),
        default=non_empty_options(source_inventory.fillna(""), "priority"),
    )
    action_filter = st.multiselect(
        "Filter by recommended next action",
        non_empty_options(source_inventory.fillna(""), "recommended_next_action"),
        default=non_empty_options(source_inventory.fillna(""), "recommended_next_action"),
    )

    filtered = source_inventory.fillna("").copy()
    filtered = apply_multiselect_filter(filtered, "priority", priority_filter)
    filtered = apply_multiselect_filter(
        filtered,
        "recommended_next_action",
        action_filter,
    )

    st.dataframe(filtered, **DATAFRAME_KWARGS)

    st.subheader("Recommended Next Parser Candidates")
    candidates = filtered[
        filtered["recommended_next_action"].isin(["inspect", "parse"])
    ].copy()
    if candidates.empty:
        st.info("No parser candidates selected.")
    else:
        st.dataframe(candidates, **DATAFRAME_KWARGS)

    st.download_button(
        "Download source inventory CSV",
        filtered.to_csv(index=False),
        file_name="source_inventory.csv",
        mime="text/csv",
    )


st.set_page_config(
    page_title="Carbon Registry Intelligence Database",
    layout="wide",
)

st.title("Carbon Registry Intelligence Database")
st.caption("v0.4 prototype: source-specific parsers -> unified tables -> explorer")

(
    methodologies,
    projects,
    issuance,
    rules,
    source_inventory,
    gs_projects,
    puro_projects,
    puro_issuances,
    unified_projects,
    unified_issuances,
) = load_data()

if not projects.empty and "methodology_no" in projects.columns:
    projects = projects.copy()
    projects["methodology_code_clean"] = projects["methodology_no"].apply(
        clean_methodology_code
    )

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Source Coverage",
        "Explore Projects",
        "Explore Issuances",
        "Source Views",
        "Data Quality",
        "Admin / Source Inventory",
    ],
)

if page == "Overview":
    render_overview(unified_projects, unified_issuances)
elif page == "Source Coverage":
    render_source_coverage(unified_projects, unified_issuances)
elif page == "Explore Projects":
    render_explore_projects(unified_projects)
elif page == "Explore Issuances":
    render_explore_issuances(unified_issuances)
elif page == "Source Views":
    render_source_views(
        methodologies,
        projects,
        issuance,
        rules,
        gs_projects,
        puro_projects,
        puro_issuances,
    )
elif page == "Data Quality":
    render_data_quality(unified_projects, unified_issuances)
else:
    render_admin(source_inventory)
