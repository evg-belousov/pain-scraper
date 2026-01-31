# src/tracking/progress.py

import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class RunProgress:
    run_id: int
    started_at: datetime

    # Counters by source
    source_counts: Dict[str, int] = field(default_factory=dict)

    # Total counters
    total_collected: int = 0
    total_new: int = 0
    total_analyzed: int = 0
    total_clusters: int = 0
    total_deep_analyses: int = 0

    # Errors
    errors: List[str] = field(default_factory=list)

    # Cost
    total_cost: float = 0.0


class ProgressTracker:
    """Track collection and analysis progress."""

    def __init__(self, db=None):
        self.db = db
        self._current_run: Optional[RunProgress] = None
        self._show_progress = True

    def set_db(self, db):
        """Set database instance."""
        self.db = db

    def start_run(self) -> int:
        """Start a new run."""
        run_id = 1
        if self.db:
            run_id = self.db.create_collection_run()

        self._current_run = RunProgress(
            run_id=run_id,
            started_at=datetime.now()
        )
        self._print(f"\n🚀 Run #{run_id} started\n")
        return run_id

    def finish_run(self, status: str = "completed"):
        """Finish the current run."""
        if not self._current_run:
            return

        if self.db:
            self.db.finish_collection_run(
                run_id=self._current_run.run_id,
                status=status,
                source_stats=self._current_run.source_counts,
                total_collected=self._current_run.total_collected,
                total_new=self._current_run.total_new,
                total_analyzed=self._current_run.total_analyzed,
                errors=self._current_run.errors
            )

        self._print_summary()
        self._current_run = None

    def get_run_id(self) -> Optional[int]:
        """Get current run ID."""
        if self._current_run:
            return self._current_run.run_id
        return None

    def increment_collected(self, source: str, count: int = 1, new: int = 1):
        """Increment collected records counter."""
        if not self._current_run:
            return

        self._current_run.source_counts[source] = (
            self._current_run.source_counts.get(source, 0) + count
        )
        self._current_run.total_collected += count
        self._current_run.total_new += new

        self._print_progress()

    def increment_analyzed(self, count: int = 1):
        """Increment analyzed records counter."""
        if not self._current_run:
            return

        self._current_run.total_analyzed += count
        self._print_progress()

    def increment_clusters(self, count: int = 1):
        """Increment clusters counter."""
        if not self._current_run:
            return

        self._current_run.total_clusters += count

    def increment_deep_analyses(self, count: int = 1):
        """Increment deep analyses counter."""
        if not self._current_run:
            return

        self._current_run.total_deep_analyses += count

    def add_cost(self, cost: float):
        """Add cost."""
        if not self._current_run:
            return

        self._current_run.total_cost += cost

    def add_error(self, error: str):
        """Record an error."""
        if not self._current_run:
            return

        self._current_run.errors.append(error)
        self._print(f"\n❌ Error: {error}")

    def set_show_progress(self, show: bool):
        """Enable/disable progress output."""
        self._show_progress = show

    def _print_progress(self):
        """Print current progress on one line."""
        if not self._show_progress or not self._current_run:
            return

        r = self._current_run
        sources_str = " | ".join(
            f"{s}: {c}" for s, c in r.source_counts.items()
        )

        # Overwrite the line
        sys.stdout.write(
            f"\r📊 Collected: {r.total_collected} (new: {r.total_new}) | "
            f"Analyzed: {r.total_analyzed} | "
            f"${r.total_cost:.4f} | "
            f"{sources_str}    "
        )
        sys.stdout.flush()

    def _print_summary(self):
        """Print final summary."""
        if not self._current_run:
            return

        r = self._current_run
        duration = datetime.now() - r.started_at

        self._print(f"\n\n{'='*60}")
        self._print(f"✅ Run #{r.run_id} completed in {duration}")
        self._print(f"{'='*60}")
        self._print(f"\n📥 Records collected: {r.total_collected}")
        self._print(f"   New (no duplicates): {r.total_new}")
        self._print(f"\n📊 By source:")

        for source, count in sorted(
            r.source_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            self._print(f"   • {source}: {count}")

        self._print(f"\n🔍 Analyzed: {r.total_analyzed}")
        self._print(f"📦 Clusters: {r.total_clusters}")
        self._print(f"🎯 Deep analyses: {r.total_deep_analyses}")
        self._print(f"\n💰 Total cost: ${r.total_cost:.4f}")

        if r.errors:
            self._print(f"\n⚠️ Errors: {len(r.errors)}")

        self._print(f"{'='*60}\n")

    def _print(self, text: str):
        """Print with newline."""
        if self._show_progress:
            print(text)
