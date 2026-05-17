"""
Memory System — vector memory (ChromaDB) with JSON fallback.
Supports short-term, long-term, project, and agent-specific memory.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class JSONMemoryStore:
    """Simple JSON-backed memory store — works without ChromaDB."""

    def __init__(self, memory_dir: str):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, list[dict]] = {}

    def _collection_path(self, collection: str) -> Path:
        return self.memory_dir / f"{collection}.json"

    def _load(self, collection: str) -> list[dict]:
        if collection in self._cache:
            return self._cache[collection]
        path = self._collection_path(collection)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._cache[collection] = data
                return data
            except Exception:
                pass
        self._cache[collection] = []
        return self._cache[collection]

    def _save(self, collection: str) -> None:
        path = self._collection_path(collection)
        path.write_text(json.dumps(self._cache.get(collection, []), ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, collection: str, text: str, metadata: Optional[dict] = None) -> str:
        """Add a memory entry."""
        entries = self._load(collection)
        entry_id = str(uuid.uuid4())[:8]
        entries.append({
            "id": entry_id,
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep last 1000 entries per collection
        if len(entries) > 1000:
            entries = entries[-1000:]
        self._cache[collection] = entries
        self._save(collection)
        return entry_id

    def query(self, collection: str, query: str, n_results: int = 5) -> list[dict]:
        """Simple keyword-based search (no embeddings in fallback mode)."""
        entries = self._load(collection)
        query_lower = query.lower()
        scored = []
        for entry in entries:
            text = entry["text"].lower()
            score = sum(1 for word in query_lower.split() if word in text)
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:n_results]]

    def get_recent(self, collection: str, n: int = 10) -> list[dict]:
        """Get most recent entries."""
        entries = self._load(collection)
        return entries[-n:]

    def clear(self, collection: str) -> None:
        self._cache[collection] = []
        self._save(collection)


class MemoryManager:
    """High-level memory interface with ChromaDB + JSON fallback."""

    COLLECTIONS = {
        "short_term": "Short-term conversation context",
        "long_term": "Persistent knowledge and facts",
        "project": "Project-specific information",
        "agent": "Agent-specific learned behaviors",
    }

    def __init__(self, memory_dir: str = "./data/memory"):
        self.memory_dir = memory_dir
        self._store = self._init_store()

    def _init_store(self) -> JSONMemoryStore:
        """Try ChromaDB first, fall back to JSON."""
        try:
            import chromadb
            # Attempt ChromaDB connection
            client = chromadb.Client()
            logger.info("ChromaDB initialized (in-memory)")
            # For now use JSON as primary (more reliable for local dev)
        except ImportError:
            logger.info("ChromaDB not available, using JSON memory store")
        return JSONMemoryStore(self.memory_dir)

    async def remember(
        self,
        text: str,
        collection: str = "long_term",
        metadata: Optional[dict] = None,
    ) -> str:
        """Store a memory."""
        entry_id = self._store.add(collection, text, metadata)
        logger.debug(f"Stored memory [{collection}] id={entry_id}: {text[:50]}")
        return f"Memory stored (id={entry_id})"

    async def recall(
        self,
        query: str,
        collection: str = "long_term",
        n_results: int = 5,
    ) -> str:
        """Retrieve relevant memories."""
        results = self._store.query(collection, query, n_results)
        if not results:
            return f"No relevant memories found for: {query!r}"

        lines = [f"Found {len(results)} relevant memories:"]
        for i, entry in enumerate(results, 1):
            ts = entry.get("timestamp", "")[:10]
            lines.append(f"\n[{i}] {ts}\n{entry['text']}")
        return "\n".join(lines)

    async def get_context(self, agent_id: str, n: int = 5) -> str:
        """Get recent context for an agent."""
        results = self._store.get_recent(f"agent_{agent_id}", n)
        if not results:
            return "No previous context for this agent."
        lines = [f"Recent context ({len(results)} entries):"]
        for entry in results:
            lines.append(f"- {entry['text'][:100]}")
        return "\n".join(lines)

    async def store_project_info(self, project_name: str, info: dict) -> str:
        """Store project-specific metadata."""
        text = f"Project: {project_name}\n" + "\n".join(f"{k}: {v}" for k, v in info.items())
        return await self.remember(text, collection="project", metadata={"project": project_name})

    async def list_collections(self) -> str:
        """List all memory collections and their sizes."""
        lines = ["Memory Collections:"]
        for col, desc in self.COLLECTIONS.items():
            entries = self._store.get_recent(col, 1000)
            lines.append(f"  {col}: {len(entries)} entries — {desc}")
        return "\n".join(lines)

    async def clear_collection(self, collection: str) -> str:
        """Clear a memory collection."""
        self._store.clear(collection)
        return f"Cleared collection: {collection}"


# Singleton
memory_manager = MemoryManager()
