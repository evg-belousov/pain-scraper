# src/analyzer/clustering.py

import os
import json
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
import hdbscan
from sklearn.preprocessing import StandardScaler

from src.storage.database import PainDatabase
from src.tracking.costs import CostTracker


@dataclass
class Cluster:
    cluster_id: int
    name: str
    size: int
    pain_ids: List[int]
    avg_severity: float
    avg_wtp: str
    top_industries: List[str]
    sample_pains: List[str]
    opportunity_score: float


class PainClusterer:
    """Cluster similar pain points using embeddings and HDBSCAN."""

    def __init__(self, db_path: str = "data/pains.db"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"
        self.db = PainDatabase(db_path)
        self.cost_tracker = CostTracker(self.db)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for list of texts.
        Batching by 100 texts (API limit).
        """
        all_embeddings = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"   Getting embeddings {i+1}-{min(i+batch_size, len(texts))} of {len(texts)}...")

            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=batch
            )

            # Track embedding cost
            if response.usage:
                self.cost_tracker.track(
                    operation="embedding",
                    model=self.embedding_model,
                    prompt_tokens=response.usage.total_tokens,
                    completion_tokens=0
                )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def cluster(
        self,
        embeddings: np.ndarray,
        min_cluster_size: int = 3,
        min_samples: int = 2
    ) -> np.ndarray:
        """
        Cluster using HDBSCAN.

        Args:
            embeddings: matrix of embeddings (N x dim)
            min_cluster_size: minimum records for cluster
            min_samples: core density

        Returns:
            labels: array of cluster labels (-1 = outlier)
        """
        # Normalize
        scaler = StandardScaler()
        scaled = scaler.fit_transform(embeddings)

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean',
            cluster_selection_method='eom'
        )

        labels = clusterer.fit_predict(scaled)
        return labels

    def generate_cluster_name(self, pains_in_cluster: List[str], cluster_id: int = None) -> str:
        """
        Generate human-readable cluster name.
        Takes up to 5 examples and asks LLM to name the theme.
        """
        samples = pains_in_cluster[:5]
        samples_text = "\n---\n".join(samples)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""Here are several business problem descriptions from one cluster:

{samples_text}

Give a short name (3-6 words) for this cluster of problems.
Just the name, no explanation.

Examples of good names:
- "Invoice management difficulties"
- "Manual CRM data entry"
- "Meeting scheduling problems"
- "Tool integration issues"
- "Customer support bottlenecks"
"""
            }],
            max_tokens=50
        )

        # Track cost
        if response.usage:
            self.cost_tracker.track(
                operation="cluster_name",
                model="gpt-4o-mini",
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                cluster_id=cluster_id
            )

        return response.choices[0].message.content.strip().strip('"')

    def run_clustering(self, min_cluster_size: int = 3) -> List[Cluster]:
        """
        Full clustering pipeline.

        1. Load pains from DB
        2. Get embeddings
        3. Cluster
        4. Generate names
        5. Calculate metrics
        6. Save results
        """
        print("\n Step 1: Loading pains from database...")
        pains = self.db.get_all_pains()
        print(f"   Loaded {len(pains)} pains")

        if len(pains) < 10:
            print("   Not enough pains for clustering (need at least 10)")
            return []

        # Prepare texts
        texts = [self._prepare_text(p) for p in pains]

        print("\n Step 2: Getting embeddings...")
        embeddings = self.get_embeddings(texts)
        embeddings_array = np.array(embeddings)
        print(f"   Got {len(embeddings)} embeddings")

        print("\n Step 3: Clustering...")
        labels = self.cluster(embeddings_array, min_cluster_size=min_cluster_size)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_outliers = list(labels).count(-1)
        print(f"   Found {n_clusters} clusters, {n_outliers} outliers")

        print("\n Step 4: Grouping and analyzing clusters...")
        clusters_dict = self._group_by_cluster(pains, labels)

        print("\n Step 5: Generating cluster names...")
        result = []
        for cluster_id, cluster_pains in clusters_dict.items():
            if cluster_id == -1:  # Skip outliers
                continue

            print(f"   Naming cluster {cluster_id} ({len(cluster_pains)} pains)...")
            name = self.generate_cluster_name(
                [p.get("pain_description", p.get("pain_title", "")) for p in cluster_pains],
                cluster_id=cluster_id
            )

            cluster = Cluster(
                cluster_id=cluster_id,
                name=name,
                size=len(cluster_pains),
                pain_ids=[p["id"] for p in cluster_pains],
                avg_severity=self._calc_avg_severity(cluster_pains),
                avg_wtp=self._calc_avg_wtp_label(cluster_pains),
                top_industries=self._get_top_industries(cluster_pains),
                sample_pains=[p.get("pain_title", "")[:200] for p in cluster_pains[:3]],
                opportunity_score=self._calc_opportunity_score(cluster_pains)
            )
            result.append(cluster)

        # Sort by opportunity score
        result.sort(key=lambda c: c.opportunity_score, reverse=True)

        print("\n Step 6: Saving clusters to database...")
        self._save_clusters(result)

        return result

    def _prepare_text(self, pain: Dict) -> str:
        """Prepare text for embedding."""
        title = pain.get("pain_title", "")
        desc = pain.get("pain_description", "")
        return f"{title}. {desc}"[:1000]

    def _group_by_cluster(self, pains: List[Dict], labels: np.ndarray) -> Dict[int, List[Dict]]:
        """Group pains by cluster label."""
        clusters = {}
        for pain, label in zip(pains, labels):
            label = int(label)
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(pain)
        return clusters

    def _calc_avg_severity(self, pains: List[Dict]) -> float:
        """Calculate average severity."""
        severities = [p.get("severity", 5) for p in pains if p.get("severity")]
        return np.mean(severities) if severities else 5.0

    def _calc_avg_wtp_label(self, pains: List[Dict]) -> str:
        """Calculate average WTP as label."""
        wtp_map = {"none": 0, "low": 1, "medium": 2, "high": 3}
        reverse_map = {0: "none", 1: "low", 2: "medium", 3: "high"}

        wtps = [wtp_map.get(p.get("willingness_to_pay", "low"), 1) for p in pains]
        avg = np.mean(wtps) if wtps else 1
        return reverse_map.get(round(avg), "medium")

    def _calc_opportunity_score(self, pains: List[Dict]) -> float:
        """
        Opportunity Score = size * avg_severity * avg_wtp_numeric
        """
        wtp_map = {"none": 0.5, "low": 1, "medium": 2, "high": 3}

        avg_severity = self._calc_avg_severity(pains)
        wtps = [wtp_map.get(p.get("willingness_to_pay", "low"), 1) for p in pains]
        avg_wtp = np.mean(wtps) if wtps else 1
        size = len(pains)

        return size * avg_severity * avg_wtp

    def _get_top_industries(self, pains: List[Dict], top_n: int = 3) -> List[str]:
        """Get top industries in cluster."""
        industries = {}
        for p in pains:
            ind = p.get("industry", "other")
            industries[ind] = industries.get(ind, 0) + 1

        sorted_ind = sorted(industries.items(), key=lambda x: x[1], reverse=True)
        return [ind for ind, _ in sorted_ind[:top_n]]

    def _save_clusters(self, clusters: List[Cluster]):
        """Save clusters to database."""
        self.db.save_clusters(clusters)
