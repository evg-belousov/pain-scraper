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
    st.set_page_config(
        page_title="Pain Point Explorer",
        page_icon="🔍",
        layout="wide"
    )

    st.title("Pain Point Explorer")
    st.markdown("*Validated business problems from Reddit*")

    db = PainDatabase()

    # Sidebar filters
    st.sidebar.header("Filters")

    industries = db.get_industries_summary()
    industry_options = ["All"] + [i["industry"] for i in industries if i["industry"]]
    selected_industry = st.sidebar.selectbox("Industry", industry_options)

    min_severity = st.sidebar.slider("Minimum Severity", 1, 10, 5)

    wtp_filter = st.sidebar.multiselect(
        "Willingness to Pay",
        ["high", "medium", "low", "none"],
        default=["high", "medium"]
    )

    ai_solvable = st.sidebar.checkbox("AI Solvable Only", value=False)

    # Main content - metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_pains = len(db.get_top_pains(min_severity=1, limit=10000))
        st.metric("Total Pains", total_pains)

    with col2:
        high_severity = len(db.get_top_pains(min_severity=8, limit=10000))
        st.metric("Critical (8+)", high_severity)

    with col3:
        st.metric("Industries", len(industries))

    with col4:
        high_wtp = sum(i["high_wtp_count"] or 0 for i in industries)
        st.metric("High WTP", int(high_wtp))

    st.markdown("---")

    # Industry overview
    st.subheader("Industries Overview")

    if industries:
        df_industries = pd.DataFrame(industries)
        if "avg_severity" in df_industries.columns:
            df_industries["avg_severity"] = df_industries["avg_severity"].round(1)
        st.dataframe(
            df_industries,
            column_config={
                "industry": "Industry",
                "count": "Pain Count",
                "avg_severity": "Avg Severity",
                "high_wtp_count": "High WTP"
            },
            hide_index=True
        )

    st.markdown("---")

    # Pain list
    st.subheader("Top Pains")

    industry_filter = None if selected_industry == "All" else selected_industry
    pains = db.get_top_pains(
        industry=industry_filter,
        min_severity=min_severity,
        limit=100
    )

    # Apply additional filters
    if wtp_filter:
        pains = [p for p in pains if p.get("willingness_to_pay") in wtp_filter]

    if ai_solvable:
        pains = [p for p in pains if p.get("solvable_with_ai")]

    if not pains:
        st.info("No pains found matching the current filters. Try adjusting the filters or run the scraper to collect more data.")
    else:
        for pain in pains[:20]:
            severity = pain.get("severity", 0)
            if severity >= 8:
                severity_color = "🔴"
            elif severity >= 6:
                severity_color = "🟡"
            else:
                severity_color = "🟢"

            with st.expander(
                f"{severity_color} **{pain.get('pain_title')}** | "
                f"r/{pain.get('subreddit')} | "
                f"Severity: {severity}/10 | "
                f"WTP: {pain.get('willingness_to_pay')}"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Description:** {pain.get('pain_description')}")

                    try:
                        quotes = json.loads(pain.get("key_quotes", "[]"))
                    except (json.JSONDecodeError, TypeError):
                        quotes = []

                    if quotes:
                        st.markdown("**Key Quotes:**")
                        for quote in quotes[:3]:
                            st.markdown(f"> {quote}")

                    st.markdown(f"**Product Idea:** {pain.get('potential_product_idea')}")
                    st.markdown(f"[View Original Post]({pain.get('post_url')})")

                with col2:
                    st.markdown(f"**Industry:** {pain.get('industry')}")
                    st.markdown(f"**Role:** {pain.get('role')}")
                    st.markdown(f"**Frequency:** {pain.get('frequency')}")
                    st.markdown(f"**Financial Impact:** {pain.get('financial_impact')}")
                    st.markdown(f"**Time Impact:** {pain.get('time_impact')}")
                    st.markdown(f"**Complexity:** {pain.get('solution_complexity')}")
                    st.markdown(f"**AI Solvable:** {'Yes' if pain.get('solvable_with_ai') else 'No'}")

                    try:
                        tags = json.loads(pain.get("tags", "[]"))
                    except (json.JSONDecodeError, TypeError):
                        tags = []

                    if tags:
                        st.markdown(f"**Tags:** {', '.join(tags)}")


if __name__ == "__main__":
    main()
