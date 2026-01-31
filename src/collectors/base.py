# src/collectors/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class RawPainData:
    """Raw data from source."""
    source: str              # "hackernews", "indiehackers", "appstore", "youtube"
    source_url: str          # URL to original
    source_id: str           # Unique ID in source

    title: Optional[str]     # Title (if available)
    content: str             # Main text
    author: Optional[str]    # Author

    score: Optional[int]     # Upvotes, likes, rating
    comments_count: Optional[int]

    metadata: dict = field(default_factory=dict)  # Additional data
    collected_at: datetime = field(default_factory=datetime.utcnow)


class BaseCollector(ABC):
    """Base class for collectors."""

    @abstractmethod
    async def collect(self, limit: int = 100) -> List[RawPainData]:
        """Collect data from source."""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Source name."""
        pass
