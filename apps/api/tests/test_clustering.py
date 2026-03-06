"""Unit tests for ClusteringService."""

import numpy as np
import pytest

from apps.api.services.clustering import ClusterResult, ClusteringService


@pytest.fixture(scope="module")
def service():
    return ClusteringService()


def _synthetic_embeddings(n: int = 40, dim: int = 384, seed: int = 42):
    """Generate reproducible random embeddings."""
    rng = np.random.default_rng(seed)
    return rng.random((n, dim)).tolist()


def _synthetic_texts(n: int = 40):
    return [f"Sample feedback item number {i}" for i in range(n)]


def test_cluster_embeddings_returns_list(service):
    """cluster_embeddings returns a non-empty list of ClusterResult."""
    embeddings = _synthetic_embeddings()
    texts = _synthetic_texts()
    results = service.cluster_embeddings(embeddings, texts, min_cluster_size=3, min_samples=2)
    assert isinstance(results, list)
    assert len(results) > 0


def test_cluster_excludes_noise(service):
    """HDBSCAN noise cluster (-1) is never returned."""
    embeddings = _synthetic_embeddings()
    texts = _synthetic_texts()
    results = service.cluster_embeddings(embeddings, texts, min_cluster_size=3, min_samples=2)
    cluster_ids = [r.cluster_id for r in results]
    assert -1 not in cluster_ids


def test_cluster_result_fields(service):
    """Every ClusterResult has the required fields with correct types."""
    embeddings = _synthetic_embeddings()
    texts = _synthetic_texts()
    results = service.cluster_embeddings(embeddings, texts, min_cluster_size=3, min_samples=2)
    for r in results:
        assert isinstance(r, ClusterResult)
        assert isinstance(r.cluster_id, int)
        assert isinstance(r.label, str) and r.label
        assert isinstance(r.centroid, list) and len(r.centroid) > 0
        assert isinstance(r.member_indices, list) and len(r.member_indices) > 0
        assert isinstance(r.member_confidences, list)


def test_cluster_member_indices_in_range(service):
    """All member indices are valid indices into the input embeddings."""
    n = 40
    embeddings = _synthetic_embeddings(n)
    texts = _synthetic_texts(n)
    results = service.cluster_embeddings(embeddings, texts, min_cluster_size=3, min_samples=2)
    for r in results:
        for idx in r.member_indices:
            assert 0 <= idx < n
