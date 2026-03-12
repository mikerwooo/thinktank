"""Tests for memory consolidation pipeline."""

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from memory.consolidation import ConsolidationPipeline, ConsolidationResult, Cluster
from memory.schemas import EpisodeTrace, SemanticPattern, Link
from memory.storage import MemoryStorage


class TestConsolidationResult:
    """Tests for ConsolidationResult dataclass."""

    def test_default_values(self):
        result = ConsolidationResult()
        assert result.patterns_created == 0
        assert result.patterns_merged == 0
        assert result.anti_patterns_created == 0
        assert result.links_created == 0
        assert result.episodes_processed == 0
        assert result.duration_seconds == 0.0

    def test_to_dict(self):
        result = ConsolidationResult(
            patterns_created=3,
            patterns_merged=1,
            anti_patterns_created=2,
            links_created=5,
            episodes_processed=10,
            duration_seconds=1.5
        )
        d = result.to_dict()
        assert d["patterns_created"] == 3
        assert d["patterns_merged"] == 1
        assert d["anti_patterns_created"] == 2
        assert d["links_created"] == 5
        assert d["episodes_processed"] == 10
        assert d["duration_seconds"] == 1.5


class TestCluster:
    """Tests for Cluster dataclass."""

    def test_default_empty_cluster(self):
        cluster = Cluster()
        assert cluster.episodes == []
        assert cluster.centroid is None
        assert cluster.label == ""

    def test_cluster_to_dict(self):
        episode = EpisodeTrace.create(
            task_id="test-1",
            goal="Test goal",
            outcome="success"
        )
        cluster = Cluster(episodes=[episode], label="test-cluster")
        d = cluster.to_dict()
        assert d["label"] == "test-cluster"
        assert d["size"] == 1


class TestConsolidationPipeline:
    """Tests for the consolidation pipeline."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp(prefix="loki-test-consolidation-")
        self.base_path = os.path.join(self.temp_dir, "memory")
        os.makedirs(self.base_path, exist_ok=True)
        self.storage = MemoryStorage(base_path=self.base_path)
        self.pipeline = ConsolidationPipeline(
            storage=self.storage,
            base_path=self.base_path
        )

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_episode(self, task_id, goal, outcome="success", task_type="implementation"):
        return EpisodeTrace.create(
            task_id=task_id,
            goal=goal,
            outcome=outcome,
            task_type=task_type
        )

    def test_consolidate_empty_returns_zero_result(self):
        result = self.pipeline.consolidate(since_hours=24)
        assert isinstance(result, ConsolidationResult)
        assert result.episodes_processed == 0
        assert result.patterns_created == 0

    def test_consolidate_returns_consolidation_result(self):
        result = self.pipeline.consolidate(since_hours=1)
        assert isinstance(result, ConsolidationResult)
        assert hasattr(result, 'duration_seconds')
        assert result.duration_seconds >= 0

    def test_cluster_by_task_type(self):
        episodes = [
            self._make_episode("t1", "Build API", task_type="implementation"),
            self._make_episode("t2", "Build UI", task_type="implementation"),
            self._make_episode("t3", "Fix bug", task_type="debugging"),
        ]
        clusters = self.pipeline.cluster_by_task_type(episodes)
        assert "implementation" in clusters
        assert "debugging" in clusters
        assert len(clusters["implementation"]) == 2
        assert len(clusters["debugging"]) == 1

    def test_extract_anti_patterns_from_failures(self):
        failed_episodes = [
            self._make_episode("f1", "Deploy app", outcome="failure"),
            self._make_episode("f2", "Deploy service", outcome="failure"),
        ]
        anti_patterns = self.pipeline.extract_anti_patterns(failed_episodes)
        assert isinstance(anti_patterns, list)

    def test_extract_common_pattern_from_cluster(self):
        episodes = [
            self._make_episode("t1", "Build REST API endpoint"),
            self._make_episode("t2", "Build REST API handler"),
            self._make_episode("t3", "Build REST API route"),
        ]
        pattern = self.pipeline.extract_common_pattern(episodes)
        # May return None if episodes lack sufficient common signals
        if pattern is not None:
            assert isinstance(pattern, SemanticPattern)

    def test_create_zettelkasten_links(self):
        pattern = SemanticPattern.create(
            pattern="Build API endpoints",
            category="implementation",
            confidence=0.8
        )
        other_patterns = [
            SemanticPattern.create(
                pattern="Build REST handlers",
                category="implementation",
                confidence=0.7
            ),
            SemanticPattern.create(
                pattern="Debug memory leaks",
                category="debugging",
                confidence=0.9
            ),
        ]
        links = self.pipeline.create_zettelkasten_links(pattern, other_patterns)
        assert isinstance(links, list)
        for link in links:
            assert isinstance(link, Link)


class TestCompressionUtilities:
    """Tests for episode compression helpers."""

    def test_compress_episode_to_summary(self):
        from memory.consolidation import compress_episode_to_summary
        episode = EpisodeTrace.create(
            task_id="t1",
            goal="Build login page",
            outcome="success"
        )
        summary = compress_episode_to_summary(episode)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_compress_episodes_to_pattern_desc(self):
        from memory.consolidation import compress_episodes_to_pattern_desc
        episodes = [
            EpisodeTrace.create(task_id="t1", goal="Build API endpoint", outcome="success"),
            EpisodeTrace.create(task_id="t2", goal="Build API handler", outcome="success"),
        ]
        desc = compress_episodes_to_pattern_desc(episodes)
        assert isinstance(desc, str)
        assert len(desc) > 0
