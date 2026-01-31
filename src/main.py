# src/main.py

import asyncio
import argparse
import os
from dotenv import load_dotenv

from src.collectors.hackernews import HackerNewsCollector
from src.collectors.indiehackers import IndieHackersCollector
from src.collectors.appstore import AppStoreCollector
from src.collectors.youtube import YouTubeCollector
from src.collectors.reddit_pullpush import RedditPullpushCollector
from src.collectors.stackexchange import StackExchangeCollector
from src.analyzer.classifier import PainClassifier
from src.storage.database import PainDatabase
from src.tracking.progress import ProgressTracker
from src.tracking.costs import CostTracker

# Load environment variables
load_dotenv()


async def run_collection(sources: list, limit: int):
    """Run data collection with progress tracking."""

    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\nError: OPENAI_API_KEY not set in .env file")
        return

    # Initialize database and tracking
    db = PainDatabase()
    progress = ProgressTracker(db)
    cost_tracker = CostTracker(db)

    # Start run
    run_id = progress.start_run()
    cost_tracker.set_run_id(run_id)

    try:
        all_data = []

        # Collect data
        if "hn" in sources or "all" in sources:
            print("\n Collecting from Hacker News...")
            try:
                collector = HackerNewsCollector()
                data = await collector.collect(limit=limit)
                all_data.extend(data)
                progress.increment_collected("hn", len(data), len(data))
            except Exception as e:
                progress.add_error(f"HN: {str(e)}")

        if "ih" in sources or "all" in sources:
            print("\n Collecting from Indie Hackers...")
            try:
                collector = IndieHackersCollector()
                data = await collector.collect(limit=limit)
                all_data.extend(data)
                progress.increment_collected("indiehackers", len(data), len(data))
            except Exception as e:
                progress.add_error(f"IH: {str(e)}")

        if "appstore" in sources or "all" in sources:
            print("\n Collecting from App Store...")
            try:
                collector = AppStoreCollector()
                data = await collector.collect(limit=limit)
                all_data.extend(data)
                progress.increment_collected("appstore", len(data), len(data))
            except Exception as e:
                progress.add_error(f"AppStore: {str(e)}")

        if "youtube" in sources or "all" in sources:
            print("\n Collecting from YouTube...")
            try:
                collector = YouTubeCollector()
                data = await collector.collect(limit=limit)
                all_data.extend(data)
                progress.increment_collected("youtube", len(data), len(data))
            except ValueError as e:
                print(f"   Skipped: {e}")
            except Exception as e:
                progress.add_error(f"YouTube: {str(e)}")

        if "reddit" in sources or "all" in sources:
            print("\n Collecting from Reddit (Pullpush)...")
            try:
                collector = RedditPullpushCollector()
                data = await collector.collect(limit=limit)
                all_data.extend(data)
                progress.increment_collected("reddit", len(data), len(data))
            except Exception as e:
                progress.add_error(f"Reddit: {str(e)}")

        if "stackexchange" in sources or "se" in sources or "all" in sources:
            print("\n Collecting from Stack Exchange...")
            try:
                collector = StackExchangeCollector()
                data = await collector.collect(limit=limit)
                all_data.extend(data)
                progress.increment_collected("stackexchange", len(data), len(data))
            except Exception as e:
                progress.add_error(f"SE: {str(e)}")

        print(f"\n Total collected: {len(all_data)} items")

        if not all_data:
            print("\nNo data collected. Check your configuration.")
            progress.finish_run(status="completed")
            return

        # Classification
        print("\n Analyzing with GPT...")
        classifier = PainClassifier(cost_tracker=cost_tracker)

        pains = []
        for i, item in enumerate(all_data):
            result = classifier.classify(item)

            if result and result.get("is_business_pain"):
                pains.append(result)
                progress.increment_analyzed()

            # Track cost
            cost = cost_tracker.get_last_cost()
            progress.add_cost(cost)

            # Print progress
            print(f"   Processing {i+1}/{len(all_data)}...", end="\r")

        print(f"\n   Identified {len(pains)} business pains")

        if not pains:
            print("\nNo business pains identified.")
            progress.finish_run(status="completed")
            return

        # Save
        print("\n Saving to database...")

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

        progress.finish_run(status="completed")

    except Exception as e:
        progress.add_error(str(e))
        progress.finish_run(status="failed")
        raise


def main():
    parser = argparse.ArgumentParser(description="Collect business pain points")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["all"],
        choices=["all", "hn", "ih", "appstore", "youtube", "reddit", "stackexchange", "se"],
        help="Sources to collect from"
    )
    parser.add_argument("--limit", type=int, default=50, help="Items per source")

    args = parser.parse_args()

    asyncio.run(run_collection(args.sources, args.limit))


if __name__ == "__main__":
    main()
