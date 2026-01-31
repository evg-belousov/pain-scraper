# src/collectors/stackexchange.py

import httpx
import asyncio
from datetime import datetime
from typing import List

from src.collectors.base import BaseCollector, RawPainData
from src.config import SE_SITES, SE_TAGS, MIN_SE_SCORE


class StackExchangeCollector(BaseCollector):
    """
    Collect pain points from Stack Exchange sites.

    Targets:
    - Software Recommendations - people describe problems and look for solutions
    - Super User - software-related issues
    - Web Applications - SaaS problems
    """

    BASE_URL = "https://api.stackexchange.com/2.3"

    def get_source_name(self) -> str:
        return "stackexchange"

    async def collect(self, limit: int = 100) -> List[RawPainData]:
        """
        Collect questions from target Stack Exchange sites.

        Logic:
        1. For each site
        2. For each tag (if specified)
        3. Fetch questions via API
        4. Filter by score
        5. Convert to RawPainData
        """

        results = []
        seen_ids = set()
        questions_per_site = max(20, limit // len(SE_SITES))

        async with httpx.AsyncClient(timeout=30.0) as client:
            for site in SE_SITES:
                site_name = site["name"]
                site_tags = site.get("tags", [])

                if site_tags:
                    # Fetch by tags
                    for tag in site_tags[:3]:  # Limit tags
                        try:
                            questions = await self._fetch_questions(
                                client,
                                site_name,
                                tag=tag,
                                limit=questions_per_site // len(site_tags[:3])
                            )

                            for q in questions:
                                if q["question_id"] not in seen_ids:
                                    if q.get("score", 0) >= MIN_SE_SCORE:
                                        seen_ids.add(q["question_id"])
                                        results.append(self._to_raw_pain(q, site_name))

                            await asyncio.sleep(0.5)  # Rate limiting

                        except Exception as e:
                            print(f"Error fetching {site_name}/{tag}: {e}")
                            continue
                else:
                    # Fetch top questions
                    try:
                        questions = await self._fetch_questions(
                            client,
                            site_name,
                            limit=questions_per_site
                        )

                        for q in questions:
                            if q["question_id"] not in seen_ids:
                                if q.get("score", 0) >= MIN_SE_SCORE:
                                    seen_ids.add(q["question_id"])
                                    results.append(self._to_raw_pain(q, site_name))

                    except Exception as e:
                        print(f"Error fetching {site_name}: {e}")
                        continue

                if len(results) >= limit:
                    break

        return results[:limit]

    async def _fetch_questions(
        self,
        client: httpx.AsyncClient,
        site: str,
        tag: str = None,
        limit: int = 30
    ) -> List[dict]:
        """Fetch questions from Stack Exchange API."""

        params = {
            "order": "desc",
            "sort": "votes",
            "site": site,
            "pagesize": min(limit, 100),
            "filter": "withbody",  # Include question body
        }

        if tag:
            params["tagged"] = tag

        try:
            resp = await client.get(f"{self.BASE_URL}/questions", params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("items", [])
        except Exception as e:
            print(f"Stack Exchange API error: {e}")
            return []

    def _to_raw_pain(self, question: dict, site: str) -> RawPainData:
        """Convert Stack Exchange question to RawPainData."""

        # Clean HTML from body
        body = question.get("body", "")
        # Simple HTML tag removal
        import re
        body = re.sub(r'<[^>]+>', ' ', body)
        body = re.sub(r'\s+', ' ', body).strip()

        created_utc = question.get("creation_date", 0)
        if created_utc:
            collected_at = datetime.utcfromtimestamp(created_utc)
        else:
            collected_at = datetime.utcnow()

        tags = question.get("tags", [])

        return RawPainData(
            source="stackexchange",
            source_url=question.get("link", ""),
            source_id=f"{site}_{question.get('question_id', '')}",
            title=question.get("title", ""),
            content=body[:5000],
            author=question.get("owner", {}).get("display_name", "[anonymous]"),
            score=question.get("score"),
            comments_count=question.get("answer_count"),
            metadata={
                "site": site,
                "tags": tags,
                "view_count": question.get("view_count"),
                "answer_count": question.get("answer_count"),
                "is_answered": question.get("is_answered"),
                "created_utc": created_utc,
            },
            collected_at=collected_at
        )
