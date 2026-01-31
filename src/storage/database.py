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
