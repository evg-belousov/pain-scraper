# src/collectors/youtube.py

import os
import httpx
from datetime import datetime
from typing import List

from src.collectors.base import BaseCollector, RawPainData
from src.config import YOUTUBE_SEARCHES, MIN_YOUTUBE_LIKES


class YouTubeCollector(BaseCollector):
    """Collect comments from YouTube."""

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY not set")

    def get_source_name(self) -> str:
        return "youtube"

    async def collect(self, limit: int = 100) -> List[RawPainData]:
        """Collect comments from relevant videos."""

        results = []
        videos_per_search = 5
        comments_per_video = max(10, limit // (len(YOUTUBE_SEARCHES) * videos_per_search))

        async with httpx.AsyncClient(timeout=30.0) as client:
            for search_query in YOUTUBE_SEARCHES:
                try:
                    # Find videos
                    videos = await self._search_videos(client, search_query, limit=videos_per_search)

                    # Collect comments
                    for video in videos:
                        comments = await self._get_video_comments(
                            client,
                            video["id"],
                            video["title"],
                            limit=comments_per_video
                        )
                        results.extend(comments)

                except Exception as e:
                    print(f"Error searching YouTube for '{search_query}': {e}")
                    continue

        return results

    async def _search_videos(
        self,
        client: httpx.AsyncClient,
        query: str,
        limit: int = 5
    ) -> List[dict]:
        """Search videos by query."""

        resp = await client.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": limit,
                "order": "relevance",
                "key": self.api_key,
            }
        )

        data = resp.json()
        videos = []

        for item in data.get("items", []):
            videos.append({
                "id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
            })

        return videos

    async def _get_video_comments(
        self,
        client: httpx.AsyncClient,
        video_id: str,
        video_title: str,
        limit: int = 20
    ) -> List[RawPainData]:
        """Get comments for video."""

        resp = await client.get(
            "https://www.googleapis.com/youtube/v3/commentThreads",
            params={
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(limit, 100),
                "order": "relevance",
                "key": self.api_key,
            }
        )

        data = resp.json()
        results = []

        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            likes = snippet.get("likeCount", 0)

            # Filter by likes
            if likes >= MIN_YOUTUBE_LIKES:
                results.append(RawPainData(
                    source="youtube",
                    source_url=f"https://www.youtube.com/watch?v={video_id}",
                    source_id=item["id"],
                    title=f"Comment on: {video_title}",
                    content=snippet.get("textDisplay", ""),
                    author=snippet.get("authorDisplayName"),
                    score=likes,
                    comments_count=item["snippet"].get("totalReplyCount", 0),
                    metadata={
                        "video_id": video_id,
                        "video_title": video_title,
                        "like_count": likes,
                    },
                    collected_at=datetime.utcnow()
                ))

        return results
