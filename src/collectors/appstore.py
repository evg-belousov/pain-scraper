# src/collectors/appstore.py

import httpx
from datetime import datetime
from typing import List

from src.collectors.base import BaseCollector, RawPainData
from src.config import APPS_TO_ANALYZE, MIN_REVIEW_LENGTH


class AppStoreCollector(BaseCollector):
    """Collect reviews from App Store."""

    def get_source_name(self) -> str:
        return "appstore"

    async def collect(self, limit: int = 100) -> List[RawPainData]:
        """Collect negative reviews (1-3 stars)."""

        results = []
        reviews_per_app = max(10, limit // len(APPS_TO_ANALYZE))

        async with httpx.AsyncClient(timeout=30.0) as client:
            for app in APPS_TO_ANALYZE:
                try:
                    reviews = await self._get_app_reviews(
                        client,
                        app["id"],
                        app["name"],
                        limit=reviews_per_app
                    )
                    results.extend(reviews)
                except Exception as e:
                    print(f"Error getting reviews for {app['name']}: {e}")
                    continue

        return results

    async def _get_app_reviews(
        self,
        client: httpx.AsyncClient,
        app_id: str,
        app_name: str,
        limit: int = 50
    ) -> List[RawPainData]:
        """Get reviews for single app."""

        # App Store RSS feed for reviews
        url = f"https://itunes.apple.com/us/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"

        try:
            resp = await client.get(url)
            data = resp.json()
        except Exception:
            return []

        results = []
        entries = data.get("feed", {}).get("entry", [])

        for entry in entries:
            if isinstance(entry, dict) and "content" in entry:
                rating = int(entry.get("im:rating", {}).get("label", "5"))
                content = entry.get("content", {}).get("label", "")
                title = entry.get("title", {}).get("label", "")

                # Only negative reviews (1-3 stars)
                if rating <= 3 and len(content) >= MIN_REVIEW_LENGTH:
                    results.append(RawPainData(
                        source="appstore",
                        source_url=f"https://apps.apple.com/app/id{app_id}",
                        source_id=entry.get("id", {}).get("label", ""),
                        title=f"{app_name}: {title}",
                        content=content,
                        author=entry.get("author", {}).get("name", {}).get("label"),
                        score=rating,
                        comments_count=None,
                        metadata={
                            "app_id": app_id,
                            "app_name": app_name,
                            "rating": rating,
                            "version": entry.get("im:version", {}).get("label"),
                        },
                        collected_at=datetime.utcnow()
                    ))

        return results[:limit]
