# src/collectors/hackernews.py

import httpx
from datetime import datetime
from typing import List, Optional

from src.collectors.base import BaseCollector, RawPainData
from src.config import HN_KEYWORDS, MIN_HN_SCORE


class HackerNewsCollector(BaseCollector):
    """Collect data from Hacker News via official API."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def get_source_name(self) -> str:
        return "hackernews"

    async def collect(self, limit: int = 100) -> List[RawPainData]:
        """Collect Ask HN posts and comments."""

        results = []

        # 1. Collect Ask HN stories
        ask_stories = await self._get_ask_stories(limit=limit)
        results.extend(ask_stories)

        # 2. Search by keywords via Algolia HN Search API
        for keyword in HN_KEYWORDS[:5]:  # Limit to avoid spamming
            keyword_results = await self._search_stories(keyword, limit=20)
            results.extend(keyword_results)

        # Remove duplicates
        seen_ids = set()
        unique_results = []
        for item in results:
            if item.source_id not in seen_ids:
                seen_ids.add(item.source_id)
                unique_results.append(item)

        return unique_results

    async def _get_ask_stories(self, limit: int = 100) -> List[RawPainData]:
        """Get Ask HN stories."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get list of IDs
            resp = await client.get(f"{self.BASE_URL}/askstories.json")
            story_ids = resp.json()[:limit]

            results = []
            for story_id in story_ids:
                story = await self._get_item(client, story_id)
                if story and self._is_relevant(story):
                    results.append(self._convert_story(story))

            return results

    async def _search_stories(self, query: str, limit: int = 20) -> List[RawPainData]:
        """Search via Algolia HN Search API."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "query": query,
                    "tags": "story",
                    "numericFilters": f"points>{MIN_HN_SCORE}",
                    "hitsPerPage": limit
                }
            )

            data = resp.json()
            results = []

            for hit in data.get("hits", []):
                results.append(RawPainData(
                    source="hackernews",
                    source_url=f"https://news.ycombinator.com/item?id={hit['objectID']}",
                    source_id=hit["objectID"],
                    title=hit.get("title"),
                    content=hit.get("story_text") or hit.get("title", ""),
                    author=hit.get("author"),
                    score=hit.get("points"),
                    comments_count=hit.get("num_comments"),
                    metadata={
                        "type": "story",
                        "created_at": hit.get("created_at"),
                    },
                    collected_at=datetime.utcnow()
                ))

            return results

    async def _get_item(self, client: httpx.AsyncClient, item_id: int) -> Optional[dict]:
        """Get single item by ID."""
        try:
            resp = await client.get(f"{self.BASE_URL}/item/{item_id}.json")
            return resp.json()
        except Exception:
            return None

    def _is_relevant(self, story: dict) -> bool:
        """Check post relevance."""
        if story.get("score", 0) < MIN_HN_SCORE:
            return False
        if story.get("deleted") or story.get("dead"):
            return False
        return True

    def _convert_story(self, story: dict) -> RawPainData:
        """Convert HN story to RawPainData."""
        return RawPainData(
            source="hackernews",
            source_url=f"https://news.ycombinator.com/item?id={story['id']}",
            source_id=str(story["id"]),
            title=story.get("title"),
            content=story.get("text") or story.get("title", ""),
            author=story.get("by"),
            score=story.get("score"),
            comments_count=len(story.get("kids", [])),
            metadata={
                "type": story.get("type"),
                "time": story.get("time"),
            },
            collected_at=datetime.utcnow()
        )
