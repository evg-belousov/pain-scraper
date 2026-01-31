# src/analyzer/prompts.py

PAIN_CLASSIFICATION_PROMPT = """Analyze this content and determine if it describes a real business pain point.

SOURCE: {source}
TITLE: {title}

CONTENT:
{content}

---

Analyze and return JSON:

{{
  "is_business_pain": true/false,
  "confidence": 0.0-1.0,

  "industry": "restaurant|cafe|dental|medical|real_estate|hvac|ecommerce|saas|agency|freelance|retail|accounting|legal|fitness|beauty|construction|logistics|education|other",

  "role": "owner|founder|manager|employee|freelancer|customer|other",

  "pain_title": "5-10 word summary of the pain",
  "pain_description": "2-3 sentence description",

  "severity": 1-10,
  "frequency": "daily|weekly|monthly|rare",

  "impact_type": "time|money|stress|growth|compliance|other",
  "estimated_impact": "description of time/money lost if mentioned",

  "existing_solutions_mentioned": ["solution1", "solution2"],
  "why_solutions_fail": "why existing solutions don't work",

  "willingness_to_pay": "none|low|medium|high",
  "willingness_evidence": "quote or signal",

  "solvable_with_software": true/false,
  "solvable_with_ai": true/false,
  "solution_complexity": "simple|medium|complex",

  "potential_product": "brief product idea",

  "key_quotes": ["exact relevant quote 1", "quote 2"],

  "tags": ["scheduling", "hiring", "inventory", "billing", "marketing", etc]
}}

If NOT a business pain, return:
{{
  "is_business_pain": false,
  "confidence": 0.0-1.0,
  "reason": "why this is not a business pain"
}}

Return ONLY valid JSON."""
