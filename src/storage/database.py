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
        """Create tables if not exist."""

        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT UNIQUE,
                    post_url TEXT,
                    subreddit TEXT,

                    industry TEXT,
                    sub_industry TEXT,
                    role TEXT,

                    pain_title TEXT,
                    pain_description TEXT,

                    severity INTEGER,
                    frequency TEXT,
                    financial_impact TEXT,
                    time_impact TEXT,
                    emotional_intensity INTEGER,

                    willingness_to_pay TEXT,
                    solvable_with_software BOOLEAN,
                    solvable_with_ai BOOLEAN,
                    solution_complexity TEXT,

                    potential_product_idea TEXT,
                    key_quotes TEXT,  -- JSON array
                    tags TEXT,  -- JSON array

                    upvotes INTEGER,
                    num_comments INTEGER,
                    confidence REAL,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    post_created TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_industry ON pains(industry)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_severity ON pains(severity DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_wtp ON pains(willingness_to_pay)
            """)

            conn.commit()

    def insert_pain(self, pain_data: Dict) -> bool:
        """Insert a pain record."""

        with self._get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO pains (
                        post_id, post_url, subreddit,
                        industry, sub_industry, role,
                        pain_title, pain_description,
                        severity, frequency, financial_impact, time_impact, emotional_intensity,
                        willingness_to_pay, solvable_with_software, solvable_with_ai, solution_complexity,
                        potential_product_idea, key_quotes, tags,
                        upvotes, num_comments, confidence, post_created
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pain_data.get("post_id"),
                    pain_data.get("post_url"),
                    pain_data.get("subreddit"),
                    pain_data.get("industry"),
                    pain_data.get("sub_industry"),
                    pain_data.get("role"),
                    pain_data.get("pain_title"),
                    pain_data.get("pain_description"),
                    pain_data.get("severity"),
                    pain_data.get("frequency"),
                    pain_data.get("financial_impact"),
                    pain_data.get("time_impact"),
                    pain_data.get("emotional_intensity"),
                    pain_data.get("willingness_to_pay_signals"),
                    pain_data.get("solvable_with_software"),
                    pain_data.get("solvable_with_ai"),
                    pain_data.get("solution_complexity"),
                    pain_data.get("potential_product_idea"),
                    json.dumps(pain_data.get("key_quotes", [])),
                    json.dumps(pain_data.get("tags", [])),
                    pain_data.get("upvotes"),
                    pain_data.get("num_comments"),
                    pain_data.get("confidence"),
                    pain_data.get("post_created"),
                ))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting pain: {e}")
                return False

    def get_top_pains(
        self,
        industry: Optional[str] = None,
        min_severity: int = 5,
        limit: int = 50
    ) -> List[Dict]:
        """Get top pains sorted by score."""

        with self._get_connection() as conn:
            query = """
                SELECT *,
                    (severity * 2 + emotional_intensity + upvotes/10) as score
                FROM pains
                WHERE severity >= ?
            """
            params: List = [min_severity]

            if industry:
                query += " AND industry = ?"
                params.append(industry)

            query += " ORDER BY score DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            return [dict(row) for row in rows]

    def get_industries_summary(self) -> List[Dict]:
        """Get pain count by industry."""

        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT
                    industry,
                    COUNT(*) as count,
                    AVG(severity) as avg_severity,
                    SUM(CASE WHEN willingness_to_pay IN ('medium', 'high') THEN 1 ELSE 0 END) as high_wtp_count
                FROM pains
                GROUP BY industry
                ORDER BY count DESC
            """).fetchall()

            return [dict(row) for row in rows]

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

    def get_all_pains(self, limit: int = 1000) -> List[Dict]:
        """Get all pains from database."""

        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM pains
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    def get_pain_by_id(self, pain_id: int) -> Optional[Dict]:
        """Get a specific pain by ID."""

        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM pains WHERE id = ?
            """, (pain_id,)).fetchone()

            return dict(row) if row else None
