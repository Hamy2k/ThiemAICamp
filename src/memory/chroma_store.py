"""
UPGRADE 1 - MEMORY SYSTEM (v2 - with error handling)
Lưu trữ code patterns, bugs đã fix, architecture decisions vào ChromaDB.
"""

import json
import time
import logging
from typing import Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings

from src.utils import retry, ThiemAICampError

logger = logging.getLogger(__name__)


class MemoryError(ThiemAICampError):
    """Error trong memory operations."""
    pass


class MemoryStore:
    """ChromaDB-based memory system cho AI Software Office."""

    COLLECTIONS = {
        "code_patterns": "Cac code patterns da hoc duoc tu projects",
        "bugs_fixed": "Bugs da fix va cach giai quyet",
        "architecture_decisions": "Cac quyet dinh kien truc va ly do",
    }

    def __init__(self, persist_dir: str = "./data/chromadb"):
        self.persist_dir = persist_dir
        try:
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise MemoryError(f"ChromaDB init failed: {e}") from e

        self._collections = {}
        for name in self.COLLECTIONS:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"description": self.COLLECTIONS[name]},
            )

    @retry(max_attempts=2, delay=0.5)
    def store_code_pattern(
        self,
        pattern_name: str,
        description: str,
        code_example: str,
        language: str = "python",
        tags: Optional[list[str]] = None,
    ) -> str:
        """Lưu một code pattern mới."""
        doc_id = f"pattern_{int(time.time() * 1000)}"
        metadata = {
            "pattern_name": pattern_name,
            "language": language,
            "tags": json.dumps(tags or []),
            "created_at": datetime.now().isoformat(),
        }
        content = f"Pattern: {pattern_name}\n\nDescription: {description}\n\nCode:\n{code_example}"

        # Dedup check
        existing = self._collections["code_patterns"].query(
            query_texts=[content], n_results=1
        )
        if existing["distances"] and existing["distances"][0] and existing["distances"][0][0] < 0.05:
            logger.info(f"Duplicate pattern detected, skipping: {pattern_name}")
            return existing["ids"][0][0]

        self._collections["code_patterns"].add(
            ids=[doc_id], documents=[content], metadatas=[metadata],
        )
        logger.info(f"Stored code pattern: {pattern_name} ({doc_id})")
        return doc_id

    @retry(max_attempts=2, delay=0.5)
    def store_bug_fix(
        self,
        bug_title: str,
        error_message: str,
        root_cause: str,
        fix_description: str,
        code_diff: str = "",
    ) -> str:
        """Lưu thông tin bug đã fix."""
        doc_id = f"bug_{int(time.time() * 1000)}"
        metadata = {
            "bug_title": bug_title,
            "created_at": datetime.now().isoformat(),
        }
        content = (
            f"Bug: {bug_title}\n\n"
            f"Error: {error_message}\n\n"
            f"Root Cause: {root_cause}\n\n"
            f"Fix: {fix_description}\n\n"
            f"Diff:\n{code_diff}"
        )
        self._collections["bugs_fixed"].add(
            ids=[doc_id], documents=[content], metadatas=[metadata],
        )
        logger.info(f"Stored bug fix: {bug_title} ({doc_id})")
        return doc_id

    @retry(max_attempts=2, delay=0.5)
    def store_architecture_decision(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str,
        alternatives: str = "",
    ) -> str:
        """Lưu một architecture decision record (ADR)."""
        doc_id = f"adr_{int(time.time() * 1000)}"
        metadata = {
            "title": title,
            "created_at": datetime.now().isoformat(),
        }
        content = (
            f"ADR: {title}\n\n"
            f"Context: {context}\n\n"
            f"Decision: {decision}\n\n"
            f"Consequences: {consequences}\n\n"
            f"Alternatives Considered: {alternatives}"
        )
        self._collections["architecture_decisions"].add(
            ids=[doc_id], documents=[content], metadatas=[metadata],
        )
        logger.info(f"Stored ADR: {title} ({doc_id})")
        return doc_id

    def update(self, collection_name: str, doc_id: str, content: str, metadata: dict = None) -> None:
        """Update một document trong collection."""
        if collection_name not in self._collections:
            raise MemoryError(f"Collection '{collection_name}' khong ton tai")
        self._collections[collection_name].update(
            ids=[doc_id], documents=[content], metadatas=[metadata] if metadata else None,
        )

    def search(
        self,
        query: str,
        collection_name: str = "code_patterns",
        n_results: int = 5,
    ) -> list[dict]:
        """Tìm kiếm trong memory bằng semantic search."""
        if collection_name not in self._collections:
            raise MemoryError(f"Collection '{collection_name}' khong ton tai")

        try:
            results = self._collections[collection_name].query(
                query_texts=[query], n_results=n_results,
            )
        except Exception as e:
            logger.error(f"Search failed in {collection_name}: {e}")
            return []

        items = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                items.append({
                    "id": results["ids"][0][i],
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        return items

    def search_all(self, query: str, n_results: int = 3) -> dict[str, list[dict]]:
        """Tìm kiếm trong tất cả collections."""
        return {
            name: self.search(query, name, n_results)
            for name in self.COLLECTIONS
        }

    def get_stats(self) -> dict:
        return {name: self._collections[name].count() for name in self.COLLECTIONS}

    def delete(self, collection_name: str, doc_id: str) -> None:
        if collection_name not in self._collections:
            raise MemoryError(f"Collection '{collection_name}' khong ton tai")
        self._collections[collection_name].delete(ids=[doc_id])
