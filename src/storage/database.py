# src/storage/database.py

import sqlite3
import json
import os
from typing import List, Dict, Optional
from contextlib import contextmanager


class PainDatabase:
    def __init__(self, db_path: str = "data/pains.db"):
        self.db_path = db_path
        self._ensure_data_dir()
        self._init_db()

    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    source_url TEXT,
                    source_id TEXT UNIQUE,

                    industry TEXT,
                    role TEXT,

                    pain_title TEXT,
                    pain_description TEXT,

                    severity INTEGER,
                    frequency TEXT,
                    impact_type TEXT,

                    willingness_to_pay TEXT,
                    solvable_with_software BOOLEAN,
                    solvable_with_ai BOOLEAN,
                    solution_complexity TEXT,

                    potential_product TEXT,
                    key_quotes TEXT,
                    tags TEXT,

                    original_score INTEGER,
                    confidence REAL,

                    collected_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_industry ON pains(industry)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_severity ON pains(severity DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON pains(source)")

            # Cluster tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clusters (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    avg_severity REAL,
                    avg_wtp TEXT,
                    top_industries TEXT,
                    sample_pains TEXT,
                    opportunity_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS pain_clusters (
                    pain_id INTEGER,
                    cluster_id INTEGER,
                    FOREIGN KEY (pain_id) REFERENCES pains(id),
                    FOREIGN KEY (cluster_id) REFERENCES clusters(id),
                    PRIMARY KEY (pain_id, cluster_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS deep_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cluster_id INTEGER UNIQUE,

                    competitors TEXT,
                    why_still_painful TEXT,

                    target_role TEXT,
                    target_company_size TEXT,
                    target_industries TEXT,
                    market_size TEXT,

                    root_cause TEXT,
                    solvable_with_software BOOLEAN,

                    mvp_description TEXT,
                    core_features TEXT,
                    out_of_scope TEXT,

                    where_to_find_customers TEXT,
                    best_channel TEXT,
                    price_range TEXT,

                    risks TEXT,

                    attractiveness_score INTEGER,
                    verdict TEXT,
                    main_argument TEXT,

                    model_used TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (cluster_id) REFERENCES clusters(id)
                )
            """)

            # Tracking tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collection_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP,
                    status TEXT DEFAULT 'running',

                    source_stats TEXT,
                    total_collected INTEGER DEFAULT 0,
                    total_new INTEGER DEFAULT 0,
                    total_analyzed INTEGER DEFAULT 0,

                    errors TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    operation TEXT,
                    model TEXT,

                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,

                    cost_usd REAL,

                    run_id INTEGER,
                    cluster_id INTEGER,
                    pain_id INTEGER,

                    FOREIGN KEY (run_id) REFERENCES collection_runs(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,

                    pains_collected INTEGER DEFAULT 0,
                    pains_analyzed INTEGER DEFAULT 0,
                    clusters_created INTEGER DEFAULT 0,
                    deep_analyses INTEGER DEFAULT 0,

                    total_cost_usd REAL DEFAULT 0,

                    cost_by_model TEXT
                )
            """)

            conn.commit()

    def insert_pain(self, pain_data: Dict) -> bool:
        with self._get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO pains (
                        source, source_url, source_id,
                        industry, role,
                        pain_title, pain_description,
                        severity, frequency, impact_type,
                        willingness_to_pay, solvable_with_software, solvable_with_ai, solution_complexity,
                        potential_product, key_quotes, tags,
                        original_score, confidence, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pain_data.get("source"),
                    pain_data.get("source_url"),
                    pain_data.get("source_id"),
                    pain_data.get("industry"),
                    pain_data.get("role"),
                    pain_data.get("pain_title"),
                    pain_data.get("pain_description"),
                    pain_data.get("severity"),
                    pain_data.get("frequency"),
                    pain_data.get("impact_type"),
                    pain_data.get("willingness_to_pay"),
                    pain_data.get("solvable_with_software"),
                    pain_data.get("solvable_with_ai"),
                    pain_data.get("solution_complexity"),
                    pain_data.get("potential_product"),
                    json.dumps(pain_data.get("key_quotes", [])),
                    json.dumps(pain_data.get("tags", [])),
                    pain_data.get("original_score"),
                    pain_data.get("confidence"),
                    pain_data.get("collected_at"),
                ))
                conn.commit()
                return True
            except Exception as e:
                print(f"Insert error: {e}")
                return False

    def get_top_pains(
        self,
        industry: Optional[str] = None,
        source: Optional[str] = None,
        min_severity: int = 5,
        limit: int = 50
    ) -> List[Dict]:
        with self._get_connection() as conn:
            query = """
                SELECT *,
                    (severity * 2 + COALESCE(original_score, 0) / 10 + confidence * 5) as score
                FROM pains
                WHERE severity >= ?
            """
            params: List = [min_severity]

            if industry:
                query += " AND industry = ?"
                params.append(industry)

            if source:
                query += " AND source = ?"
                params.append(source)

            query += " ORDER BY score DESC LIMIT ?"
            params.append(limit)

            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def get_summary(self) -> Dict:
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM pains").fetchone()[0]

            by_industry = conn.execute("""
                SELECT industry, COUNT(*) as count, AVG(severity) as avg_severity
                FROM pains GROUP BY industry ORDER BY count DESC
            """).fetchall()

            by_source = conn.execute("""
                SELECT source, COUNT(*) as count
                FROM pains GROUP BY source
            """).fetchall()

            return {
                "total": total,
                "by_industry": [dict(r) for r in by_industry],
                "by_source": [dict(r) for r in by_source],
            }

    def search_pains(self, query: str, limit: int = 20) -> List[Dict]:
        """Full-text search in pain titles and descriptions."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM pains
                WHERE pain_title LIKE ? OR pain_description LIKE ?
                ORDER BY severity DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit)).fetchall()

            return [dict(row) for row in rows]

    def get_all_pains(self, limit: int = 10000) -> List[Dict]:
        """Get all pains from database."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM pains
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]

    def save_clusters(self, clusters) -> bool:
        """Save clusters to database."""
        with self._get_connection() as conn:
            try:
                # Clear existing clusters
                conn.execute("DELETE FROM pain_clusters")
                conn.execute("DELETE FROM clusters")

                for cluster in clusters:
                    # Insert cluster
                    conn.execute("""
                        INSERT INTO clusters (
                            id, name, size, avg_severity, avg_wtp,
                            top_industries, sample_pains, opportunity_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cluster.cluster_id,
                        cluster.name,
                        cluster.size,
                        cluster.avg_severity,
                        cluster.avg_wtp,
                        json.dumps(cluster.top_industries),
                        json.dumps(cluster.sample_pains),
                        cluster.opportunity_score,
                    ))

                    # Insert pain-cluster mappings
                    for pain_id in cluster.pain_ids:
                        conn.execute("""
                            INSERT INTO pain_clusters (pain_id, cluster_id)
                            VALUES (?, ?)
                        """, (pain_id, cluster.cluster_id))

                conn.commit()
                return True
            except Exception as e:
                print(f"Error saving clusters: {e}")
                return False

    def get_clusters(self, order_by: str = "opportunity_score", limit: int = 100) -> List[Dict]:
        """Get all clusters."""
        with self._get_connection() as conn:
            rows = conn.execute(f"""
                SELECT * FROM clusters
                ORDER BY {order_by} DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]

    def get_pains_by_cluster(self, cluster_id: int) -> List[Dict]:
        """Get all pains in a cluster."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT p.* FROM pains p
                JOIN pain_clusters pc ON p.id = pc.pain_id
                WHERE pc.cluster_id = ?
                ORDER BY p.severity DESC
            """, (cluster_id,)).fetchall()
            return [dict(row) for row in rows]

    def save_deep_analysis(self, analysis) -> bool:
        """Save deep analysis to database."""
        with self._get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO deep_analyses (
                        cluster_id, competitors, why_still_painful,
                        target_role, target_company_size, target_industries, market_size,
                        root_cause, solvable_with_software,
                        mvp_description, core_features, out_of_scope,
                        where_to_find_customers, best_channel, price_range,
                        risks, attractiveness_score, verdict, main_argument,
                        model_used, analyzed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis.cluster_id,
                    json.dumps(analysis.competitors),
                    analysis.why_still_painful,
                    analysis.target_role,
                    analysis.target_company_size,
                    json.dumps(analysis.target_industries),
                    analysis.market_size,
                    analysis.root_cause,
                    analysis.solvable_with_software,
                    analysis.mvp_description,
                    json.dumps(analysis.core_features),
                    json.dumps(analysis.out_of_scope),
                    json.dumps(analysis.where_to_find_customers),
                    analysis.best_channel,
                    analysis.price_range,
                    json.dumps(analysis.risks),
                    analysis.attractiveness_score,
                    analysis.verdict,
                    analysis.main_argument,
                    analysis.model_used,
                    analysis.analyzed_at,
                ))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error saving deep analysis: {e}")
                return False

    def get_deep_analysis(self, cluster_id: int) -> Optional[Dict]:
        """Get deep analysis for a cluster."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM deep_analyses WHERE cluster_id = ?
            """, (cluster_id,)).fetchone()
            return dict(row) if row else None

    def get_analyzed_cluster_ids(self) -> List[int]:
        """Get list of cluster IDs that have been analyzed."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT cluster_id FROM deep_analyses
            """).fetchall()
            return [row[0] for row in rows]

    def get_all_deep_analyses(self, order_by: str = "attractiveness_score") -> List[Dict]:
        """Get all deep analyses."""
        with self._get_connection() as conn:
            rows = conn.execute(f"""
                SELECT da.*, c.name as cluster_name, c.size as cluster_size
                FROM deep_analyses da
                JOIN clusters c ON da.cluster_id = c.id
                ORDER BY da.{order_by} DESC
            """).fetchall()
            return [dict(row) for row in rows]

    # ==================== Tracking Methods ====================

    def create_collection_run(self) -> int:
        """Create a new collection run and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO collection_runs (status) VALUES ('running')
            """)
            conn.commit()
            return cursor.lastrowid

    def finish_collection_run(
        self,
        run_id: int,
        status: str,
        source_stats: Dict[str, int],
        total_collected: int,
        total_new: int,
        total_analyzed: int,
        errors: List[str]
    ):
        """Finish a collection run with results."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE collection_runs SET
                    finished_at = CURRENT_TIMESTAMP,
                    status = ?,
                    source_stats = ?,
                    total_collected = ?,
                    total_new = ?,
                    total_analyzed = ?,
                    errors = ?
                WHERE id = ?
            """, (
                status,
                json.dumps(source_stats),
                total_collected,
                total_new,
                total_analyzed,
                json.dumps(errors),
                run_id
            ))
            conn.commit()

    def get_recent_runs(self, limit: int = 10) -> List[Dict]:
        """Get recent collection runs."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT r.*,
                    COALESCE((SELECT SUM(cost_usd) FROM llm_costs WHERE run_id = r.id), 0) as cost
                FROM collection_runs r
                ORDER BY r.started_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

            results = []
            for row in rows:
                d = dict(row)
                # Parse JSON fields
                if d.get("source_stats"):
                    try:
                        d["source_stats"] = json.loads(d["source_stats"])
                    except:
                        d["source_stats"] = {}
                if d.get("errors"):
                    try:
                        d["errors"] = json.loads(d["errors"])
                    except:
                        d["errors"] = []
                results.append(d)

            return results

    def save_llm_usage(self, usage) -> bool:
        """Save LLM usage record."""
        with self._get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO llm_costs (
                        operation, model,
                        prompt_tokens, completion_tokens, total_tokens,
                        cost_usd, run_id, cluster_id, pain_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage.operation,
                    usage.model,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.prompt_tokens + usage.completion_tokens,
                    usage.cost_usd,
                    usage.run_id,
                    usage.cluster_id,
                    usage.pain_id
                ))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error saving LLM usage: {e}")
                return False

    def increment_daily_cost(self, date: str, cost: float, model: str):
        """Increment daily cost statistics."""
        with self._get_connection() as conn:
            # Get existing record
            row = conn.execute(
                "SELECT cost_by_model, total_cost_usd FROM daily_stats WHERE date = ?",
                (date,)
            ).fetchone()

            if row:
                # Update existing
                try:
                    cost_by_model = json.loads(row[0]) if row[0] else {}
                except:
                    cost_by_model = {}

                cost_by_model[model] = cost_by_model.get(model, 0) + cost
                total_cost = row[1] + cost

                conn.execute("""
                    UPDATE daily_stats SET
                        total_cost_usd = ?,
                        cost_by_model = ?
                    WHERE date = ?
                """, (total_cost, json.dumps(cost_by_model), date))
            else:
                # Create new
                cost_by_model = {model: cost}
                conn.execute("""
                    INSERT INTO daily_stats (date, total_cost_usd, cost_by_model)
                    VALUES (?, ?, ?)
                """, (date, cost, json.dumps(cost_by_model)))

            conn.commit()

    def increment_daily_stats(self, date: str, field: str, count: int = 1):
        """Increment a daily stats counter."""
        valid_fields = ["pains_collected", "pains_analyzed", "clusters_created", "deep_analyses"]
        if field not in valid_fields:
            return

        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM daily_stats WHERE date = ?", (date,)
            ).fetchone()

            if row:
                conn.execute(f"""
                    UPDATE daily_stats SET {field} = {field} + ?
                    WHERE date = ?
                """, (count, date))
            else:
                conn.execute(f"""
                    INSERT INTO daily_stats (date, {field})
                    VALUES (?, ?)
                """, (date, count))

            conn.commit()

    def get_daily_cost(self, date: str) -> float:
        """Get total cost for a specific date."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT total_cost_usd FROM daily_stats WHERE date = ?",
                (date,)
            ).fetchone()
            return row[0] if row else 0.0

    def get_cost_since(self, start_date: str) -> float:
        """Get total cost since a date."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT SUM(total_cost_usd) FROM daily_stats WHERE date >= ?",
                (start_date,)
            ).fetchone()
            return row[0] if row and row[0] else 0.0

    def get_total_cost_by_run(self, run_id: int) -> float:
        """Get total cost for a run."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT SUM(cost_usd) FROM llm_costs WHERE run_id = ?",
                (run_id,)
            ).fetchone()
            return row[0] if row and row[0] else 0.0

    def get_daily_costs(self, days: int = 30) -> List[Dict]:
        """Get daily costs for the last N days."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT date, total_cost_usd as cost, cost_by_model
                FROM daily_stats
                ORDER BY date DESC
                LIMIT ?
            """, (days,)).fetchall()

            results = []
            for row in rows:
                d = dict(row)
                if d.get("cost_by_model"):
                    try:
                        d["cost_by_model"] = json.loads(d["cost_by_model"])
                    except:
                        d["cost_by_model"] = {}
                results.append(d)

            return list(reversed(results))

    def get_costs_by_operation(self) -> Dict[str, float]:
        """Get total costs grouped by operation."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT operation, SUM(cost_usd) as total
                FROM llm_costs
                GROUP BY operation
                ORDER BY total DESC
            """).fetchall()
            return {row[0]: row[1] for row in rows}

    def get_costs_by_model(self) -> Dict[str, float]:
        """Get total costs grouped by model."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT model, SUM(cost_usd) as total
                FROM llm_costs
                GROUP BY model
                ORDER BY total DESC
            """).fetchall()
            return {row[0]: row[1] for row in rows}

    def get_pain_counts_by_source(self) -> Dict[str, int]:
        """Get pain counts grouped by source."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT source, COUNT(*) as count
                FROM pains
                GROUP BY source
                ORDER BY count DESC
            """).fetchall()
            return {row[0]: row[1] for row in rows}

    def count_pains(self) -> int:
        """Get total pain count."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM pains").fetchone()
            return row[0] if row else 0

    def count_clusters(self) -> int:
        """Get total cluster count."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM clusters").fetchone()
            return row[0] if row else 0

    def count_deep_analyses(self) -> int:
        """Get total deep analyses count."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM deep_analyses").fetchone()
            return row[0] if row else 0
