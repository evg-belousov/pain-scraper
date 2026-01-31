# src/dedup.py

import argparse
import os
from dotenv import load_dotenv

from src.analyzer.deduplication import SmartDeduplicator
from src.storage.database import PainDatabase

# Load environment variables
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Manage pain deduplication")
    parser.add_argument(
        "--reprocess-all",
        action="store_true",
        help="Reprocess all pains for deduplication"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show deduplication statistics"
    )
    parser.add_argument(
        "--show-duplicates",
        type=int,
        default=0,
        help="Show top N pains with most duplicates"
    )

    args = parser.parse_args()

    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set in .env file")
        return

    db = PainDatabase()

    if args.stats or (not args.reprocess_all and args.show_duplicates == 0):
        # Show statistics
        stats = db.get_dedup_stats()

        print("\n" + "=" * 60)
        print("DEDUPLICATION STATISTICS")
        print("=" * 60)
        print(f"\n📊 Total records: {stats['total_count']}")
        print(f"✅ Unique pains: {stats['canonical_count']}")
        print(f"🔁 Duplicates: {stats['duplicate_count']}")
        print(f"🔗 Related pairs: {stats['related_count']}")
        print(f"📈 Duplicate ratio: {stats['duplicate_ratio']:.1%}")
        print("=" * 60 + "\n")

    if args.show_duplicates > 0:
        print("\n" + "=" * 60)
        print(f"TOP {args.show_duplicates} PAINS BY DUPLICATE COUNT")
        print("=" * 60)

        top_pains = db.get_top_canonical_by_duplicates(limit=args.show_duplicates)

        if not top_pains:
            print("\nNo duplicates found yet.")
        else:
            for pain in top_pains:
                print(f"\n[{pain['duplicate_count']}x] {pain['pain_title']}")
                print(f"   Industry: {pain['industry']} | Severity: {pain['severity']}")

                duplicates = db.get_duplicates_of(pain['id'])
                if duplicates:
                    print(f"   Duplicates:")
                    for dup in duplicates[:3]:
                        print(f"      - [{dup['source']}] {dup['pain_title'][:50]}...")
                    if len(duplicates) > 3:
                        print(f"      ... and {len(duplicates) - 3} more")

        print("\n" + "=" * 60)

    if args.reprocess_all:
        print("\n" + "=" * 60)
        print("REPROCESSING ALL PAINS FOR DEDUPLICATION")
        print("=" * 60)

        deduplicator = SmartDeduplicator()

        print("\nThis will:")
        print("  1. Create embeddings for all pains (if not cached)")
        print("  2. Find similar pains")
        print("  3. Mark duplicates and related pains")
        print("\nProcessing...")

        stats = deduplicator.reprocess_all(with_llm_verify=True)

        print(f"\n✅ Processed: {stats['processed']}")
        print(f"🔁 Duplicates found: {stats['duplicates']}")
        print(f"🔗 Related pairs: {stats['related']}")

        print("\n" + "=" * 60)
        print("Reprocessing complete.")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
