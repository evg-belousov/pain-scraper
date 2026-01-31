# src/analyzer/deep_analysis.py

import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
from openai import OpenAI

from src.storage.database import PainDatabase
from src.tracking.costs import CostTracker


class Verdict(Enum):
    GO = "go"
    MAYBE = "maybe"
    NO_GO = "no_go"


@dataclass
class Competitor:
    name: str
    price_range: str
    weakness: str


@dataclass
class DeepAnalysis:
    cluster_id: int

    # Competitors
    competitors: List[Dict[str, str]]
    why_still_painful: str

    # Target audience
    target_role: str
    target_company_size: str
    target_industries: List[str]
    market_size: str

    # Root cause
    root_cause: str
    solvable_with_software: bool

    # MVP
    mvp_description: str
    core_features: List[str]
    out_of_scope: List[str]

    # Customer acquisition
    where_to_find_customers: List[str]
    best_channel: str
    price_range: str

    # Risks
    risks: List[str]

    # Verdict
    attractiveness_score: int
    verdict: str
    main_argument: str

    # Meta
    analyzed_at: str
    model_used: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEEP_ANALYSIS_PROMPT = """You are an expert in product analytics and business idea validation.

Here is a cluster of business pains from various sources:

**Cluster Name:** {cluster_name}
**Number of mentions:** {cluster_size}
**Average severity (1-10):** {avg_severity}
**Sources:** {sources}

**Sample pains from this cluster:**
{sample_pains}

---

Analyze this cluster and respond in JSON format:

```json
{{
    "competitors": [
        {{"name": "Tool Name", "price_range": "$X-Y/mo", "weakness": "Why it doesn't fully solve the problem"}}
    ],
    "why_still_painful": "Why people still complain despite existing solutions",
    "target_role": "Specific role (e.g., 'Marketing Manager at SMB')",
    "target_company_size": "Company size (e.g., '10-50 employees')",
    "target_industries": ["industry1", "industry2"],
    "market_size": "small|medium|large",
    "root_cause": "Why this problem exists",
    "solvable_with_software": true,
    "mvp_description": "One paragraph describing minimum viable product",
    "core_features": ["feature1", "feature2", "feature3"],
    "out_of_scope": ["what NOT to build in v1"],
    "where_to_find_customers": ["channel1", "channel2"],
    "best_channel": "The single best channel to find first customers",
    "price_range": "Acceptable price range (e.g., '$29-99/mo')",
    "risks": ["risk1", "risk2", "risk3"],
    "attractiveness_score": 7,
    "verdict": "go|maybe|no_go",
    "main_argument": "The main reason for this verdict"
}}
```

Be specific and actionable. Don't use generic advice.
Return ONLY valid JSON, no markdown code blocks."""


class DeepAnalyzer:
    """Perform deep analysis on top clusters."""

    def __init__(self, db_path: str = "data/pains.db"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db = PainDatabase(db_path)
        self.cost_tracker = CostTracker(self.db)
        self.model = "gpt-4o"  # Need smart model for deep analysis

    def analyze_cluster(self, cluster_id: int) -> Optional[DeepAnalysis]:
        """Perform deep analysis on a single cluster."""

        # Get cluster data
        clusters = self.db.get_clusters(limit=1000)
        cluster = None
        for c in clusters:
            if c.get("id") == cluster_id:
                cluster = c
                break

        if not cluster:
            print(f"Cluster {cluster_id} not found")
            return None

        pains = self.db.get_pains_by_cluster(cluster_id)

        if not pains:
            print(f"No pains found for cluster {cluster_id}")
            return None

        # Prepare sample pains (up to 10 for context)
        sample_pains = self._format_sample_pains(pains[:10])

        # Format prompt
        prompt = DEEP_ANALYSIS_PROMPT.format(
            cluster_name=cluster.get("name", "Unknown"),
            cluster_size=cluster.get("size", len(pains)),
            avg_severity=cluster.get("avg_severity", 7),
            sources=self._get_sources_summary(pains),
            sample_pains=sample_pains
        )

        try:
            # LLM request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )

            # Track LLM cost
            if response.usage:
                self.cost_tracker.track(
                    operation="deep_analysis",
                    model=self.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    cluster_id=cluster_id
                )

            response_text = response.choices[0].message.content.strip()

            # Clean up potential markdown
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            # Parse response
            data = json.loads(response_text)

            analysis = DeepAnalysis(
                cluster_id=cluster_id,
                competitors=data.get("competitors", []),
                why_still_painful=data.get("why_still_painful", ""),
                target_role=data.get("target_role", ""),
                target_company_size=data.get("target_company_size", ""),
                target_industries=data.get("target_industries", []),
                market_size=data.get("market_size", "medium"),
                root_cause=data.get("root_cause", ""),
                solvable_with_software=data.get("solvable_with_software", True),
                mvp_description=data.get("mvp_description", ""),
                core_features=data.get("core_features", []),
                out_of_scope=data.get("out_of_scope", []),
                where_to_find_customers=data.get("where_to_find_customers", []),
                best_channel=data.get("best_channel", ""),
                price_range=data.get("price_range", ""),
                risks=data.get("risks", []),
                attractiveness_score=data.get("attractiveness_score", 5),
                verdict=data.get("verdict", "maybe"),
                main_argument=data.get("main_argument", ""),
                analyzed_at=datetime.utcnow().isoformat(),
                model_used=self.model
            )

            # Save to database
            self.db.save_deep_analysis(analysis)

            return analysis

        except json.JSONDecodeError as e:
            print(f"JSON parse error for cluster {cluster_id}: {e}")
            return None
        except Exception as e:
            print(f"Error analyzing cluster {cluster_id}: {e}")
            return None

    def analyze_top_clusters(
        self,
        top_n: int = 10,
        min_size: int = 5
    ) -> List[DeepAnalysis]:
        """Analyze top clusters that haven't been analyzed yet."""

        clusters = self.db.get_clusters(order_by="opportunity_score", limit=top_n)

        # Filter by size and not yet analyzed
        clusters = [c for c in clusters if c.get("size", 0) >= min_size]

        # Check which ones are already analyzed
        analyzed_ids = set(self.db.get_analyzed_cluster_ids())

        to_analyze = [c for c in clusters if c.get("id") not in analyzed_ids]

        if not to_analyze:
            print("All top clusters already analyzed.")
            return []

        print(f"Analyzing {len(to_analyze)} clusters...")

        results = []
        for cluster in to_analyze:
            cluster_id = cluster.get("id")
            cluster_name = cluster.get("name", "Unknown")
            print(f"\n   Analyzing: {cluster_name}...")

            analysis = self.analyze_cluster(cluster_id)
            if analysis:
                results.append(analysis)

        return results

    def _format_sample_pains(self, pains: List[Dict]) -> str:
        """Format sample pains for prompt."""
        formatted = []
        for i, pain in enumerate(pains, 1):
            source = pain.get("source", "unknown")
            title = pain.get("pain_title", "")
            desc = pain.get("pain_description", "")[:300]
            formatted.append(f"{i}. [{source}] {title}\n   {desc}")
        return "\n\n".join(formatted)

    def _get_sources_summary(self, pains: List[Dict]) -> str:
        """Get sources summary."""
        from collections import Counter
        sources = Counter(p.get("source", "unknown") for p in pains)
        return ", ".join(f"{s}: {c}" for s, c in sources.most_common())
