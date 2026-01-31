# src/collectors/indiehackers.py

import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional

from src.collectors.base import BaseCollector, RawPainData


class IndieHackersCollector(BaseCollector):
    """Collect interviews from Indie Hackers."""

    BASE_URL = "https://www.indiehackers.com"

    def get_source_name(self) -> str:
        return "indiehackers"

    async def collect(self, limit: int = 100) -> List[RawPainData]:
        """Collect interviews."""

        results = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get interview list
            interviews = await self._get_interview_list(client, limit)

            for interview_url in interviews:
                try:
                    interview_data = await self._parse_interview(client, interview_url)
                    if interview_data:
                        results.append(interview_data)
                except Exception as e:
                    print(f"Error parsing {interview_url}: {e}")
                    continue

        return results

    async def _get_interview_list(self, client: httpx.AsyncClient, limit: int) -> List[str]:
        """Get list of interview URLs."""

        urls = []
        page = 1

        while len(urls) < limit:
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/interviews",
                    params={"page": page},
                    follow_redirects=True
                )

                soup = BeautifulSoup(resp.text, "html.parser")

                # Find interview links
                interview_links = soup.select("a[href*='/interview/']")

                if not interview_links:
                    break

                for link in interview_links:
                    href = link.get("href")
                    if href and "/interview/" in href:
                        full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                        if full_url not in urls:
                            urls.append(full_url)

                page += 1

                if page > 10:  # Page limit
                    break

            except Exception as e:
                print(f"Error getting interview list page {page}: {e}")
                break

        return urls[:limit]

    async def _parse_interview(self, client: httpx.AsyncClient, url: str) -> Optional[RawPainData]:
        """Parse single interview."""

        resp = await client.get(url, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Title
        title_elem = soup.select_one("h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Interview content
        content_elem = soup.select_one("article") or soup.select_one(".interview-content")
        content = content_elem.get_text(separator="\n", strip=True) if content_elem else ""

        if not content:
            return None

        # Author / company
        author_elem = soup.select_one(".founder-name") or soup.select_one("[class*='author']")
        author = author_elem.get_text(strip=True) if author_elem else None

        # Extract challenges section if exists
        challenges_section = self._extract_challenges(content)

        return RawPainData(
            source="indiehackers",
            source_url=url,
            source_id=url.split("/")[-1],
            title=title,
            content=challenges_section or content[:5000],
            author=author,
            score=None,
            comments_count=None,
            metadata={
                "full_content_length": len(content),
                "has_challenges_section": bool(challenges_section),
            },
            collected_at=datetime.utcnow()
        )

    def _extract_challenges(self, content: str) -> str:
        """Extract challenges/struggles section."""

        keywords = [
            "biggest challenge",
            "hardest part",
            "struggle",
            "obstacle",
            "what went wrong",
            "mistake",
            "difficult",
            "problem",
        ]

        lines = content.split("\n")
        relevant_lines = []
        capture = False
        capture_count = 0

        for line in lines:
            line_lower = line.lower()

            # Start capture if keyword found
            if any(kw in line_lower for kw in keywords):
                capture = True
                capture_count = 0

            if capture:
                relevant_lines.append(line)
                capture_count += 1

                # Capture 10 lines after keyword
                if capture_count > 10:
                    capture = False

        return "\n".join(relevant_lines) if relevant_lines else ""
