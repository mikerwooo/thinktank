"""Tests for token economics tracking and optimization."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from memory.token_economics import TokenEconomics, THRESHOLDS


class TestThresholds:
    """Tests for threshold configuration."""

    def test_thresholds_exist(self):
        assert isinstance(THRESHOLDS, list)
        assert len(THRESHOLDS) > 0

    def test_thresholds_have_required_fields(self):
        for t in THRESHOLDS:
            assert "metric" in t, f"Threshold missing 'metric': {t}"
            assert "op" in t, f"Threshold missing 'op': {t}"
            assert "value" in t, f"Threshold missing 'value': {t}"
            assert "action" in t, f"Threshold missing 'action': {t}"
            assert "priority" in t, f"Threshold missing 'priority': {t}"

    def test_thresholds_have_valid_operators(self):
        valid_ops = {">", "<", ">=", "<=", "==", "!="}
        for t in THRESHOLDS:
            assert t["op"] in valid_ops, f"Invalid operator '{t['op']}' in threshold: {t}"

    def test_thresholds_have_positive_priority(self):
        for t in THRESHOLDS:
            assert t["priority"] > 0, f"Priority should be positive: {t}"


class TestTokenEconomics:
    """Tests for TokenEconomics class."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp(prefix="loki-test-token-")
        self.base_path = os.path.join(self.temp_dir, "memory")
        os.makedirs(self.base_path, exist_ok=True)
        self.economics = TokenEconomics(base_path=self.base_path)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        assert self.economics is not None
        assert hasattr(self.economics, 'metrics')
        assert hasattr(self.economics, 'session_id')

    def test_save_and_load(self):
        self.economics.save()
        file_path = Path(self.base_path) / "token_economics.json"
        assert file_path.exists(), "save() should create token_economics.json"

        # Load into new instance
        new_economics = TokenEconomics(base_path=self.base_path)
        new_economics.load()
        assert new_economics.session_id == self.economics.session_id

    def test_save_creates_valid_json(self):
        self.economics.save()
        file_path = Path(self.base_path) / "token_economics.json"
        with open(file_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_reset_clears_metrics(self):
        # Set some metrics first
        if hasattr(self.economics, 'metrics') and isinstance(self.economics.metrics, dict):
            for key in self.economics.metrics:
                self.economics.metrics[key] = 100
            self.economics.reset()
            for key in self.economics.metrics:
                assert self.economics.metrics[key] == 0, f"Metric {key} should be 0 after reset"

    def test_load_nonexistent_file(self):
        empty_dir = tempfile.mkdtemp(prefix="loki-test-empty-")
        try:
            economics = TokenEconomics(base_path=empty_dir)
            # Should not raise - graceful handling of missing file
            economics.load()
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)


class TestTokenEstimation:
    """Tests for token estimation utilities."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp(prefix="loki-test-token-est-")
        self.base_path = os.path.join(self.temp_dir, "memory")
        os.makedirs(self.base_path, exist_ok=True)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_estimate_tokens_exists(self):
        from memory.token_economics import estimate_tokens
        result = estimate_tokens("Hello world, this is a test sentence.")
        assert isinstance(result, (int, float))
        assert result > 0

    def test_estimate_tokens_empty_string(self):
        from memory.token_economics import estimate_tokens
        result = estimate_tokens("")
        assert result == 0

    def test_estimate_tokens_scales_with_length(self):
        from memory.token_economics import estimate_tokens
        short = estimate_tokens("Hello")
        long = estimate_tokens("Hello world, this is a much longer sentence with many more words in it.")
        assert long > short, "Longer text should estimate more tokens"
