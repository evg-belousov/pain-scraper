# src/config.py

# Hacker News
HN_KEYWORDS = [
    "Ask HN",
    "frustrated",
    "struggling",
    "problem",
    "hate",
    "nightmare",
    "waste time",
    "anyone else",
    "how do you handle",
    "looking for tool",
    "wish there was",
]

HN_STORY_TYPES = [
    "ask",      # Ask HN posts
    "show",     # Show HN (comments have feedback)
]

# Indie Hackers - interview categories
IH_CATEGORIES = [
    "podcast",
    "interview",
]

# App Store - business apps to analyze reviews
APPS_TO_ANALYZE = [
    # Restaurants / HoReCa
    {"name": "Toast POS", "id": "1111252754", "platform": "ios"},
    {"name": "Square POS", "id": "335393788", "platform": "ios"},
    {"name": "7shifts", "id": "1073041402", "platform": "ios"},

    # Small business
    {"name": "QuickBooks", "id": "584947037", "platform": "ios"},
    {"name": "Wave Invoicing", "id": "881670290", "platform": "ios"},
    {"name": "Jobber", "id": "620098427", "platform": "ios"},

    # CRM / Sales
    {"name": "HubSpot", "id": "1107711722", "platform": "ios"},
    {"name": "Pipedrive", "id": "597826306", "platform": "ios"},

    # Scheduling
    {"name": "Calendly", "id": "1451094657", "platform": "ios"},
    {"name": "Acuity Scheduling", "id": "1179447119", "platform": "ios"},
]

# YouTube - channels and search queries
YOUTUBE_SEARCHES = [
    "restaurant owner biggest mistake",
    "small business owner struggles",
    "why I closed my business",
    "coffee shop owner problems",
    "freelancer biggest challenge",
    "startup founder lessons learned",
    "dental practice management problems",
    "real estate agent struggles",
]

# Reddit - subreddits and keywords for Pullpush API
REDDIT_SUBREDDITS = [
    # Business
    "smallbusiness",
    "Entrepreneur",
    "startups",
    "ecommerce",

    # SaaS / Tech
    "SaaS",
    "microsaas",
    "indiehackers",
    "webdev",

    # Professions
    "freelance",
    "consulting",
    "realtors",
    "accounting",
    "restaurateur",

    # Productivity
    "productivity",
    "automation",
]

REDDIT_PAIN_KEYWORDS = [
    "frustrated",
    "annoying",
    "waste time",
    "manual process",
    "looking for",
    "anyone know",
    "is there a tool",
    "I wish",
    "hate when",
    "struggle with",
    "tedious",
    "nightmare",
    "pain in the ass",
    "so slow",
    "broken",
]

# Minimum thresholds
MIN_HN_SCORE = 10
MIN_REVIEW_LENGTH = 100
MIN_YOUTUBE_LIKES = 50
MIN_REDDIT_SCORE = 5
