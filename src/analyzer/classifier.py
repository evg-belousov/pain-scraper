# src/analyzer/classifier.py

import anthropic
import json
from typing import Optional, Dict, List, Callable

from src.collectors.base import RawPainData
from src.analyzer.prompts import PAIN_CLASSIFICATION_PROMPT


class PainClassifier:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"

    def classify(self, data: RawPainData) -> Optional[Dict]:
        """Classify single item."""

        prompt = PAIN_CLASSIFICATION_PROMPT.format(
            source=data.source,
            title=data.title or "No title",
            content=data.content[:4000]
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text.strip()

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
