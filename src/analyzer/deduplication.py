# src/analyzer/deduplication.py

import numpy as np
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import os
from openai import OpenAI

from src.storage.database import PainDatabase
from src.tracking.costs import CostTracker


class RelationType(Enum):
    SAME = "same"           # >0.95 — exact duplicate
    RELATED = "related"     # 0.85-0.95 — similar topic
    DIFFERENT = "different" # <0.85 — different problems


# Similarity thresholds
THRESHOLD_SAME = 0.95      # Nearly identical
THRESHOLD_RELATED = 0.85   # Similar but possibly different


@dataclass
class SimilarityMatch:
    pain_id: int
    similarity: float
    relation_type: RelationType
    title: str
    content_preview: str


class Deduplicator:
    """Find and link similar pain points without deleting them."""

    def __init__(self, db_path: str = "data/pains.db"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db = PainDatabase(db_path)
        self.cost_tracker = CostTracker(self.db)
        self.embedding_model = "text-embedding-3-small"

    def process_new_pain(self, pain_id: int) -> Tuple[bool, List[SimilarityMatch]]:
        """
        Process a new record: find similar ones, determine relationships.

        Returns:
            (is_new_unique, similar_pains)
            - is_new_unique: True if this is a truly new unique pain
            - similar_pains: list of similar records with relation type
        """
        pain = self.db.get_pain_by_id(pain_id)
        if not pain:
            return True, []

        # 1. Get or create embedding
        embedding = self._get_or_create_embedding(pain)

        # 2. Find similar records
        similar = self._find_similar(pain_id, embedding, top_k=10)

        # 3. Determine relationships
        matches = []
        is_unique = True
        canonical_id = None

        for sim_pain_id, similarity in similar:
            relation = self._classify_relation(similarity)

            if relation == RelationType.SAME:
                is_unique = False
                # Find canonical ID (oldest record in group)
                sim_pain = self.db.get_pain_by_id(sim_pain_id)
                if sim_pain:
                    canonical_id = sim_pain.get("canonical_id") or sim_pain_id

            # Save relationship
            self.db.save_similarity(pain_id, sim_pain_id, similarity, relation.value)

            sim_pain = self.db.get_pain_by_id(sim_pain_id)
            if sim_pain:
                matches.append(SimilarityMatch(
                    pain_id=sim_pain_id,
                    similarity=similarity,
                    relation_type=relation,
                    title=sim_pain.get("pain_title", ""),
                    content_preview=sim_pain.get("pain_description", "")[:100]
                ))

        # 4. Update canonical_id if found duplicate
        if canonical_id:
            self.db.update_pain_dedup(pain_id,
                canonical_id=canonical_id,
                is_canonical=False
            )
            # Increment duplicate count for canonical record
            self.db.increment_duplicate_count(canonical_id)

        return is_unique, matches

    def _get_or_create_embedding(self, pain: Dict[str, Any]) -> np.ndarray:
        """Get embedding from cache or create new one."""
        if pain.get("embedding") is not None:
            return np.frombuffer(pain["embedding"], dtype=np.float32)

        # Create embedding
        text = self._prepare_text(pain)
        embedding = self._create_embedding(text)

        # Save to cache
        self.db.update_pain_embedding(
            pain["id"],
            embedding=embedding.tobytes(),
            embedding_model=self.embedding_model
        )

        return embedding

    def _prepare_text(self, pain: Dict[str, Any]) -> str:
        """
        Prepare text for embedding.

        Include context for better differentiation of similar pains.
        """
        parts = [
            pain.get("pain_title", ""),
            pain.get("pain_description", "")
        ]

        # Add industry and role if available — helps differentiate
        # "hard to hire" in restaurant vs in IT
        if pain.get("industry"):
            parts.append(f"Industry: {pain['industry']}")
        if pain.get("role"):
            parts.append(f"Role: {pain['role']}")

        return " | ".join(filter(None, parts))

    def _create_embedding(self, text: str) -> np.ndarray:
        """Request to OpenAI Embeddings API."""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text[:8000]  # Limit text length
        )

        # Track cost
        if response.usage:
            self.cost_tracker.track(
                operation="dedup_embedding",
                model=self.embedding_model,
                prompt_tokens=response.usage.total_tokens,
                completion_tokens=0
            )

        return np.array(response.data[0].embedding, dtype=np.float32)

    def _find_similar(
        self,
        pain_id: int,
        embedding: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Find similar records by cosine similarity.

        Returns list of (pain_id, similarity) sorted by descending similarity.
        """
        # Get all embeddings from database (except current record)
        all_pains = self.db.get_pains_with_embeddings(exclude_id=pain_id)

        if not all_pains:
            return []

        results = []
        for other_pain in all_pains:
            if other_pain.get("embedding") is None:
                continue

            other_emb = np.frombuffer(other_pain["embedding"], dtype=np.float32)
            similarity = self._cosine_similarity(embedding, other_emb)

            if similarity >= THRESHOLD_RELATED:  # Cutoff by minimum threshold
                results.append((other_pain["id"], similarity))

        # Sort by descending similarity
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _classify_relation(self, similarity: float) -> RelationType:
        """Classify relation type by similarity."""
        if similarity >= THRESHOLD_SAME:
            return RelationType.SAME
        elif similarity >= THRESHOLD_RELATED:
            return RelationType.RELATED
        else:
            return RelationType.DIFFERENT


class SmartDeduplicator(Deduplicator):
    """
    Extended deduplicator with LLM verification for borderline cases.

    For records with similarity 0.90-0.96 (gray zone), ask LLM:
    is this the same problem or different ones?
    """

    GRAY_ZONE_LOW = 0.90
    GRAY_ZONE_HIGH = 0.96

    def _is_gray_zone(self, similarity: float) -> bool:
        """Check if falls into gray zone."""
        return self.GRAY_ZONE_LOW <= similarity <= self.GRAY_ZONE_HIGH

    def verify_with_llm(
        self,
        pain1_id: int,
        pain2_id: int
    ) -> RelationType:
        """
        Ask LLM: is this one problem or different ones?

        Call only for borderline cases (gray zone).
        """
        pain1 = self.db.get_pain_by_id(pain1_id)
        pain2 = self.db.get_pain_by_id(pain2_id)

        if not pain1 or not pain2:
            return RelationType.DIFFERENT

        prompt = f"""Determine if these two records describe the SAME business problem or DIFFERENT problems.

**Record 1:**
Source: {pain1.get('source', 'unknown')}
Industry: {pain1.get('industry') or 'not specified'}
"{pain1.get('pain_title', '')}"
{pain1.get('pain_description', '')[:500]}

**Record 2:**
Source: {pain2.get('source', 'unknown')}
Industry: {pain2.get('industry') or 'not specified'}
"{pain2.get('pain_title', '')}"
{pain2.get('pain_description', '')[:500]}

---

Criteria for DIFFERENT problems (even if they sound similar):
- Different stages of a process (creating vs tracking vs paying)
- Different integrations (email vs calendar vs CRM)
- Different target markets (B2B vs B2C, enterprise vs SMB)
- Different roles (owner vs manager vs employee)
- Different industries with different specifics

Criteria for SAME problem:
- Same pain, just in different words
- One author complaining in different places
- General category without significant differences

Answer with ONE word:
- SAME — this is the same problem
- DIFFERENT — these are different problems
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )

        # Track cost
        if response.usage:
            self.cost_tracker.track(
                operation="dedup_verify",
                model="gpt-4o-mini",
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )

        answer = response.choices[0].message.content.strip().upper()

        if "SAME" in answer:
            return RelationType.SAME
        else:
            return RelationType.DIFFERENT

    def process_new_pain(self, pain_id: int) -> Tuple[bool, List[SimilarityMatch]]:
        """
        Process new record with LLM verification for gray zone.
        """
        pain = self.db.get_pain_by_id(pain_id)
        if not pain:
            return True, []

        embedding = self._get_or_create_embedding(pain)
        similar = self._find_similar(pain_id, embedding, top_k=10)

        matches = []
        is_unique = True
        canonical_id = None

        for sim_pain_id, similarity in similar:
            # Basic classification
            relation = self._classify_relation(similarity)

            # If gray zone — verify with LLM
            if self._is_gray_zone(similarity):
                relation = self.verify_with_llm(pain_id, sim_pain_id)

            if relation == RelationType.SAME:
                is_unique = False
                sim_pain = self.db.get_pain_by_id(sim_pain_id)
                if sim_pain:
                    canonical_id = sim_pain.get("canonical_id") or sim_pain_id

            self.db.save_similarity(pain_id, sim_pain_id, similarity, relation.value)

            sim_pain = self.db.get_pain_by_id(sim_pain_id)
            if sim_pain:
                matches.append(SimilarityMatch(
                    pain_id=sim_pain_id,
                    similarity=similarity,
                    relation_type=relation,
                    title=sim_pain.get("pain_title", ""),
                    content_preview=sim_pain.get("pain_description", "")[:100]
                ))

        if canonical_id:
            self.db.update_pain_dedup(pain_id,
                canonical_id=canonical_id,
                is_canonical=False
            )
            self.db.increment_duplicate_count(canonical_id)

        return is_unique, matches

    def reprocess_all(self, with_llm_verify: bool = False) -> Dict[str, int]:
        """
        Reprocess all pains for deduplication.

        Returns stats: {"processed": N, "duplicates": M, "related": K}
        """
        pains = self.db.get_all_pains()
        stats = {"processed": 0, "duplicates": 0, "related": 0}

        for pain in pains:
            is_unique, matches = self.process_new_pain(pain["id"])
            stats["processed"] += 1

            if not is_unique:
                stats["duplicates"] += 1

            for match in matches:
                if match.relation_type == RelationType.RELATED:
                    stats["related"] += 1

            if stats["processed"] % 50 == 0:
                print(f"   Processed {stats['processed']}/{len(pains)}...")

        return stats
