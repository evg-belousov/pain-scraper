# src/storage/models.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Pain:
    id: int
    source: str
    source_url: str
    source_id: str

    industry: str
    role: str

    pain_title: str
    pain_description: str

    severity: int
    frequency: str
    impact_type: str

    willingness_to_pay: str
    solvable_with_software: bool
    solvable_with_ai: bool
    solution_complexity: str

    potential_product: str
    key_quotes: List[str]
    tags: List[str]

    original_score: Optional[int]
    confidence: float

    collected_at: datetime
    created_at: datetime
