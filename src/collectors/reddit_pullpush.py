# src/collectors/reddit_pullpush.py

import httpx
import asyncio
from datetime import datetime
from typing import List

from src.collectors.base import BaseCollector, RawPainData
from src.config import REDDIT_SUBREDDITS, REDDIT_PAIN_KEYWORDS, MIN_REDDIT_SCORE


class RedditPullpushCollector(BaseCollector):
    """Collect pain points from Reddit via Pullpush API."""

    BASE_URL = "https://api.pullpush.io/reddit"

    def get_source_name(self) -> str:
        return "reddit"

    async def collect(self, limit: int = 100) -> List[RawPainData]:
        """
        Collect posts from target subreddits.

        Logic:
        1. For each subreddit
        2. For each keyword
        3. Fetch posts via API
        4. Filter by minimum score
        5. Convert to RawPainData
        6. Deduplicate by source_id
        """

        results = []
        seen_ids = set()

        # Calculate limits per subreddit/keyword combo
        num_subreddits = len(REDDIT_SUBREDDITS)
        num_keywords = min(5, len(REDDIT_PAIN_KEYWORDS))  # Limit keywords to avoid too many requests
        posts_per_query = max(10, limit // (num_subreddits * num_keywords))

        async with httpx.AsyncClient(timeout=30.0) as client:
            for subreddit in REDDIT_SUBREDDITS:
                for keyword in REDDIT_PAIN_KEYWORDS[:num_keywords]:
                    try:
                        submissions = await self._fetch_submissions(
                            client,
                            subreddit,
                            keyword,
                            limit=posts_per_query
                        )

                        for sub in submissions:
                            # Skip if already seen
                            if sub.get("id") in seen_ids:
                                continue

                            # Skip low score posts
                            if sub.get("score", 0) < MIN_REDDIT_SCORE:
                                continue

                            # Skip posts with no content
                            if not sub.get("selftext") or sub.get("selftext") == "[removed]":
                                continue

                            seen_ids.add(sub["id"])
                            results.append(self._to_raw_pain(sub))

                        # Rate limiting - pause between requests
                        await asyncio.sleep(1.0)

                    except Exception as e:
                        print(f"Error fetching r/{subreddit} '{keyword}': {e}")
                        continue

                    # Check if we have enough
                    if len(results) >= limit:
                        return results[:limit]

        return results

    async def _fetch_submissions(
        self,
        client: httpx.AsyncClient,
        subreddit: str,
        query: str,
        limit: int = 100
    ) -> List[dict]:
        """Fetch submissions from Pullpush API."""

        url = f"{self.BASE_URL}/search/submission/"

        params = {
            "subreddit": subreddit,
            "q": query,
            "size": min(limit, 100),  # API max is 100
            "sort": "desc",
            "sort_type": "score",
        }

        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except httpx.HTTPStatusError as e:
            print(f"HTTP error {e.response.status_code} for r/{subreddit}")
            return []
        except Exception as e:
            print(f"Request error for r/{subreddit}: {e}")
            return []

    def _to_raw_pain(self, submission: dict) -> RawPainData:
        """Convert Reddit submission to RawPainData."""

        # Build permalink URL
        permalink = submission.get("permalink", "")
        if permalink:
            source_url = f"https://reddit.com{permalink}"
        else:
            source_url = f"https://reddit.com/r/{submission.get('subreddit')}/comments/{submission.get('id')}"

        # Get created timestamp
        created_utc = submission.get("created_utc", 0)
        if created_utc:
            collected_at = datetime.utcfromtimestamp(created_utc)
        else:
            collected_at = datetime.utcnow()

        return RawPainData(
            source="reddit",
            source_url=source_url,
            source_id=submission.get("id", ""),
            title=submission.get("title", ""),
            content=submission.get("selftext", "")[:5000],  # Limit content size
            author=submission.get("author", "[deleted]"),
            score=submission.get("score"),
            comments_count=submission.get("num_comments"),
            metadata={
                "subreddit": submission.get("subreddit"),
                "score": submission.get("score"),
                "num_comments": submission.get("num_comments"),
                "upvote_ratio": submission.get("upvote_ratio"),
                "created_utc": created_utc,
            },
            collected_at=collected_at
        )
