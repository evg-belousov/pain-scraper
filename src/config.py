# src/config.py

SUBREDDITS = [
    # Small business general
    "smallbusiness",
    "Entrepreneur",
    "startups",

    # HoReCa
    "restaurateur",
    "Restaurant_Managers",
    "coffeeshops",
    "barista",
    "KitchenConfidential",

    # Medical
    "dentistry",
    "Dentists",
    "optometry",
    "veterinary",

    # Real estate
    "realtors",
    "PropertyManagement",

    # Services
    "HVAC",
    "Plumbing",
    "electricians",
    "AutoDetailing",
    "lawncare",

    # E-commerce
    "ecommerce",
    "FulfillmentByAmazon",
    "shopify",

    # Freelance and agencies
    "freelance",
    "agency",
    "web_design",
    "marketing",
]

PAIN_KEYWORDS = [
    # Explicit pain signals
    "nightmare",
    "frustrated",
    "frustrating",
    "hate",
    "worst part",
    "struggle with",
    "pain in the ass",
    "killing me",
    "drives me crazy",
    "waste time",
    "waste money",
    "losing money",
    "costs me",
    "expensive",

    # Looking for solutions
    "anyone else",
    "how do you handle",
    "is there a tool",
    "is there a way",
    "wish there was",
    "looking for",
    "need help with",
    "any recommendations",
    "what software",
    "what do you use for",

    # Time costs
    "hours every",
    "spend too much time",
    "takes forever",
    "manual process",
    "doing it manually",

    # Software complaints
    "too expensive",
    "overpriced",
    "too complicated",
    "doesn't work",
    "broken",
    "missing feature",
]

# Minimum thresholds
MIN_UPVOTES = 5
MIN_COMMENTS = 3
MAX_POST_AGE_DAYS = 90
