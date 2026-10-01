"""Local RAG Cache subsystem.

Provides deterministic, course-scoped offline knowledge retrieval using BM25.
Enforces strict course isolation so knowledge chunks from Course A can never
leak into Course B.
"""

from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gayatri.local_runtime.rag_cache")

_TOKEN_PATTERN = re.compile(r"\b[a-zA-Z0-9_]+\b")


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return _TOKEN_PATTERN.findall(text.lower())


class LocalRAGCache:
    """Course-isolated offline BM25 knowledge search engine."""

    def __init__(self, index_dir: Optional[Path | str] = None) -> None:
        self.index_dir = Path(index_dir or "data/cache/rag").resolve()
        self.index_dir.mkdir(parents=True, exist_ok=True)
        # In-memory index: {course_id: {chunk_id: chunk_dict}}
        self._in_memory_indices: Dict[str, Dict[str, Any]] = {}
        self._load_existing_indices()

    def _load_existing_indices(self) -> None:
        """Scan index_dir and preload existing course knowledge indices."""
        for file in self.index_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                cid = data.get("course_id")
                if cid and "chunks" in data:
                    self._in_memory_indices[cid] = data
            except Exception as exc:
                logger.warning("Failed to load local RAG index %s: %s", file, exc)

    def index_course_knowledge(
        self,
        course_id: str,
        chunks: List[Dict[str, Any]],
        version_tag: str = "v1.0",
    ) -> int:
        """Index a list of text chunks strictly bound to course_id.
        
        Each chunk should have: 'id', 'text', and optional 'metadata'.
        """
        formatted_chunks = []
        for idx, chunk in enumerate(chunks):
            cid = chunk.get("id") or f"{course_id}_chk_{idx + 1}"
            text = chunk.get("text") or chunk.get("content") or ""
            metadata = chunk.get("metadata") or {
                k: v for k, v in chunk.items() if k not in ("id", "text", "content")
            }
            tokens = _tokenize(text)
            formatted_chunks.append({
                "id": cid,
                "text": text,
                "tokens": tokens,
                "token_count": len(tokens),
                "metadata": metadata,
                "course_id": course_id,
            })

        index_data = {
            "course_id": course_id,
            "version_tag": version_tag,
            "total_chunks": len(formatted_chunks),
            "chunks": formatted_chunks,
        }

        self._in_memory_indices[course_id] = index_data

        target_file = self.index_dir / f"{course_id}_{version_tag}.json"
        target_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")

        return len(formatted_chunks)

    def search(
        self,
        query: str,
        course_id: str,
        top_k: int = 3,
        version_tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search course knowledge chunks using BM25 scoring.
        
        Strictly course-isolated: Only returns chunks registered under course_id.
        """
        index_data = self._in_memory_indices.get(course_id)
        if not index_data:
            # Attempt to read from disk if not loaded in memory
            pattern = f"{course_id}_{version_tag or '*'}.json"
            matching_files = list(self.index_dir.glob(pattern))
            if matching_files:
                try:
                    index_data = json.loads(matching_files[0].read_text(encoding="utf-8"))
                    self._in_memory_indices[course_id] = index_data
                except Exception:
                    pass

        if not index_data or not index_data.get("chunks"):
            return []

        chunks: List[Dict[str, Any]] = index_data["chunks"]
        total_docs = len(chunks)
        if total_docs == 0:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        avg_doc_len = sum(c.get("token_count", len(c.get("tokens", []))) for c in chunks) / max(total_docs, 1)

        # Calculate document frequencies for query tokens
        doc_freqs: Dict[str, int] = {}
        for token in set(query_tokens):
            df = sum(1 for c in chunks if token in c.get("tokens", []))
            doc_freqs[token] = df

        # BM25 parameters
        k1 = 1.5
        b = 0.75

        scored_results = []
        for chunk in chunks:
            tokens = chunk.get("tokens", [])
            doc_len = chunk.get("token_count", len(tokens))
            score = 0.0

            # Count term occurrences in doc
            term_counts: Dict[str, int] = {}
            for t in tokens:
                term_counts[t] = term_counts.get(t, 0) + 1

            for q_term in query_tokens:
                tf = term_counts.get(q_term, 0)
                if tf == 0:
                    continue

                df = doc_freqs.get(q_term, 0)
                # Robertson-Spärck Jones IDF
                idf = math.log(((total_docs - df + 0.5) / (df + 0.5)) + 1.0)
                if idf < 0:
                    idf = 0.01

                num = tf * (k1 + 1.0)
                denom = tf + k1 * (1.0 - b + b * (doc_len / max(avg_doc_len, 1.0)))
                score += idf * (num / denom)

            if score > 0.0:
                scored_results.append({
                    "id": chunk["id"],
                    "text": chunk["text"],
                    "score": round(score, 4),
                    "metadata": chunk.get("metadata", {}),
                    "course_id": course_id,
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def get_indexed_courses(self) -> List[str]:
        """Return list of course IDs currently indexed in local RAG cache."""
        return list(self._in_memory_indices.keys())

    def clear_course_index(self, course_id: str) -> bool:
        """Remove a course's knowledge index from memory and disk."""
        removed = False
        if course_id in self._in_memory_indices:
            del self._in_memory_indices[course_id]
            removed = True

        for f in self.index_dir.glob(f"{course_id}_*.json"):
            try:
                f.unlink()
                removed = True
            except Exception:
                pass

        return removed
