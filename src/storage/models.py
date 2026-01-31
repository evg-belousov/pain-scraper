# src/storage/models.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Pain:
    id: int
    post_id: str
    post_url: str
    subreddit: str

    industry: str
    sub_industry: Optional[str]
    role: str

    pain_title: str
    pain_description: str

    severity: int
    frequency: str
    financial_impact: str
    time_impact: str
    emotional_intensity: int

    willingness_to_pay: str
    solvable_with_software: bool
    solvable_with_ai: bool
    solution_complexity: str

    potential_product_idea: str
    key_quotes: List[str]
    tags: List[str]

    upvotes: int
    num_comments: int
    confidence: float

    created_at: datetime
    post_created: datetime
