"""
Memory Manager - per-customer long-term memory (Phase 3).

Pehle yeh fake SHA-256 embeddings use karta tha (broken).
Ab real embeddings (Gemini text-embedding-004) use karta hai via embedding_service,
aur vector_store (Qdrant ya in-process) me store karta hai.

Memory do tarah ki hoti hai:
  1. interactions  - har baat-cheet ka summary (semantic search ke liye embedded)
  2. facts         - customer ke baare me stable facts (address, pasand, dietary, etc.)

Memory collection: settings.QDRANT_COLLECTION (default "ai_memory")
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger

from config import settings
from services.embedding_service import embed_text, embed_query
from services.vector_store import get_vector_store


class MemoryManager:
    """Per-customer persistent memory backed by the vector store."""

    def __init__(self, collection: Optional[str] = None):
        self.collection = collection or getattr(settings, "QDRANT_COLLECTION", "ai_memory")
        self.store = get_vector_store()

    # ── Interactions (conversation turns) ────────────────────────
    async def add_interaction(
        self, customer_id: str, business_id: str, message: str, response: str
    ) -> None:
        text = f"Customer: {message}\nAI: {response}"
        try:
            vector = await embed_text(text)
        except Exception as e:
            logger.debug("[memory] embed interaction failed: {}", e)
            return
        pid = str(uuid.uuid4())
        self.store.upsert(
            collection=self.collection,
            point_id=pid,
            vector=vector,
            payload={
                "point_id": pid,
                "customer_id": customer_id,
                "business_id": business_id,
                "type": "interaction",
                "message": message,
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def search_similar(
        self, customer_id: str, business_id: str, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        try:
            qvec = await embed_query(query)
        except Exception as e:
            logger.debug("[memory] embed query failed: {}", e)
            return []
        return self.store.search(
            collection=self.collection,
            query_vector=qvec,
            filters={"customer_id": customer_id, "business_id": business_id, "type": "interaction"},
            limit=limit,
            score_threshold=0.3,
        )

    # ── Facts (stable customer attributes) ───────────────────────
    async def store_fact(
        self, customer_id: str, business_id: str, fact: str, fact_type: str = "general"
    ) -> None:
        try:
            vector = await embed_text(fact)
        except Exception as e:
            logger.debug("[memory] embed fact failed: {}", e)
            return
        pid = str(uuid.uuid4())
        self.store.upsert(
            collection=self.collection,
            point_id=pid,
            vector=vector,
            payload={
                "point_id": pid,
                "customer_id": customer_id,
                "business_id": business_id,
                "type": "fact",
                "fact_type": fact_type,
                "fact": fact,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def recall_facts(
        self, customer_id: str, business_id: str, fact_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {
            "customer_id": customer_id,
            "business_id": business_id,
            "type": "fact",
        }
        if fact_type:
            filters["fact_type"] = fact_type
        # Facts usually few & stable => scroll/count via filter, not vector search.
        # Use search with a neutral query vector only if store supports filter-only.
        try:
            qvec = await embed_query("customer profile preferences address")
        except Exception:
            qvec = []
        return self.store.search(
            collection=self.collection,
            query_vector=qvec,
            filters=filters,
            limit=50,
            score_threshold=0.0,
        )

    # ── Aggregate context for the LLM ────────────────────────────
    async def get_context(self, customer_id: str, business_id: str, query: str = "") -> Dict[str, Any]:
        """
        Customer ke baare me relevant context return karta hai:
          - facts (stable: address, preferences, etc.)
          - recent_similar (query se related pichli baat-cheet)
        """
        facts = await self.recall_facts(customer_id, business_id)
        recent = []
        if query:
            recent = await self.search_similar(customer_id, business_id, query, limit=3)
        return {
            "customer_id": customer_id,
            "business_id": business_id,
            "interaction_count": self.store.count(
                self.collection,
                {"customer_id": customer_id, "business_id": business_id, "type": "interaction"},
            ),
            "facts": [f.get("fact") for f in facts if f.get("fact")],
            "recent_similar": recent,
        }

    async def clear_old_memory(self, customer_id: str, days: int = 90) -> int:
        """
        Days se purane interactions hatao. Qdrant payload delete by timestamp
        complex hai, so iska effective impl production me scheduled job hoga.
        In-process store me sab clear kar deta hai (dev convenience).
        """
        return self.store.delete_by_payload(
            self.collection, {"customer_id": customer_id}
        )


# Convenience module-level instance
_memory: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    global _memory
    if _memory is None:
        _memory = MemoryManager()
    return _memory
