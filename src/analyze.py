# src/analyze.py

import argparse
import os
from dotenv import load_dotenv

from src.analyzer.deep_analysis import DeepAnalyzer

# Load environment variables
load_dotenv()


def print_analysis(analysis, cluster_name: str = None):
    """Pretty print analysis results."""
    verdict_emoji = {"go": "✅", "maybe": "🤔", "no_go": "❌"}
    emoji = verdict_emoji.get(analysis.verdict, "?")

    print(f"\n{emoji} Cluster #{analysis.cluster_id}: {cluster_name or 'Unknown'}")
    print(f"   Attractiveness: {analysis.attractiveness_score}/10")
    print(f"   Verdict: {analysis.verdict.upper()}")
    print(f"\n   💡 {analysis.main_argument}")

    print(f"\n   📊 Target: {analysis.target_role}")
    print(f"   🏢 Company Size: {analysis.target_company_size}")
    print(f"   📈 Market Size: {analysis.market_size}")

    print(f"\n   🛠️ MVP: {analysis.mvp_description[:200]}...")
    print(f"   ⭐ Core Features:")
    for f in analysis.core_features[:3]:
        print(f"      - {f}")

    print(f"\n   🎯 Best Channel: {analysis.best_channel}")
    print(f"   💰 Price Range: {analysis.price_range}")

    print(f"\n   ⚔️ Competitors:")
    for comp in analysis.competitors[:3]:
        print(f"      - {comp.get('name', 'Unknown')} ({comp.get('price_range', '?')})")
        print(f"        Weakness: {comp.get('weakness', '?')[:80]}")

    print(f"\n   ⚠️ Top Risks:")
    for risk in analysis.risks[:2]:
        print(f"      - {risk[:100]}")


def main():
    parser = argparse.ArgumentParser(description="Deep analysis of pain clusters")
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top clusters to analyze (default: 10)"
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=5,
        help="Minimum cluster size (default: 5)"
    )
    parser.add_argument(
        "--cluster-id",
        type=int,
        default=None,
        help="Analyze specific cluster by ID"
    )

    args = parser.parse_args()

    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set in .env file")
        return

    print("=" * 60)
    print("DEEP CLUSTER ANALYSIS")
    print("=" * 60)

    analyzer = DeepAnalyzer()

    if args.cluster_id:
        # Analyze single cluster
        print(f"\nAnalyzing cluster #{args.cluster_id}...")
        analysis = analyzer.analyze_cluster(args.cluster_id)
        if analysis:
            print_analysis(analysis)
        else:
            print(f"Failed to analyze cluster #{args.cluster_id}")
    else:
        # Analyze top clusters
        print(f"\nAnalyzing top {args.top} clusters (min size: {args.min_size})...")
        results = analyzer.analyze_top_clusters(
            top_n=args.top,
            min_size=args.min_size
        )

        if not results:
            print("\nNo new clusters to analyze.")
            return

        print(f"\n{'=' * 60}")
        print(f"RESULTS: Analyzed {len(results)} clusters")
        print("=" * 60)

        # Sort by attractiveness for display
        results.sort(key=lambda x: x.attractiveness_score, reverse=True)

        # Summary
        go_count = sum(1 for r in results if r.verdict == "go")
        maybe_count = sum(1 for r in results if r.verdict == "maybe")
        no_go_count = sum(1 for r in results if r.verdict == "no_go")

        print(f"\n📊 Summary:")
        print(f"   ✅ GO: {go_count}")
        print(f"   🤔 MAYBE: {maybe_count}")
        print(f"   ❌ NO GO: {no_go_count}")

        # Show GO opportunities first
        print(f"\n{'=' * 60}")
        print("TOP OPPORTUNITIES (GO verdict):")
        print("=" * 60)

        for analysis in results:
            if analysis.verdict == "go":
                print_analysis(analysis)

        # Show MAYBE opportunities
        if maybe_count > 0:
            print(f"\n{'=' * 60}")
            print("POTENTIAL OPPORTUNITIES (MAYBE verdict):")
            print("=" * 60)

            for analysis in results:
                if analysis.verdict == "maybe":
                    print_analysis(analysis)

    print(f"\n{'=' * 60}")
    print("Analysis complete. Run dashboard to explore details.")
    print("streamlit run src/dashboard/app.py")


if __name__ == "__main__":
    main()
