# src/dashboard/app.py

import streamlit as st
import pandas as pd
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.storage.database import PainDatabase


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
    high_severity_count = len([p for p in db.get_top_pains(min_severity=7, limit=1000)])
    col4.metric("High Severity (7+)", high_severity_count)

    st.markdown("---")

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
        st.info("No pains found matching the current filters. Try adjusting the filters or run the collector to gather more data.")
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
                    st.markdown(f"**Complexity:** {pain.get('solution_complexity')}")

                    try:
                        tags = json.loads(pain.get("tags", "[]"))
                    except (json.JSONDecodeError, TypeError):
                        tags = []

                    if tags:
                        st.markdown(f"**Tags:** {', '.join(tags[:5])}")


if __name__ == "__main__":
    main()
