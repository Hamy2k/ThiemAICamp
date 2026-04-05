"""Tests for config system."""

import os
import pytest
from src import config


class TestConfig:
    def test_defaults_exist(self):
        assert config.LLM_MODEL
        assert config.DB_PATH
        assert config.CHROMADB_PATH
        assert config.SANDBOX_TIMEOUT > 0
        assert config.APPROVAL_TIMEOUT > 0
        assert config.REVIEW_MIN_SCORE > 0
        assert config.METRICS_MAX_MEMORY > 0

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("THIEMAICAMP_SANDBOX_TIMEOUT", "60")
        # Re-import to pick up new env
        import importlib
        importlib.reload(config)
        assert config.SANDBOX_TIMEOUT == 60
        # Reset
        monkeypatch.delenv("THIEMAICAMP_SANDBOX_TIMEOUT")
        importlib.reload(config)

    def test_all_config_values_are_not_none(self):
        for attr in dir(config):
            if attr.isupper() and not attr.startswith("_"):
                val = getattr(config, attr)
                # WEBHOOK_URL can be empty string
                assert val is not None, f"config.{attr} is None"
