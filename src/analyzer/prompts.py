# src/analyzer/prompts.py

CLASSIFICATION_PROMPT = """Analyze this Reddit post and extract business pain points.

POST FROM r/{subreddit}:
Title: {title}

Body:
{body}

Top Comments:
{comments}

---

Analyze and return JSON:

{{
  "is_business_pain": true/false,
  "confidence": 0.0-1.0,

  "industry": "restaurant|cafe|dental|medical|real_estate|hvac|ecommerce|saas|agency|freelance|retail|other",
  "sub_industry": "more specific category if applicable",

  "role": "owner|manager|employee|customer|other",

  "pain_title": "Short 5-10 word summary of the pain",
  "pain_description": "2-3 sentence description of the problem",

  "severity": 1-10,
  "severity_reasoning": "Why this severity score",

  "frequency": "daily|weekly|monthly|quarterly|yearly|one-time",

  "financial_impact": "none|low|medium|high|critical",
  "financial_impact_estimate": "$X per month/year if mentioned",

  "time_impact": "none|low|medium|high|critical",
  "time_impact_estimate": "X hours per week if mentioned",

  "emotional_intensity": 1-10,
  "emotional_keywords": ["frustrated", "angry", etc],

  "existing_solutions_mentioned": ["solution1", "solution2"],
  "why_existing_solutions_fail": "explanation if mentioned",

  "willingness_to_pay_signals": "none|low|medium|high",
  "willingness_to_pay_evidence": "quotes or signals",

  "solvable_with_software": true/false,
  "solvable_with_ai": true/false,
  "solution_complexity": "simple|medium|complex",

  "potential_product_idea": "Brief product concept",
  "product_name_suggestion": "Catchy name idea",

  "key_quotes": ["exact quote 1", "exact quote 2"],

  "tags": ["scheduling", "inventory", "hiring", "billing", etc]
}}

If this is NOT a business pain (just a question, discussion, success story, etc), return:
{{
  "is_business_pain": false,
  "confidence": 0.0-1.0,
  "rejection_reason": "why this is not a business pain"
}}

Return ONLY valid JSON, no markdown."""
