# src/scraper/keywords.py

"""
Additional keyword utilities for pain point discovery.
"""

from src.config import PAIN_KEYWORDS


def get_keywords_for_industry(industry: str) -> list[str]:
    """Get industry-specific keywords combined with general pain keywords."""

    industry_keywords = {
        "restaurant": [
            "reservation system",
            "food waste",
            "staff scheduling",
            "inventory management",
            "supplier",
            "menu pricing",
            "no-shows",
        ],
        "dental": [
            "patient scheduling",
            "insurance claims",
            "treatment plans",
            "patient retention",
            "dental software",
            "billing",
        ],
        "hvac": [
            "dispatch",
            "field service",
            "quoting",
            "parts inventory",
            "technician scheduling",
            "customer follow-up",
        ],
        "ecommerce": [
            "inventory sync",
            "shipping costs",
            "returns",
            "customer support",
            "product photos",
            "supplier management",
        ],
        "agency": [
            "client management",
            "project tracking",
            "time tracking",
            "invoicing",
            "scope creep",
            "client communication",
        ],
        "real_estate": [
            "lead management",
            "showing scheduling",
            "document signing",
            "CRM",
            "listing management",
            "commission tracking",
        ],
    }

    specific = industry_keywords.get(industry, [])
    return specific + PAIN_KEYWORDS[:10]  # Combine with top general keywords


def filter_keywords_by_context(keywords: list[str], context: str) -> list[str]:
    """Filter keywords to match specific context."""

    context_lower = context.lower()

    if "software" in context_lower or "tool" in context_lower:
        return [k for k in keywords if any(w in k for w in [
            "software", "tool", "app", "system", "platform"
        ])] or keywords[:5]

    if "time" in context_lower:
        return [k for k in keywords if any(w in k for w in [
            "time", "hours", "manual", "forever", "slow"
        ])] or keywords[:5]

    if "money" in context_lower or "cost" in context_lower:
        return [k for k in keywords if any(w in k for w in [
            "money", "cost", "expensive", "price", "budget"
        ])] or keywords[:5]

    return keywords
