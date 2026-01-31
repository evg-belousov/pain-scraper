# src/dashboard/app.py

import streamlit as st
import pandas as pd
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.storage.database import PainDatabase


def show_pains_tab(db, summary):
    """Show pains exploration tab."""

    # Filters
    st.sidebar.header("Filters")

    industries = ["All"] + [i["industry"] for i in summary["by_industry"] if i["industry"]]
    selected_industry = st.sidebar.selectbox("Industry", industries)

    sources = ["All"] + [s["source"] for s in summary["by_source"] if s["source"]]
    selected_source = st.sidebar.selectbox("Source", sources)

    min_severity = st.sidebar.slider("Min Severity", 1, 10, 5)

    wtp_filter = st.sidebar.multiselect(
        "Willingness to Pay",
        ["high", "medium", "low", "none"],
        default=["high", "medium"]
    )

    ai_solvable = st.sidebar.checkbox("AI Solvable Only", value=False)

    # Summary tables
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("By Industry")
        if summary["by_industry"]:
            df_ind = pd.DataFrame(summary["by_industry"])
            if "avg_severity" in df_ind.columns:
                df_ind["avg_severity"] = df_ind["avg_severity"].round(1)
            st.dataframe(df_ind, hide_index=True)

    with col2:
        st.subheader("By Source")
        if summary["by_source"]:
            df_src = pd.DataFrame(summary["by_source"])
            st.dataframe(df_src, hide_index=True)

    st.markdown("---")

    # Get filtered pains
    pains = db.get_top_pains(
        industry=None if selected_industry == "All" else selected_industry,
        source=None if selected_source == "All" else selected_source,
        min_severity=min_severity,
        limit=100
    )

    # Apply additional filters
    if wtp_filter:
        pains = [p for p in pains if p.get("willingness_to_pay") in wtp_filter]

    if ai_solvable:
        pains = [p for p in pains if p.get("solvable_with_ai")]

    # Display
    st.subheader(f"Top Pains ({len(pains)} found)")

    if not pains:
        st.info("No pains found matching the current filters.")
    else:
        for pain in pains[:30]:
            severity = pain.get("severity", 0)
            color = "🔴" if severity >= 8 else "🟡" if severity >= 6 else "🟢"

            with st.expander(f"{color} {pain.get('pain_title')} | {pain.get('industry')} | Severity: {severity}/10"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Description:** {pain.get('pain_description')}")

                    try:
                        quotes = json.loads(pain.get("key_quotes", "[]"))
                    except (json.JSONDecodeError, TypeError):
                        quotes = []

                    if quotes:
                        st.markdown("**Key Quotes:**")
                        for q in quotes[:2]:
                            st.markdown(f"> {q}")

                    st.markdown(f"**Product Idea:** {pain.get('potential_product')}")
                    st.markdown(f"[View Source]({pain.get('source_url')})")

                with col2:
                    st.markdown(f"**Source:** {pain.get('source')}")
                    st.markdown(f"**Role:** {pain.get('role')}")
                    st.markdown(f"**Frequency:** {pain.get('frequency')}")
                    st.markdown(f"**Impact:** {pain.get('impact_type')}")
                    st.markdown(f"**WTP:** {pain.get('willingness_to_pay')}")
                    st.markdown(f"**AI Solvable:** {'Yes' if pain.get('solvable_with_ai') else 'No'}")

                    try:
                        tags = json.loads(pain.get("tags", "[]"))
                    except (json.JSONDecodeError, TypeError):
                        tags = []

                    if tags:
                        st.markdown(f"**Tags:** {', '.join(tags[:5])}")


def show_deep_analysis(analysis: dict):
    """Show deep analysis details."""
    verdict = analysis.get("verdict", "maybe")
    verdict_colors = {"go": "green", "maybe": "orange", "no_go": "red"}
    verdict_emoji = {"go": "✅", "maybe": "🤔", "no_go": "❌"}

    col1, col2, col3 = st.columns(3)
    col1.metric("Attractiveness", f"{analysis.get('attractiveness_score', 0)}/10")
    col2.metric("Verdict", f"{verdict_emoji.get(verdict, '?')} {verdict.upper()}")
    col3.metric("Market Size", analysis.get("market_size", "medium").title())

    st.markdown(f"**{analysis.get('main_argument', '')}**")

    # MVP
    st.markdown("##### MVP Concept")
    st.write(analysis.get("mvp_description", ""))

    try:
        features = json.loads(analysis.get("core_features", "[]"))
    except:
        features = []
    if features:
        st.markdown("**Core Features:**")
        for f in features:
            st.markdown(f"- {f}")

    # Target & Acquisition
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Target Audience")
        st.markdown(f"**Role:** {analysis.get('target_role', '')}")
        st.markdown(f"**Company Size:** {analysis.get('target_company_size', '')}")
        try:
            industries = json.loads(analysis.get("target_industries", "[]"))
        except:
            industries = []
        if industries:
            st.markdown(f"**Industries:** {', '.join(industries)}")

    with col2:
        st.markdown("##### Customer Acquisition")
        st.markdown(f"**Best Channel:** {analysis.get('best_channel', '')}")
        st.markdown(f"**Price Range:** {analysis.get('price_range', '')}")
        try:
            channels = json.loads(analysis.get("where_to_find_customers", "[]"))
        except:
            channels = []
        if channels:
            st.markdown(f"**Where to find:** {', '.join(channels[:3])}")

    # Competitors
    try:
        competitors = json.loads(analysis.get("competitors", "[]"))
    except:
        competitors = []
    if competitors:
        with st.expander("Competitors"):
            for comp in competitors:
                st.markdown(f"**{comp.get('name', 'Unknown')}** ({comp.get('price_range', '?')})")
                st.markdown(f"  Weakness: {comp.get('weakness', '')}")

    # Risks
    try:
        risks = json.loads(analysis.get("risks", "[]"))
    except:
        risks = []
    if risks:
        with st.expander("Risks"):
            for risk in risks:
                st.markdown(f"⚠️ {risk}")


def show_clusters_tab(db):
    """Show clusters exploration tab."""

    clusters = db.get_clusters(order_by="opportunity_score", limit=100)

    if not clusters:
        st.info("No clusters found. Run `python3 -m src.cluster` to generate clusters.")
        return

    # Filters
    min_size = st.sidebar.slider("Min Cluster Size", 1, 20, 3)
    filtered = [c for c in clusters if c.get("size", 0) >= min_size]

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Clusters", len(filtered))
    col2.metric("Total Pains in Clusters", sum(c.get("size", 0) for c in filtered))
    if filtered:
        col3.metric("Avg Opportunity Score", f"{sum(c.get('opportunity_score', 0) for c in filtered) / len(filtered):.1f}")

    st.markdown("---")

    # Cluster list
    st.subheader("Top Clusters by Opportunity Score")

    for cluster in filtered:
        opp_score = cluster.get("opportunity_score", 0)
        if opp_score >= 100:
            score_color = "🔥"
        elif opp_score >= 50:
            score_color = "⭐"
        else:
            score_color = "📊"

        with st.expander(
            f"{score_color} **{cluster.get('name')}** | "
            f"Size: {cluster.get('size')} | "
            f"Score: {opp_score:.1f}"
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Sample pains
                try:
                    samples = json.loads(cluster.get("sample_pains", "[]"))
                except (json.JSONDecodeError, TypeError):
                    samples = []

                if samples:
                    st.markdown("**Example Pains:**")
                    for sample in samples[:3]:
                        st.markdown(f"- {sample}")

                # Show pains in cluster button
                cluster_id = cluster.get("id")
                if cluster_id:
                    if st.button(f"Show all pains in cluster", key=f"btn_{cluster_id}"):
                        pains = db.get_pains_by_cluster(cluster_id)
                        for pain in pains[:10]:
                            st.markdown(f"- [{pain.get('source')}] {pain.get('pain_title')}")
                        if len(pains) > 10:
                            st.markdown(f"... and {len(pains) - 10} more")

            with col2:
                st.markdown(f"**Cluster ID:** {cluster.get('id')}")
                st.markdown(f"**Size:** {cluster.get('size')} pains")
                st.markdown(f"**Avg Severity:** {cluster.get('avg_severity', 0):.1f}")
                st.markdown(f"**Avg WTP:** {cluster.get('avg_wtp', 'medium')}")
                st.markdown(f"**Opportunity Score:** {opp_score:.1f}")

                try:
                    industries = json.loads(cluster.get("top_industries", "[]"))
                except (json.JSONDecodeError, TypeError):
                    industries = []

                if industries:
                    st.markdown(f"**Industries:** {', '.join(industries)}")

            # Deep Analysis section
            analysis = db.get_deep_analysis(cluster_id)
            if analysis:
                st.markdown("---")
                show_deep_analysis(analysis)
            else:
                st.markdown("---")
                st.info("Deep analysis not available. Run `python3 -m src.analyze --cluster-id " + str(cluster_id) + "` to generate.")


def main():
    st.set_page_config(page_title="Pain Point Explorer", page_icon="🔍", layout="wide")

    st.title("Pain Point Explorer")

    db = PainDatabase()
    summary = db.get_summary()

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pains", summary["total"])
    col2.metric("Industries", len(summary["by_industry"]))
    col3.metric("Sources", len(summary["by_source"]))
    clusters = db.get_clusters(limit=1000)
    col4.metric("Clusters", len(clusters))

    st.markdown("---")

    # Tabs
    tab1, tab2 = st.tabs(["Pains", "Clusters"])

    with tab1:
        show_pains_tab(db, summary)

    with tab2:
        show_clusters_tab(db)


if __name__ == "__main__":
    main()
