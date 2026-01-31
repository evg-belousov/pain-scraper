# src/analyzer/incremental_clustering.py

from typing import List, Optional, Dict
import numpy as np
from datetime import datetime

from src.storage.database import PainDatabase


class IncrementalClusterer:
    """
    Add new records to existing clusters without full recalculation.
    """

    CLUSTER_ASSIGNMENT_THRESHOLD = 0.75  # Minimum similarity with centroid

    def __init__(self, db_path: str = "data/pains.db"):
        self.db = PainDatabase(db_path)

    def assign_to_cluster(self, pain_id: int) -> Optional[int]:
        """
        Try to add record to existing cluster.

        Returns:
            cluster_id if added, None if no cluster matched
        """
        pain = self.db.get_pain_by_id(pain_id)

        if not pain or pain.get("embedding") is None:
            return None

        embedding = np.frombuffer(pain["embedding"], dtype=np.float32)

        # Get centroids of all clusters
        clusters = self.db.get_clusters_with_centroids()

        best_cluster = None
        best_similarity = 0

        for cluster in clusters:
            if cluster.get("centroid") is None:
                continue

            centroid = np.frombuffer(cluster["centroid"], dtype=np.float32)
            similarity = self._cosine_similarity(embedding, centroid)

            if similarity > best_similarity:
                best_similarity = similarity
                best_cluster = cluster

        # Check threshold
        if best_similarity >= self.CLUSTER_ASSIGNMENT_THRESHOLD and best_cluster:
            self.db.add_pain_to_cluster(pain_id, best_cluster["id"])
            self._update_centroid(best_cluster["id"])
            return best_cluster["id"]

        return None

    def _update_centroid(self, cluster_id: int):
        """Recalculate cluster centroid after adding a record."""
        pains = self.db.get_pains_by_cluster(cluster_id)

        embeddings = []
        for pain in pains:
            emb_data = self.db.get_pain_embedding(pain["id"])
            if emb_data:
                emb = np.frombuffer(emb_data, dtype=np.float32)
                embeddings.append(emb)

        if embeddings:
            centroid = np.mean(embeddings, axis=0).astype(np.float32)
            self.db.update_cluster_centroid(cluster_id, centroid.tobytes())

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def process_unclustered(self) -> Dict[str, int]:
        """
        Process all records without a cluster.

        Returns:
            {"assigned": N, "orphaned": M}
        """
        unclustered = self.db.get_unclustered_pains()

        assigned = 0
        orphaned = 0

        for pain in unclustered:
            cluster_id = self.assign_to_cluster(pain["id"])
            if cluster_id:
                assigned += 1
                print(f"   Pain #{pain['id']} -> Cluster #{cluster_id}")
            else:
                orphaned += 1

        return {"assigned": assigned, "orphaned": orphaned}

    def should_full_recluster(self) -> bool:
        """
        Determine if full cluster recalculation is needed.

        Criteria:
        - More than 30% of records without cluster
        - More than 7 days since last full clustering
        - More than 500 new records added
        """
        stats = self.db.get_clustering_stats()

        if stats["total"] == 0:
            return True

        orphan_ratio = stats["unclustered"] / max(stats["total"], 1)

        return (
            orphan_ratio > 0.3 or
            stats.get("days_since_full_clustering", 999) > 7 or
            stats.get("new_since_clustering", 0) > 500
        )

    def compute_all_centroids(self):
        """Compute centroids for all clusters based on their pains."""
        clusters = self.db.get_clusters()

        for cluster in clusters:
            cluster_id = cluster["id"]
            pains = self.db.get_pains_by_cluster(cluster_id)

            embeddings = []
            for pain in pains:
                emb_data = self.db.get_pain_embedding(pain["id"])
                if emb_data:
                    emb = np.frombuffer(emb_data, dtype=np.float32)
                    embeddings.append(emb)

            if embeddings:
                centroid = np.mean(embeddings, axis=0).astype(np.float32)
                self.db.update_cluster_centroid(cluster_id, centroid.tobytes())
                print(f"   Computed centroid for cluster #{cluster_id} ({len(embeddings)} pains)")
