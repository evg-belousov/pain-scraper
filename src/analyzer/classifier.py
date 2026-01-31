# src/analyzer/classifier.py

import os
from openai import OpenAI
import json
from typing import Optional, Dict, List, Callable

from src.collectors.base import RawPainData
from src.analyzer.prompts import PAIN_CLASSIFICATION_PROMPT
from src.tracking.costs import CostTracker


class PainClassifier:
    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"  # Fast and cheap, use "gpt-4o" for better quality
        self.cost_tracker = cost_tracker

    def classify(self, data: RawPainData) -> Optional[Dict]:
        """Classify single item."""

        prompt = PAIN_CLASSIFICATION_PROMPT.format(
            source=data.source,
            title=data.title or "No title",
            content=data.content[:4000]
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            # Track cost
            if self.cost_tracker and response.usage:
                self.cost_tracker.track(
                    operation="classify",
                    model=self.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens
                )

            result_text = response.choices[0].message.content.strip()

            # Clean markdown
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1]
                result_text = result_text.rsplit("```", 1)[0]

            result = json.loads(result_text)

            # Add source metadata
            result["source"] = data.source
            result["source_url"] = data.source_url
            result["source_id"] = data.source_id
            result["original_score"] = data.score
            result["collected_at"] = data.collected_at.isoformat()

            return result

        except Exception as e:
            print(f"Classification error: {e}")
            return None

    def classify_batch(
        self,
        items: List[RawPainData],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """Classify batch."""

        results = []

        for i, item in enumerate(items):
            result = self.classify(item)

            if result and result.get("is_business_pain"):
                results.append(result)

            if progress_callback:
                progress_callback(i + 1, len(items))

        return results
