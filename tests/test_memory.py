"""Tests for memory store."""

import os
import pytest
from src.memory.chroma_store import MemoryStore, MemoryError


@pytest.fixture
def store(tmp_path):
    yield MemoryStore(persist_dir=str(tmp_path / "chroma"))


class TestMemoryStore:
    def test_store_code_pattern(self, store):
        doc_id = store.store_code_pattern(
            "Singleton", "Thread-safe singleton", "class S: _inst = None"
        )
        assert doc_id.startswith("pattern_")

    def test_store_bug_fix(self, store):
        doc_id = store.store_bug_fix(
            "NPE", "NullPointerError", "Missing check", "Added guard"
        )
        assert doc_id.startswith("bug_")

    def test_store_architecture_decision(self, store):
        doc_id = store.store_architecture_decision(
            "Use PostgreSQL", "Need ACID", "PostgreSQL", "Good for relational"
        )
        assert doc_id.startswith("adr_")

    def test_search(self, store):
        store.store_code_pattern("Retry", "Retry with backoff", "def retry(): ...")
        results = store.search("retry pattern", "code_patterns")
        assert len(results) > 0
        assert "Retry" in results[0]["content"]

    def test_search_invalid_collection(self, store):
        with pytest.raises(MemoryError):
            store.search("query", "nonexistent")

    def test_search_all(self, store):
        store.store_code_pattern("Pattern1", "Desc", "code")
        store.store_bug_fix("Bug1", "Error", "Cause", "Fix")
        results = store.search_all("test query")
        assert "code_patterns" in results
        assert "bugs_fixed" in results
        assert "architecture_decisions" in results

    def test_get_stats(self, store):
        store.store_code_pattern("P1", "D1", "C1")
        stats = store.get_stats()
        assert stats["code_patterns"] == 1
        assert stats["bugs_fixed"] == 0

    def test_delete(self, store):
        doc_id = store.store_code_pattern("ToDelete", "D", "C")
        store.delete("code_patterns", doc_id)
        stats = store.get_stats()
        assert stats["code_patterns"] == 0

    def test_update(self, store):
        doc_id = store.store_code_pattern("Original", "Desc", "code_v1")
        store.update("code_patterns", doc_id, "Updated content")
        results = store.search("Updated", "code_patterns")
        assert len(results) > 0

    def test_dedup_detection(self, store):
        id1 = store.store_code_pattern("Same", "Same desc", "same code")
        id2 = store.store_code_pattern("Same", "Same desc", "same code")
        # Should return existing ID instead of creating duplicate
        assert id1 == id2
