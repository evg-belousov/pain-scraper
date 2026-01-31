# src/tracking/costs.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Prices as of February 2026
MODEL_PRICES = {
    # GPT-4o
    "gpt-4o": {
        "prompt": 2.50 / 1_000_000,      # $2.50 per 1M tokens
        "completion": 10.00 / 1_000_000   # $10.00 per 1M tokens
    },
    # GPT-4o-mini
    "gpt-4o-mini": {
        "prompt": 0.15 / 1_000_000,       # $0.15 per 1M tokens
        "completion": 0.60 / 1_000_000    # $0.60 per 1M tokens
    },
    # Embeddings
    "text-embedding-3-small": {
        "prompt": 0.02 / 1_000_000,       # $0.02 per 1M tokens
        "completion": 0
    },
    "text-embedding-3-large": {
        "prompt": 0.13 / 1_000_000,
        "completion": 0
    }
}


@dataclass
class LLMUsage:
    operation: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    run_id: Optional[int] = None
    cluster_id: Optional[int] = None
    pain_id: Optional[int] = None


class CostTracker:
    """Track LLM API costs."""

    def __init__(self, db=None):
        self.db = db
        self._current_run_id: Optional[int] = None
        self._last_cost: float = 0.0

    def set_db(self, db):
        """Set database instance."""
        self.db = db

    def set_run_id(self, run_id: int):
        """Set current run for cost attribution."""
        self._current_run_id = run_id

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for a request."""
        prices = MODEL_PRICES.get(model, MODEL_PRICES["gpt-4o-mini"])

        cost = (
            prompt_tokens * prices["prompt"] +
            completion_tokens * prices["completion"]
        )
        return round(cost, 6)

    def track(
        self,
        operation: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cluster_id: Optional[int] = None,
        pain_id: Optional[int] = None
    ) -> LLMUsage:
        """
        Record LLM usage.

        Call after each OpenAI API request.
        """
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
        self._last_cost = cost

        usage = LLMUsage(
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            run_id=self._current_run_id,
            cluster_id=cluster_id,
            pain_id=pain_id
        )

        if self.db:
            self.db.save_llm_usage(usage)
            self._update_daily_stats(cost, model)

        return usage

    def get_last_cost(self) -> float:
        """Get cost of last tracked request."""
        return self._last_cost

    def _update_daily_stats(self, cost: float, model: str):
        """Update daily statistics."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.db:
            self.db.increment_daily_cost(today, cost, model)

    def get_run_cost(self, run_id: int) -> float:
        """Total cost for a run."""
        if self.db:
            return self.db.get_total_cost_by_run(run_id)
        return 0.0

    def get_today_cost(self) -> float:
        """Cost for today."""
        if self.db:
            today = datetime.now().strftime("%Y-%m-%d")
            return self.db.get_daily_cost(today)
        return 0.0

    def get_month_cost(self) -> float:
        """Cost for current month."""
        if self.db:
            month_start = datetime.now().strftime("%Y-%m-01")
            return self.db.get_cost_since(month_start)
        return 0.0
