# src/main.py

import asyncio
import argparse
import os
from dotenv import load_dotenv

from src.collectors.hackernews import HackerNewsCollector
from src.collectors.indiehackers import IndieHackersCollector
from src.collectors.appstore import AppStoreCollector
from src.collectors.youtube import YouTubeCollector
from src.analyzer.classifier import PainClassifier
from src.storage.database import PainDatabase

# Load environment variables
load_dotenv()


async def run_collection(sources: list, limit: int):
    """Run data collection."""

    print("=" * 60)
    print("PAIN POINT COLLECTOR")
    print("=" * 60)

    # Validate API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\nError: ANTHROPIC_API_KEY not set in .env file")
        return

    all_data = []

    # Collect data
    if "hn" in sources or "all" in sources:
        print("\n Collecting from Hacker News...")
        collector = HackerNewsCollector()
        data = await collector.collect(limit=limit)
        all_data.extend(data)
        print(f"   Found {len(data)} items")

    if "ih" in sources or "all" in sources:
        print("\n Collecting from Indie Hackers...")
        collector = IndieHackersCollector()
        data = await collector.collect(limit=limit)
        all_data.extend(data)
        print(f"   Found {len(data)} items")

    if "appstore" in sources or "all" in sources:
        print("\n Collecting from App Store...")
        collector = AppStoreCollector()
        data = await collector.collect(limit=limit)
        all_data.extend(data)
        print(f"   Found {len(data)} items")

    if "youtube" in sources or "all" in sources:
        print("\n Collecting from YouTube...")
        try:
            collector = YouTubeCollector()
            data = await collector.collect(limit=limit)
            all_data.extend(data)
            print(f"   Found {len(data)} items")
        except ValueError as e:
            print(f"   Skipped: {e}")

    print(f"\n Total collected: {len(all_data)} items")

    if not all_data:
        print("\nNo data collected. Check your configuration.")
        return

    # Classification
    print("\n Analyzing with Claude...")
    classifier = PainClassifier()

    def progress(current, total):
        print(f"   Processing {current}/{total}...", end="\r")

    pains = classifier.classify_batch(all_data, progress_callback=progress)
    print(f"\n   Identified {len(pains)} business pains")

    if not pains:
        print("\nNo business pains identified.")
        return

    # Save
    print("\n Saving to database...")
    db = PainDatabase()

    saved = 0
    for pain in pains:
        if db.insert_pain(pain):
            saved += 1

    print(f"   Saved {saved} new pains")

    # Summary
    summary = db.get_summary()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nTotal pains in database: {summary['total']}")

    print("\nBy Industry:")
    for item in summary["by_industry"][:10]:
        avg_sev = item['avg_severity']
        if avg_sev:
            print(f"   {item['industry']}: {item['count']} (avg severity: {avg_sev:.1f})")
        else:
            print(f"   {item['industry']}: {item['count']}")

    print("\nBy Source:")
    for item in summary["by_source"]:
        print(f"   {item['source']}: {item['count']}")

    print("\n Top 5 Pains:")
    for pain in db.get_top_pains(limit=5):
        print(f"   [{pain['severity']}/10] {pain['pain_title']}")
        print(f"       Industry: {pain['industry']} | WTP: {pain['willingness_to_pay']}")
        print(f"       -> {pain['potential_product']}")

    print("\n Done! Run `streamlit run src/dashboard/app.py` to explore.")


def main():
    parser = argparse.ArgumentParser(description="Collect business pain points")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["all"],
        choices=["all", "hn", "ih", "appstore", "youtube"],
        help="Sources to collect from"
    )
    parser.add_argument("--limit", type=int, default=50, help="Items per source")

    args = parser.parse_args()

    asyncio.run(run_collection(args.sources, args.limit))


if __name__ == "__main__":
    main()
