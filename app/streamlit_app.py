from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed" / "jcm_mn"
GLOBAL_DATA_DIR = PROJECT_ROOT / "data" / "processed"
GOLD_STANDARD_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "gold_standard"
PURO_EARTH_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "puro_earth"
CANONICAL_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "unified"


@st.cache_data
def load_data():
    methodologies = pd.read_csv(DATA_DIR / "methodologies.csv")
    projects = pd.read_csv(DATA_DIR / "projects_mongolia.csv")
    issuance = pd.read_csv(DATA_DIR / "issuance_records.csv")

    rules_path = DATA_DIR / "rules_forms.csv"
    if rules_path.exists():
        rules = pd.read_csv(rules_path)
    else:
        rules = pd.DataFrame()

    source_inventory_path = GLOBAL_DATA_DIR / "source_inventory.csv"
    if source_inventory_path.exists():
        source_inventory = pd.read_csv(source_inventory_path)
    else:
        source_inventory = pd.DataFrame()

    gs_projects_path = GOLD_STANDARD_DATA_DIR / "gs_projects.csv"
    if gs_projects_path.exists():
        gs_projects = pd.read_csv(gs_projects_path)
    else:
        gs_projects = pd.DataFrame()

    puro_projects_path = PURO_EARTH_DATA_DIR / "puro_projects_all.csv"
    if puro_projects_path.exists():
        puro_projects = pd.read_csv(puro_projects_path)
    else:
        puro_projects = pd.DataFrame()

    puro_issuances_path = PURO_EARTH_DATA_DIR / "puro_issuances_all.csv"
    if puro_issuances_path.exists():
        puro_issuances = pd.read_csv(puro_issuances_path)
    else:
        puro_issuances = pd.DataFrame()

    unified_projects_path = CANONICAL_DATA_DIR / "projects.csv"
    if unified_projects_path.exists():
        unified_projects = pd.read_csv(unified_projects_path)
    else:
        unified_projects = pd.DataFrame()

    unified_issuances_path = CANONICAL_DATA_DIR / "issuances.csv"
    if unified_issuances_path.exists():
        unified_issuances = pd.read_csv(unified_issuances_path)
    else:
        unified_issuances = pd.DataFrame()

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


st.set_page_config(
    page_title="Global Carbon Methodology DB - JCM Pilot",
    layout="wide",
)

st.title("Global Carbon Methodology Intelligence Database")
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

projects["methodology_code_clean"] = projects["methodology_no"].apply(
    clean_methodology_code
)

tab_overview, tab_all_projects, tab_all_issuances, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab_admin = st.tabs(
    [
        "Overview",
        "All Projects",
        "All Issuances",
        "Methodologies",
        "Projects",
        "Issuance",
        "Rules & Forms",
        "Methodology → Projects",
        "Gold Standard Projects",
        "Puro Earth",
        "Admin / Source Inventory",
    ]
)

with tab_overview:
    st.subheader("Overview")

    if unified_projects.empty or unified_issuances.empty:
        st.warning(
            "Unified outputs are missing. Run: "
            "`python -m etl.build_unified.build_projects` and "
            "`python -m etl.build_unified.build_issuances`"
        )
    else:
        overview_projects = unified_projects.fillna("").copy()
        overview_issuances = unified_issuances.fillna("").copy()
        overview_issuances["issued_quantity"] = pd.to_numeric(
            overview_issuances["issued_quantity"],
            errors="coerce",
        )

        project_methods = set(
            overview_projects["methodology_name"].replace("", pd.NA).dropna().unique()
        )
        issuance_methods = set(
            overview_issuances["methodology_name"].replace("", pd.NA).dropna().unique()
        )
        source_names = set(
            overview_projects["source_name"].replace("", pd.NA).dropna().unique()
        ) | set(
            overview_issuances["source_name"].replace("", pd.NA).dropna().unique()
        )

        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("Unified projects", len(overview_projects))
        metric2.metric("Unified issuances", len(overview_issuances))
        metric3.metric("Sources", len(source_names))
        metric4.metric(
            "Countries",
            overview_projects["country"].replace("", pd.NA).nunique(),
        )

        metric5, metric6, metric7 = st.columns(3)
        metric5.metric("Methodologies", len(project_methods | issuance_methods))
        metric6.metric(
            "Total issued quantity",
            f"{overview_issuances['issued_quantity'].sum():,.0f}",
        )
        metric7.metric(
            "Projects missing methodology",
            int((overview_projects["methodology_name"] == "").sum()),
        )

        st.markdown("### Source coverage")
        summary1, summary2, summary3 = st.columns(3)

        with summary1:
            st.markdown("#### Projects by source")
            projects_by_source = (
                overview_projects
                .groupby("source_name", as_index=False)
                .size()
                .rename(columns={"size": "projects"})
                .sort_values("projects", ascending=False)
            )
            st.dataframe(projects_by_source, use_container_width=True, hide_index=True)

        with summary2:
            st.markdown("#### Issuances by source")
            issuances_by_source = (
                overview_issuances
                .groupby("source_name", as_index=False)
                .size()
                .rename(columns={"size": "issuance_rows"})
                .sort_values("issuance_rows", ascending=False)
            )
            st.dataframe(issuances_by_source, use_container_width=True, hide_index=True)

        with summary3:
            st.markdown("#### Issued quantity by source")
            issued_by_source = (
                overview_issuances
                .groupby("source_name", as_index=False)["issued_quantity"]
                .sum()
                .sort_values("issued_quantity", ascending=False)
            )
            st.dataframe(issued_by_source, use_container_width=True, hide_index=True)

        st.markdown("### About / Data Model")
        st.markdown(
            """
Source-specific parsers preserve each registry's raw shape and source-specific fields.
The unified projects and issuances tables normalize the overlapping fields across sources.
This explorer uses those unified tables for cross-source comparison while keeping the original source tabs available for inspection.
"""
        )

with tab_admin:
    st.subheader("Source Inventory")

    if source_inventory.empty:
        st.warning("No source_inventory.csv found.")
    else:
        st.markdown(
            """
This table tracks candidate carbon methodology and registry sources for future expansion.

The goal is to decide which sources are worth parsing next.
"""
        )

        priority_filter = st.multiselect(
            "Filter by priority",
            sorted(source_inventory["priority"].dropna().unique()),
            default=sorted(source_inventory["priority"].dropna().unique()),
        )

        action_filter = st.multiselect(
            "Filter by recommended next action",
            sorted(source_inventory["recommended_next_action"].dropna().unique()),
            default=sorted(source_inventory["recommended_next_action"].dropna().unique()),
        )

        filtered_sources = source_inventory[
            source_inventory["priority"].isin(priority_filter)
            & source_inventory["recommended_next_action"].isin(action_filter)
        ].copy()

        st.dataframe(filtered_sources, use_container_width=True, hide_index=True)

        st.markdown("### Recommended next parser candidates")

        candidates = filtered_sources[
            filtered_sources["recommended_next_action"].isin(["inspect", "parse"])
        ].copy()

        if candidates.empty:
            st.info("No parser candidates selected.")
        else:
            st.dataframe(
                candidates[
                    [
                        "source_name",
                        "parser_difficulty",
                        "priority",
                        "recommended_next_action",
                        "notes",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.download_button(
            "Download source inventory CSV",
            filtered_sources.to_csv(index=False),
            file_name="source_inventory.csv",
            mime="text/csv",
        )

with tab_all_projects:
    st.subheader("All Projects")

    if unified_projects.empty:
        st.warning(
            "No unified projects CSV found. Run: "
            "`python -m etl.build_unified.build_projects` and "
            "`python -m etl.build_unified.build_issuances`"
        )
    else:
        unified_projects = unified_projects.fillna("").copy()

        metric1, metric2, metric3, metric4, metric5 = st.columns(5)
        metric1.metric("Total projects", len(unified_projects))
        metric2.metric("Sources", unified_projects["source_name"].replace("", pd.NA).nunique())
        metric3.metric("Countries", unified_projects["country"].replace("", pd.NA).nunique())
        metric4.metric(
            "Methodologies",
            unified_projects["methodology_name"].replace("", pd.NA).nunique(),
        )
        metric5.metric(
            "Missing methodology",
            int((unified_projects["methodology_name"] == "").sum()),
        )

        source_options = sorted(
            unified_projects["source_name"].replace("", pd.NA).dropna().unique()
        )
        country_options = sorted(
            unified_projects["country"].replace("", pd.NA).dropna().unique()
        )
        project_type_options = sorted(
            unified_projects["project_type"].replace("", pd.NA).dropna().unique()
        )
        methodology_options = sorted(
            unified_projects["methodology_name"].replace("", pd.NA).dropna().unique()
        )
        status_options = sorted(
            unified_projects["status"].replace("", pd.NA).dropna().unique()
        )

        source_filter = st.multiselect(
            "Filter by unified source",
            source_options,
            default=source_options,
            key="unified_projects_source_filter",
        )

        country_filter = st.multiselect(
            "Filter by unified country",
            country_options,
            default=[],
            key="unified_projects_country_filter",
        )

        project_type_filter = st.multiselect(
            "Filter by unified project type",
            project_type_options,
            default=[],
            key="unified_projects_project_type_filter",
        )

        methodology_filter = st.multiselect(
            "Filter by unified methodology",
            methodology_options,
            default=[],
            key="unified_projects_methodology_filter",
        )

        status_filter = st.multiselect(
            "Filter by unified status",
            status_options,
            default=[],
            key="unified_projects_status_filter",
        )

        filtered_unified_projects = unified_projects.copy()
        if source_filter:
            filtered_unified_projects = filtered_unified_projects[
                filtered_unified_projects["source_name"].isin(source_filter)
            ]
        if country_filter:
            filtered_unified_projects = filtered_unified_projects[
                filtered_unified_projects["country"].isin(country_filter)
            ]
        if project_type_filter:
            filtered_unified_projects = filtered_unified_projects[
                filtered_unified_projects["project_type"].isin(project_type_filter)
            ]
        if methodology_filter:
            filtered_unified_projects = filtered_unified_projects[
                filtered_unified_projects["methodology_name"].isin(methodology_filter)
            ]
        if status_filter:
            filtered_unified_projects = filtered_unified_projects[
                filtered_unified_projects["status"].isin(status_filter)
            ]
        filtered_unified_projects = filtered_unified_projects.copy()

        st.dataframe(
            filtered_unified_projects,
            use_container_width=True,
            hide_index=True,
            column_config={
                "project_url": st.column_config.LinkColumn("project_url"),
            },
        )

        st.download_button(
            "Download unified projects CSV",
            filtered_unified_projects.to_csv(index=False),
            file_name="unified_projects.csv",
            mime="text/csv",
        )

        st.markdown("### Source split summary")
        source_split = (
            filtered_unified_projects
            .groupby("source_name", as_index=False)
            .size()
            .rename(columns={"size": "projects"})
            .sort_values("projects", ascending=False)
        )
        if not source_split.empty:
            source_split["share_pct"] = (
                source_split["projects"] / source_split["projects"].sum() * 100
            ).round(1)
        st.dataframe(source_split, use_container_width=True, hide_index=True)

        summary1, summary2, summary3 = st.columns(3)

        with summary1:
            st.markdown("### Projects by source")
            st.dataframe(source_split, use_container_width=True, hide_index=True)

        with summary2:
            st.markdown("### Top 15 countries")
            top_countries = (
                filtered_unified_projects[filtered_unified_projects["country"] != ""]
                .groupby("country", as_index=False)
                .size()
                .rename(columns={"size": "projects"})
                .sort_values("projects", ascending=False)
                .head(15)
            )
            st.dataframe(top_countries, use_container_width=True, hide_index=True)

        with summary3:
            st.markdown("### Top 15 methodologies")
            top_methodologies = (
                filtered_unified_projects[
                    filtered_unified_projects["methodology_name"] != ""
                ]
                .groupby("methodology_name", as_index=False)
                .size()
                .rename(columns={"size": "projects"})
                .sort_values("projects", ascending=False)
                .head(15)
            )
            st.dataframe(top_methodologies, use_container_width=True, hide_index=True)

with tab_all_issuances:
    st.subheader("All Issuances")

    if unified_issuances.empty:
        st.warning(
            "No unified issuances CSV found. Run: "
            "`python -m etl.build_unified.build_projects` and "
            "`python -m etl.build_unified.build_issuances`"
        )
    else:
        unified_issuances = unified_issuances.fillna("").copy()
        unified_issuances["issued_quantity"] = pd.to_numeric(
            unified_issuances["issued_quantity"],
            errors="coerce",
        )

        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("Total issuance rows", len(unified_issuances))
        metric2.metric(
            "Total issued quantity",
            f"{unified_issuances['issued_quantity'].sum():,.0f}",
        )
        metric3.metric("Sources", unified_issuances["source_name"].replace("", pd.NA).nunique())
        metric4.metric(
            "Methodologies",
            unified_issuances["methodology_name"].replace("", pd.NA).nunique(),
        )

        source_options = sorted(
            unified_issuances["source_name"].replace("", pd.NA).dropna().unique()
        )
        methodology_options = sorted(
            unified_issuances["methodology_name"].replace("", pd.NA).dropna().unique()
        )
        durability_options = sorted(
            unified_issuances["durability"].replace("", pd.NA).dropna().unique()
        )

        source_filter = st.multiselect(
            "Filter by issuance source",
            source_options,
            default=source_options,
            key="unified_issuances_source_filter",
        )

        methodology_filter = st.multiselect(
            "Filter by issuance methodology",
            methodology_options,
            default=[],
            key="unified_issuances_methodology_filter",
        )

        durability_filter = st.multiselect(
            "Filter by issuance durability",
            durability_options,
            default=[],
            key="unified_issuances_durability_filter",
        )

        filtered_unified_issuances = unified_issuances.copy()
        if source_filter:
            filtered_unified_issuances = filtered_unified_issuances[
                filtered_unified_issuances["source_name"].isin(source_filter)
            ]
        if methodology_filter:
            filtered_unified_issuances = filtered_unified_issuances[
                filtered_unified_issuances["methodology_name"].isin(methodology_filter)
            ]
        if durability_filter:
            filtered_unified_issuances = filtered_unified_issuances[
                filtered_unified_issuances["durability"].isin(durability_filter)
            ]
        filtered_unified_issuances = filtered_unified_issuances.copy()

        st.dataframe(filtered_unified_issuances, use_container_width=True, hide_index=True)

        st.download_button(
            "Download unified issuances CSV",
            filtered_unified_issuances.to_csv(index=False),
            file_name="unified_issuances.csv",
            mime="text/csv",
        )

        summary1, summary2, summary3, summary4 = st.columns(4)

        with summary1:
            st.markdown("### Issuance rows by source")
            issuance_rows_by_source = (
                filtered_unified_issuances
                .groupby("source_name", as_index=False)
                .size()
                .rename(columns={"size": "issuance_rows"})
                .sort_values("issuance_rows", ascending=False)
            )
            st.dataframe(issuance_rows_by_source, use_container_width=True, hide_index=True)

        with summary2:
            st.markdown("### Issued quantity by source")
            issued_by_source = (
                filtered_unified_issuances
                .groupby("source_name", as_index=False)["issued_quantity"]
                .sum()
                .sort_values("issued_quantity", ascending=False)
            )
            st.dataframe(issued_by_source, use_container_width=True, hide_index=True)

        with summary3:
            st.markdown("### Issued quantity by methodology")
            issued_by_methodology = (
                filtered_unified_issuances[
                    filtered_unified_issuances["methodology_name"] != ""
                ]
                .groupby("methodology_name", as_index=False)["issued_quantity"]
                .sum()
                .sort_values("issued_quantity", ascending=False)
            )
            st.dataframe(issued_by_methodology, use_container_width=True, hide_index=True)

        with summary4:
            st.markdown("### Issued quantity by credit unit")
            issued_by_credit_unit = (
                filtered_unified_issuances[
                    filtered_unified_issuances["credit_unit"] != ""
                ]
                .groupby("credit_unit", as_index=False)["issued_quantity"]
                .sum()
                .sort_values("issued_quantity", ascending=False)
            )
            st.dataframe(issued_by_credit_unit, use_container_width=True, hide_index=True)

with tab1:
    st.subheader("Methodologies")

    status_filter = st.multiselect(
        "Filter by status",
        sorted(methodologies["status"].dropna().unique()),
        default=sorted(methodologies["status"].dropna().unique()),
    )

    filtered = methodologies[
        methodologies["status"].isin(status_filter)
    ].copy()

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.download_button(
        "Download methodologies CSV",
        filtered.to_csv(index=False),
        file_name="jcm_mn_methodologies.csv",
        mime="text/csv",
    )

with tab2:
    st.subheader("Mongolia projects")

    project_status_filter = st.multiselect(
        "Filter by project status",
        sorted(projects["status"].dropna().unique()),
        default=sorted(projects["status"].dropna().unique()),
    )

    filtered_projects = projects[
        projects["status"].isin(project_status_filter)
    ].copy()

    st.dataframe(filtered_projects, use_container_width=True, hide_index=True)

    st.download_button(
        "Download Mongolia projects CSV",
        filtered_projects.to_csv(index=False),
        file_name="jcm_mn_projects.csv",
        mime="text/csv",
    )

with tab3:
    st.subheader("Issuance records")

    country_filter = st.multiselect(
        "Filter by credit allocation country",
        sorted(issuance["country"].dropna().unique()),
        default=sorted(issuance["country"].dropna().unique()),
    )

    filtered_issuance = issuance[
        issuance["country"].isin(country_filter)
    ].copy()

    st.dataframe(filtered_issuance, use_container_width=True, hide_index=True)

    issued_summary = (
        filtered_issuance
        .groupby("country", as_index=False)["issued_amount"]
        .sum()
    )

    st.markdown("### Issued amount by country")
    st.dataframe(issued_summary, use_container_width=True, hide_index=True)

    st.download_button(
        "Download issuance CSV",
        filtered_issuance.to_csv(index=False),
        file_name="jcm_mn_issuance.csv",
        mime="text/csv",
    )

with tab4:
    st.subheader("Rules & Forms")

    if rules.empty:
        st.warning(
            "No rules/forms CSV found. Run: "
            "`python -m etl.sources.jcm_mn.parse_rules`"
        )
    else:
        section_filter = st.multiselect(
            "Filter by section",
            sorted(rules["section"].dropna().unique()),
            default=sorted(rules["section"].dropna().unique()),
        )

        format_filter = st.multiselect(
            "Filter by file format",
            sorted(rules["file_format"].dropna().unique()),
            default=sorted(rules["file_format"].dropna().unique()),
        )

        filtered_rules = rules[
            rules["section"].isin(section_filter)
            & rules["file_format"].isin(format_filter)
        ].copy()

        st.dataframe(filtered_rules, use_container_width=True, hide_index=True)

        st.markdown("### Document links")

        for _, row in filtered_rules.iterrows():
            title = row["document_title"]
            fmt = row["file_format"]
            url = row["file_url"]
            st.markdown(f"- [{title}]({url}) `{fmt}`")

        st.download_button(
            "Download rules/forms CSV",
            filtered_rules.to_csv(index=False),
            file_name="jcm_mn_rules_forms.csv",
            mime="text/csv",
        )

with tab5:
    st.subheader("Methodology → Projects")

    selected_methodology = st.selectbox(
        "Select methodology",
        methodologies["methodology_code"].tolist(),
    )

    selected_row = methodologies[
        methodologies["methodology_code"] == selected_methodology
    ].iloc[0]

    st.markdown("### Methodology details")
    st.write("**Title:**", selected_row["title"])
    st.write("**Status:**", selected_row["status"])
    st.write("**Latest version:**", selected_row["latest_version"])
    st.write("**Approval date:**", selected_row["approval_date"])
    st.write("**Sectoral scope:**", selected_row["sectoral_scope"])

    related_projects = projects[
        projects["methodology_code_clean"] == selected_methodology
    ].copy()

    st.markdown("### Related Mongolia projects")

    if related_projects.empty:
        st.info("No related Mongolia projects found for this methodology.")
    else:
        st.dataframe(
            related_projects[
                [
                    "reference_no",
                    "project_title",
                    "status",
                    "registration_date",
                    "host_country_participant",
                    "japanese_participant",
                    "methodology_no",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        related_refs = related_projects["reference_no"].dropna().unique().tolist()

        related_issuance = issuance[
            issuance["reference_no"].isin(related_refs)
        ].copy()

        st.markdown("### Issuance records for related projects")

        if related_issuance.empty:
            st.info("No issuance records found for related projects.")
        else:
            st.dataframe(
                related_issuance,
                use_container_width=True,
                hide_index=True,
            )

with tab6:
    st.subheader("Gold Standard Projects")

    if gs_projects.empty:
        st.warning(
            "No Gold Standard projects CSV found. Run: "
            "`python -m etl.sources.gold_standard.parse_projects_export`"
        )
    else:
        st.metric("Total projects", len(gs_projects))

        status_filter = st.multiselect(
            "Filter by Gold Standard status",
            sorted(gs_projects["status"].dropna().unique()),
            default=sorted(gs_projects["status"].dropna().unique()),
        )

        country_filter = st.multiselect(
            "Filter by Gold Standard country",
            sorted(gs_projects["country"].dropna().unique()),
            default=sorted(gs_projects["country"].dropna().unique()),
        )

        project_type_filter = st.multiselect(
            "Filter by Gold Standard project type",
            sorted(gs_projects["project_type"].dropna().unique()),
            default=sorted(gs_projects["project_type"].dropna().unique()),
        )

        filtered_gs_projects = gs_projects[
            gs_projects["status"].isin(status_filter)
            & gs_projects["country"].isin(country_filter)
            & gs_projects["project_type"].isin(project_type_filter)
        ].copy()

        st.dataframe(filtered_gs_projects, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Gold Standard projects CSV",
            filtered_gs_projects.to_csv(index=False),
            file_name="gold_standard_projects.csv",
            mime="text/csv",
        )

with tab7:
    st.subheader("Puro Earth")

    if puro_projects.empty or puro_issuances.empty:
        st.warning(
            "No full Puro Earth registry outputs found. Run: "
            "`python etl/sources/puro_earth/parse_projects_playwright.py` and "
            "`python etl/sources/puro_earth/parse_issuances_playwright.py`"
        )
    else:
        puro_projects = puro_projects.copy()
        puro_issuances = puro_issuances.copy()
        puro_issuances["issued_qty"] = pd.to_numeric(
            puro_issuances["issued_qty"],
            errors="coerce",
        )

        metric1, metric2, metric3, metric4, metric5 = st.columns(5)
        metric1.metric("Total projects", len(puro_projects))
        metric2.metric("Total issuances", len(puro_issuances))
        metric3.metric("Total issued quantity", int(puro_issuances["issued_qty"].sum()))
        metric4.metric("Countries", puro_projects["country"].dropna().nunique())
        metric5.metric("Methodologies", puro_projects["methodology"].dropna().nunique())

        country_options = sorted(puro_projects["country"].dropna().unique())
        methodology_options = sorted(
            set(puro_projects["methodology"].dropna().unique())
            | set(puro_issuances["methodology"].dropna().unique())
        )
        durability_options = sorted(puro_issuances["durability"].dropna().unique())

        country_filter = st.multiselect(
            "Filter by Puro country",
            country_options,
            default=country_options,
            key="puro_country_filter",
        )

        methodology_filter = st.multiselect(
            "Filter by Puro methodology",
            methodology_options,
            default=methodology_options,
            key="puro_methodology_filter",
        )

        durability_filter = st.multiselect(
            "Filter by Puro durability",
            durability_options,
            default=durability_options,
            key="puro_durability_filter",
        )

        filtered_puro_projects = puro_projects[
            puro_projects["country"].isin(country_filter)
            & puro_projects["methodology"].isin(methodology_filter)
        ].copy()

        filtered_puro_issuances = puro_issuances[
            puro_issuances["methodology"].isin(methodology_filter)
            & puro_issuances["durability"].isin(durability_filter)
        ].copy()

        project_ids = filtered_puro_projects["project_id"].dropna().astype(str).unique()
        filtered_puro_issuances = filtered_puro_issuances[
            filtered_puro_issuances["project_id"].astype(str).isin(project_ids)
        ].copy()

        st.markdown("### Puro projects")
        st.dataframe(filtered_puro_projects, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Puro projects CSV",
            filtered_puro_projects.to_csv(index=False),
            file_name="puro_projects_all.csv",
            mime="text/csv",
        )

        st.markdown("### Puro issuances")
        st.dataframe(filtered_puro_issuances, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Puro issuances CSV",
            filtered_puro_issuances.to_csv(index=False),
            file_name="puro_issuances_all.csv",
            mime="text/csv",
        )

        summary1, summary2 = st.columns(2)

        with summary1:
            st.markdown("### Projects by methodology")
            projects_by_methodology = (
                filtered_puro_projects
                .groupby("methodology", as_index=False)
                .size()
                .rename(columns={"size": "projects"})
                .sort_values("projects", ascending=False)
            )
            st.dataframe(projects_by_methodology, use_container_width=True, hide_index=True)

            st.markdown("### Projects by country")
            projects_by_country = (
                filtered_puro_projects
                .groupby("country", as_index=False)
                .size()
                .rename(columns={"size": "projects"})
                .sort_values("projects", ascending=False)
            )
            st.dataframe(projects_by_country, use_container_width=True, hide_index=True)

        with summary2:
            st.markdown("### Issued quantity by methodology")
            issued_by_methodology = (
                filtered_puro_issuances
                .groupby("methodology", as_index=False)["issued_qty"]
                .sum()
                .sort_values("issued_qty", ascending=False)
            )
            st.dataframe(issued_by_methodology, use_container_width=True, hide_index=True)

            st.markdown("### Issued quantity by country")
            issuance_with_country = filtered_puro_issuances.merge(
                filtered_puro_projects[["project_id", "country"]],
                on="project_id",
                how="left",
            )
            issued_by_country = (
                issuance_with_country
                .groupby("country", as_index=False)["issued_qty"]
                .sum()
                .sort_values("issued_qty", ascending=False)
            )
            st.dataframe(issued_by_country, use_container_width=True, hide_index=True)
