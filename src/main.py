# src/main.py

import argparse
import os
from dotenv import load_dotenv

from src.config import SUBREDDITS, PAIN_KEYWORDS
from src.scraper.reddit import RedditScraper
from src.analyzer.classifier import PainClassifier
from src.storage.database import PainDatabase

# Load environment variables
load_dotenv()


def scrape_and_analyze(
    subreddits: list = None,
    keywords: list = None,
    limit_per_subreddit: int = 50
):
    """Main scraping and analysis pipeline."""

    subreddits = subreddits or SUBREDDITS
    keywords = keywords or PAIN_KEYWORDS

    print("=" * 60)
    print("PAIN POINT SCRAPER")
    print("=" * 60)

    # Validate environment variables
    if not os.getenv("REDDIT_CLIENT_ID") or not os.getenv("REDDIT_CLIENT_SECRET"):
        print("\n❌ Error: Reddit credentials not found!")
        print("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
        print("See .env.example for reference")
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Error: Anthropic API key not found!")
        print("Please set ANTHROPIC_API_KEY in .env file")
        return

    # Step 1: Scrape Reddit
    print("\n📥 Step 1: Scraping Reddit...")
    scraper = RedditScraper()
    posts = scraper.scrape_all_subreddits(
        subreddits=subreddits,
        keywords=keywords[:10],  # Limit keywords to avoid too many requests
        limit_per_subreddit=limit_per_subreddit
    )
    print(f"✅ Collected {len(posts)} posts")

    if not posts:
        print("\n⚠️ No posts found. Check your subreddits and keywords.")
        return

    # Step 2: Analyze with Claude
    print("\n🧠 Step 2: Analyzing with Claude...")
    classifier = PainClassifier()

    def progress(current, total):
        print(f"  Processing {current}/{total}...", end="\r")

    pains = classifier.classify_batch(posts, progress_callback=progress)
    print(f"\n✅ Identified {len(pains)} business pains")

    if not pains:
        print("\n⚠️ No business pains identified in the collected posts.")
        return

    # Step 3: Save to database
    print("\n💾 Step 3: Saving to database...")
    db = PainDatabase()

    saved = 0
    for pain in pains:
        if db.insert_pain(pain):
            saved += 1

    print(f"✅ Saved {saved} new pains to database")

    # Step 4: Summary
    print("\n📊 Summary by Industry:")
    for industry in db.get_industries_summary():
        avg_sev = industry['avg_severity']
        if avg_sev:
            print(f"  {industry['industry']}: {industry['count']} pains (avg severity: {avg_sev:.1f})")
        else:
            print(f"  {industry['industry']}: {industry['count']} pains")

    print("\n🔥 Top 5 Pains:")
    for pain in db.get_top_pains(limit=5):
        print(f"  [{pain['severity']}/10] {pain['pain_title']}")
        print(f"      → {pain['potential_product_idea']}")

    print("\n✅ Done! Run `streamlit run src/dashboard/app.py` to explore results.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape and analyze business pains")
    parser.add_argument("--limit", type=int, default=50, help="Posts per subreddit")
    parser.add_argument("--subreddits", nargs="+", help="Specific subreddits")
    args = parser.parse_args()

    scrape_and_analyze(
        subreddits=args.subreddits,
        limit_per_subreddit=args.limit
    )
