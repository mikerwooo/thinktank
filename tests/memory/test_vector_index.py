"""Tests for vector index (numpy-based cosine similarity)."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

import pytest

from memory.vector_index import VectorIndex


@pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")
class TestVectorIndex:
    """Tests for VectorIndex operations."""

    def setup_method(self):
        self.dim = 8
        self.index = VectorIndex(dimension=self.dim)
        self.temp_dir = tempfile.mkdtemp(prefix="loki-test-vector-")

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _random_vec(self):
        vec = np.random.randn(self.dim).astype(np.float32)
        return vec / np.linalg.norm(vec)

    def test_add_and_search(self):
        vec = self._random_vec()
        self.index.add("doc-1", vec, {"title": "Test"})
        results = self.index.search(vec, k=1)
        assert len(results) >= 1
        assert results[0][0] == "doc-1"

    def test_search_returns_most_similar(self):
        target = self._random_vec()
        similar = target + np.random.randn(self.dim).astype(np.float32) * 0.01
        similar = similar / np.linalg.norm(similar)
        distant = self._random_vec()

        self.index.add("similar", similar, {})
        self.index.add("distant", distant, {})

        results = self.index.search(target, k=2)
        assert results[0][0] == "similar", "Most similar vector should be first"

    def test_add_multiple_and_search(self):
        for i in range(10):
            self.index.add(f"doc-{i}", self._random_vec(), {"index": i})
        results = self.index.search(self._random_vec(), k=5)
        assert len(results) == 5

    def test_remove(self):
        vec = self._random_vec()
        self.index.add("to-remove", vec, {})
        self.index.remove("to-remove")
        results = self.index.search(vec, k=1)
        # Should return empty or not contain removed id
        for r in results:
            assert r[0] != "to-remove"

    def test_update(self):
        old_vec = self._random_vec()
        new_vec = self._random_vec()
        self.index.add("doc-1", old_vec, {"version": 1})
        self.index.update("doc-1", new_vec)
        results = self.index.search(new_vec, k=1)
        assert results[0][0] == "doc-1"

    def test_get_metadata(self):
        vec = self._random_vec()
        self.index.add("doc-1", vec, {"title": "My Document", "page": 5})
        meta = self.index.get_metadata("doc-1")
        assert meta is not None
        assert meta["title"] == "My Document"
        assert meta["page"] == 5

    def test_get_metadata_missing_id(self):
        result = self.index.get_metadata("nonexistent")
        assert result is None

    def test_clear(self):
        for i in range(5):
            self.index.add(f"doc-{i}", self._random_vec(), {})
        self.index.clear()
        stats = self.index.get_stats()
        assert stats["count"] == 0

    def test_get_stats(self):
        for i in range(3):
            self.index.add(f"doc-{i}", self._random_vec(), {"i": i})
        stats = self.index.get_stats()
        assert stats["count"] == 3
        assert stats["dimension"] == self.dim
        assert stats["memory_bytes"] > 0

    def test_empty_search(self):
        results = self.index.search(self._random_vec(), k=5)
        assert results == [] or len(results) == 0

    def test_dimension_consistency(self):
        index = VectorIndex(dimension=16)
        vec = np.random.randn(16).astype(np.float32)
        index.add("doc-1", vec, {})
        stats = index.get_stats()
        assert stats["dimension"] == 16
