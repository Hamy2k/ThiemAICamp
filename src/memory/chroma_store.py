"""
UPGRADE 1 - MEMORY SYSTEM
Lưu trữ code patterns, bugs đã fix, architecture decisions vào ChromaDB.
Sử dụng LangChain + Anthropic embeddings để tìm kiếm ngữ nghĩa.
"""

import os
import json
import time
from typing import Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings
from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document


class MemoryStore:
    """ChromaDB-based memory system cho AI Software Office."""

    COLLECTIONS = {
        "code_patterns": "Các code patterns đã học được từ projects",
        "bugs_fixed": "Bugs đã fix và cách giải quyết",
        "architecture_decisions": "Các quyết định kiến trúc và lý do",
    }

    def __init__(self, persist_dir: str = "./data/chromadb"):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collections = {}
        for name in self.COLLECTIONS:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"description": self.COLLECTIONS[name]},
            )

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
        self._collections["code_patterns"].add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata],
        )
        return doc_id

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
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata],
        )
        return doc_id

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
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata],
        )
        return doc_id

    def search(
        self,
        query: str,
        collection_name: str = "code_patterns",
        n_results: int = 5,
    ) -> list[dict]:
        """Tìm kiếm trong memory bằng semantic search."""
        if collection_name not in self._collections:
            raise ValueError(f"Collection '{collection_name}' không tồn tại")

        results = self._collections[collection_name].query(
            query_texts=[query],
            n_results=n_results,
        )

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
        """Thống kê số lượng records trong mỗi collection."""
        return {
            name: self._collections[name].count()
            for name in self.COLLECTIONS
        }

    def delete(self, collection_name: str, doc_id: str) -> None:
        """Xóa một document khỏi collection."""
        self._collections[collection_name].delete(ids=[doc_id])
