# src/cluster.py

import argparse
import os
from dotenv import load_dotenv

from src.analyzer.clustering import PainClusterer

# Load environment variables
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Cluster pain points")
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=3,
        help="Minimum records for a cluster (default: 3)"
    )

    args = parser.parse_args()

    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set in .env file")
        return

    print("=" * 60)
    print("PAIN POINT CLUSTERING")
    print("=" * 60)

    clusterer = PainClusterer()
    clusters = clusterer.run_clustering(min_cluster_size=args.min_cluster_size)

    if not clusters:
        print("\nNo clusters found.")
        return

    print("\n" + "=" * 60)
    print(f"RESULTS: {len(clusters)} clusters found")
    print("=" * 60)

    print("\nTop 10 by Opportunity Score:\n")

    for i, c in enumerate(clusters[:10], 1):
        print(f"{i}. {c.name}")
        print(f"   Size: {c.size} | Severity: {c.avg_severity:.1f} | WTP: {c.avg_wtp}")
        print(f"   Opportunity Score: {c.opportunity_score:.1f}")
        print(f"   Industries: {', '.join(c.top_industries)}")
        print(f"   Examples: {c.sample_pains[0][:80]}...")
        print()

    print("=" * 60)
    print("Clusters saved to database.")
    print("Run `streamlit run src/dashboard/app.py` to explore.")


if __name__ == "__main__":
    main()
