"""
Vector Store - Qdrant (production) ya in-process numpy (fallback) ke upar
ek unified interface. Knowledge Base aur Memory dono yahi use karte hain.

Agar QDRANT_ENABLED=True aur Qdrant reachable hai => Qdrant.
Warna => InProcessVectorStore (numpy cosine similarity, restart pe DB se reload).

Yeh design isliye taaki:
  - Local Windows dev (jahan Qdrant nahi hai) me bhi feature chale.
  - Production me scale ho sake.
"""

import math
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from loguru import logger

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        PointStruct,
        VectorParams,
        Distance,
        PointIdsList,
        Filter,
        FieldCondition,
        MatchValue,
    )
    QDRANT_AVAILABLE = True
except Exception:
    QDRANT_AVAILABLE = False

from config import settings
from services.embedding_service import EMBEDDING_DIM


# ────────────────────────────────────────────────────────────────────
#  Qdrant-backed implementation
# ────────────────────────────────────────────────────────────────────
class QdrantStore:
    def __init__(self, host: str, port: int):
        self.client = QdrantClient(host=host, port=port, timeout=10)
        self._ok = False
        try:
            self.client.get_collections()
            self._ok = True
        except Exception as e:
            logger.warning("[vector] Qdrant not reachable at {}:{} - {}", host, port, e)
            self.client = None

    @property
    def available(self) -> bool:
        return self.client is not None and self._ok

    def _ensure_collection(self, collection: str):
        if not self.client:
            return
        try:
            names = [c.name for c in self.client.get_collections().collections]
            if collection not in names:
                self.client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
                )
                logger.info("[vector] Created Qdrant collection: {}", collection)
        except Exception as e:
            logger.debug("[vector] ensure_collection: {}", e)

    def upsert(self, collection: str, point_id: str, vector: List[float], payload: Dict[str, Any]):
        if not self.client:
            return
        self._ensure_collection(collection)
        try:
            # dimension safety
            if len(vector) < EMBEDDING_DIM:
                vector = vector + [0.0] * (EMBEDDING_DIM - len(vector))
            else:
                vector = vector[:EMBEDDING_DIM]
            self.client.upsert(
                collection_name=collection,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)],
            )
        except Exception as e:
            logger.warning("[vector] upsert failed: {}", e)

    def search(
        self,
        collection: str,
        query_vector: List[float],
        filters: Dict[str, Any],
        limit: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        self._ensure_collection(collection)
        if len(query_vector) < EMBEDDING_DIM:
            query_vector = query_vector + [0.0] * (EMBEDDING_DIM - len(query_vector))
        else:
            query_vector = query_vector[:EMBEDDING_DIM]
        try:
            must = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()]
            qfilter = Filter(must=must) if must else None
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=qfilter,
                limit=limit,
            )
            out = []
            for r in results:
                if r.score >= score_threshold:
                    p = dict(r.payload or {})
                    p["_score"] = r.score
                    out.append(p)
            return out
        except Exception as e:
            logger.warning("[vector] search failed: {}", e)
            return []

    def delete_by_payload(self, collection: str, filters: Dict[str, Any]) -> int:
        """Delete all points matching payload filters (e.g. business_id+doc_id)."""
        if not self.client:
            return 0
        try:
            must = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()]
            self.client.delete(
                collection_name=collection,
                points_selector=Filter(must=must),
            )
            return 1
        except Exception as e:
            logger.warning("[vector] delete_by_payload failed: {}", e)
            return 0

    def count(self, collection: str, filters: Dict[str, Any]) -> int:
        if not self.client:
            return 0
        try:
            must = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()]
            res = self.client.count(
                collection_name=collection,
                count_filter=Filter(must=must),
                exact=True,
            )
            return res.count
        except Exception:
            return 0


# ────────────────────────────────────────────────────────────────────
#  In-process fallback (numpy cosine similarity)
# ────────────────────────────────────────────────────────────────────
class InProcessStore:
    """Simple list-of-points store. Persistent nahi restart pe, but OK for dev/small data."""

    def __init__(self):
        self._data: Dict[str, Dict[str, Dict[str, Any]]] = {}  # collection -> {pid: {vector, payload}}
        logger.info("[vector] Using in-process vector store (fallback). Qdrant recommended for production.")

    @property
    def available(self) -> bool:
        return True

    def upsert(self, collection: str, point_id: str, vector: List[float], payload: Dict[str, Any]):
        if len(vector) < EMBEDDING_DIM:
            vector = vector + [0.0] * (EMBEDDING_DIM - len(vector))
        else:
            vector = vector[:EMBEDDING_DIM]
        self._data.setdefault(collection, {})[point_id] = {"vector": vector, "payload": payload}

    def search(
        self,
        collection: str,
        query_vector: List[float],
        filters: Dict[str, Any],
        limit: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        if len(query_vector) < EMBEDDING_DIM:
            query_vector = query_vector + [0.0] * (EMBEDDING_DIM - len(query_vector))
        else:
            query_vector = query_vector[:EMBEDDING_DIM]
        points = self._data.get(collection, {})
        scored = []
        for pid, entry in points.items():
            p = entry["payload"]
            if all(p.get(k) == v for k, v in filters.items()):
                score = _cosine(query_vector, entry["vector"])
                if score >= score_threshold:
                    rec = dict(p)
                    rec["_score"] = score
                    scored.append(rec)
        scored.sort(key=lambda x: x["_score"], reverse=True)
        return scored[:limit]

    def delete_by_payload(self, collection: str, filters: Dict[str, Any]) -> int:
        points = self._data.get(collection, {})
        to_remove = [
            pid for pid, e in points.items()
            if all(e["payload"].get(k) == v for k, v in filters.items())
        ]
        for pid in to_remove:
            del points[pid]
        return len(to_remove)

    def count(self, collection: str, filters: Dict[str, Any]) -> int:
        points = self._data.get(collection, {})
        return sum(
            1 for e in points.values()
            if all(e["payload"].get(k) == v for k, v in filters.items())
        )


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ────────────────────────────────────────────────────────────────────
#  Singleton factory
# ────────────────────────────────────────────────────────────────────
_store: Optional[Any] = None


def get_vector_store():
    """Return the active vector store (Qdrant if available, else in-process)."""
    global _store
    if _store is not None:
        return _store

    enabled = getattr(settings, "QDRANT_ENABLED", True)
    if enabled and QDRANT_AVAILABLE:
        # Support QDRANT_URL (e.g. "http://qdrant:6333" in Docker) in addition to QDRANT_HOST/PORT
        q_url = getattr(settings, "QDRANT_URL", "") or ""
        q_host = settings.QDRANT_HOST
        q_port = settings.QDRANT_PORT
        if q_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(q_url if "://" in q_url else f"http://{q_url}")
                q_host = parsed.hostname or q_host
                q_port = parsed.port or q_port
            except Exception:
                pass
        q = QdrantStore(host=q_host, port=q_port)
        if q.available:
            _store = q
            return _store

    _store = InProcessStore()
    return _store
