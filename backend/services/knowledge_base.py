"""
Knowledge Base (RAG) - Business-specific knowledge jo bot seekhta hai.

Ab real implementation: DB (metadata) + vector store (embeddings) based.
Pehle yeh in-memory dict tha (restart pe delete). Ab persistent hai.

Sources:
  - ingest_document(file_path)   => uploaded files (PDF/Word/Excel/TXT)
  - ingest_text(title, content)  => manual FAQ / policies
  - ingest_inventory(db)         => auto-ingest Product table
  - search(query)                => semantic top-k relevant chunks

Vector store collection: settings.QDRANT_KNOWLEDGE_COLLECTION (default "business_knowledge")
"""

import uuid
from typing import List, Dict, Any, Optional

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from database import async_session
from models import KnowledgeDocument, Product
from services.embedding_service import embed_texts, embed_query
from services.vector_store import get_vector_store
from services.document_parser import parse_file, chunk_text


KB_COLLECTION = lambda: getattr(settings, "QDRANT_KNOWLEDGE_COLLECTION", "business_knowledge")
SCORE_THRESHOLD = 0.35  # cosine similarity cutoff for relevant matches


class KnowledgeBase:
    """
    Business knowledge base backed by KnowledgeDocument table + vector store.
    Pass `db` when operating within a request; otherwise opens its own session.
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.store = get_vector_store()

    # ── internal session helper ──────────────────────────────────
    def _session(self):
        """Return (session, should_close) tuple."""
        if self.db is not None:
            return self.db, False
        return async_session(), True

    # ── chunk upsert (private) ───────────────────────────────────
    async def _store_chunks(
        self,
        business_id: str,
        doc_id: str,
        chunks: List[str],
        title: str,
        doc_type: str,
        source: str,
    ) -> int:
        if not chunks:
            return 0
        try:
            vectors = await embed_texts(chunks)
        except Exception as e:
            logger.warning("[kb] embed chunks failed: {}", e)
            return 0

        collection = KB_COLLECTION()
        stored = 0
        for chunk, vec in zip(chunks, vectors):
            if not vec:
                continue
            cid = str(uuid.uuid4())
            self.store.upsert(
                collection=collection,
                point_id=cid,
                vector=vec,
                payload={
                    "point_id": cid,
                    "business_id": business_id,
                    "doc_id": doc_id,
                    "title": title,
                    "doc_type": doc_type,
                    "source": source,
                    "chunk_index": stored,
                    "content": chunk,
                },
            )
            stored += 1
        return stored

    async def _delete_chunks(self, business_id: str, doc_id: str) -> None:
        self.store.delete_by_payload(
            KB_COLLECTION(),
            {"business_id": business_id, "doc_id": doc_id},
        )

    # ── public: file ingestion ───────────────────────────────────
    async def ingest_document(
        self,
        business_id: str,
        file_path: str,
        title: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Optional[KnowledgeDocument]:
        import os
        filename = os.path.basename(file_path)
        title = title or os.path.splitext(filename)[0]

        content = parse_file(file_path)
        if not content.strip():
            logger.warning("[kb] no text extracted from {}", filename)
            return None

        chunks = chunk_text(content)
        doc_id = str(uuid.uuid4())

        session, close = self._session()
        try:
            doc = KnowledgeDocument(
                id=doc_id,
                business_id=business_id,
                title=title,
                content=content,
                doc_type="file",
                source=filename,
                file_path=file_path,
                mime_type=mime_type,
                chunk_count=len(chunks),
            )
            session.add(doc)
            await session.flush()

            stored = await self._store_chunks(business_id, doc_id, chunks, title, "file", filename)
            if stored != len(chunks):
                doc.chunk_count = stored
            if close:
                await session.commit()
            logger.info("[kb] ingested file '{}' -> {} chunks", filename, stored)
            return doc
        except Exception as e:
            logger.error("[kb] ingest_document failed: {}", e)
            if close:
                await session.rollback()
            raise
        finally:
            if close:
                await session.close()

    # ── public: manual text / FAQ ────────────────────────────────
    async def ingest_text(
        self, business_id: str, text: str, title: str = "Manual Entry"
    ) -> Optional[KnowledgeDocument]:
        text = (text or "").strip()
        if not text:
            return None
        chunks = chunk_text(text)
        doc_id = str(uuid.uuid4())

        session, close = self._session()
        try:
            doc = KnowledgeDocument(
                id=doc_id,
                business_id=business_id,
                title=title,
                content=text,
                doc_type="manual",
                source="manual",
                chunk_count=len(chunks),
            )
            session.add(doc)
            await session.flush()
            stored = await self._store_chunks(business_id, doc_id, chunks, title, "manual", "manual")
            doc.chunk_count = stored
            if close:
                await session.commit()
            logger.info("[kb] ingested manual '{}' -> {} chunks", title, stored)
            return doc
        except Exception as e:
            logger.error("[kb] ingest_text failed: {}", e)
            if close:
                await session.rollback()
            raise
        finally:
            if close:
                await session.close()

    # ── public: inventory auto-ingest ────────────────────────────
    async def ingest_inventory(self, business_id: str) -> int:
        """
        Product table se saare active products/services ko knowledge me daalo.
        Pehle existing 'inventory' docs hatao, fir fresh ingest karo (re-index).
        Returns number of products ingested.
        """
        session, close = self._session()
        try:
            # remove old inventory docs + their chunks
            old = await session.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.business_id == business_id,
                    KnowledgeDocument.doc_type == "inventory",
                )
            )
            old_docs = list(old.scalars().all())
            for d in old_docs:
                await self._delete_chunks(business_id, d.id)
                await session.delete(d)

            products_res = await session.execute(
                select(Product).where(
                    Product.business_id == business_id,
                    Product.is_active == True,
                )
            )
            products = list(products_res.scalars().all())
            count = 0
            for p in products:
                # build a descriptive text block per product
                lines = [f"Product/Service: {p.name}"]
                if p.brand:
                    lines.append(f"Brand: {p.brand}")
                if p.model:
                    lines.append(f"Model: {p.model}")
                lines.append(f"Price: ₹{p.price} per {p.unit or 'piece'}")
                if p.stock_quantity is not None:
                    lines.append(f"Stock: {p.stock_quantity} {p.unit or 'piece'}")
                if p.category:
                    lines.append(f"Category: {p.category}")
                if p.description:
                    lines.append(f"Details: {p.description}")
                if p.item_type:
                    lines.append(f"Type: {p.item_type}")
                if p.warranty:
                    lines.append(f"Warranty: {p.warranty}")

                text = "\n".join(lines)
                doc_id = str(uuid.uuid4())
                doc = KnowledgeDocument(
                    id=doc_id,
                    business_id=business_id,
                    title=p.name,
                    content=text,
                    doc_type="inventory",
                    source="inventory",
                    chunk_count=1,
                )
                session.add(doc)
                await self._store_chunks(business_id, doc_id, [text], p.name, "inventory", "inventory")
                count += 1

            if close:
                await session.commit()
            logger.info("[kb] inventory re-indexed: {} products", count)
            return count
        except Exception as e:
            logger.error("[kb] ingest_inventory failed: {}", e)
            if close:
                await session.rollback()
            raise
        finally:
            if close:
                await session.close()

    # ── public: semantic search ──────────────────────────────────
    async def search(
        self, business_id: str, query: str, top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """Top-k relevant knowledge chunks for a query."""
        query = (query or "").strip()
        if not query:
            return []
        try:
            qvec = await embed_query(query)
        except Exception as e:
            logger.warning("[kb] search embed failed: {}", e)
            return []
        results = self.store.search(
            collection=KB_COLLECTION(),
            query_vector=qvec,
            filters={"business_id": business_id},
            limit=top_k,
            score_threshold=SCORE_THRESHOLD,
        )
        # dedupe by content
        seen = set()
        out = []
        for r in results:
            c = r.get("content", "")
            if c and c not in seen:
                seen.add(c)
                out.append({
                    "content": c,
                    "title": r.get("title", ""),
                    "doc_type": r.get("doc_type", ""),
                    "source": r.get("source", ""),
                    "score": r.get("_score", 0.0),
                })
        return out

    async def get_context(self, business_id: str, query: str, top_k: int = 4) -> str:
        """Formatted context string ready to inject into the LLM prompt."""
        results = await self.search(business_id, query, top_k=top_k)
        if not results:
            return ""
        parts = []
        for r in results:
            src = f" [{r['title']}]" if r.get("title") else ""
            parts.append(f"{r['content']}{src}")
        return "\n\n---\n\n".join(parts)

    # ── public: list / delete docs ───────────────────────────────
    async def list_documents(self, business_id: str) -> List[Dict[str, Any]]:
        session, close = self._session()
        try:
            res = await session.execute(
                select(KnowledgeDocument)
                .where(KnowledgeDocument.business_id == business_id)
                .order_by(KnowledgeDocument.created_at.desc())
            )
            docs = res.scalars().all()
            return [
                {
                    "id": d.id,
                    "title": d.title,
                    "doc_type": d.doc_type,
                    "source": d.source,
                    "chunk_count": d.chunk_count,
                    "is_active": d.is_active,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in docs
            ]
        finally:
            if close:
                await session.close()

    async def delete_document(self, business_id: str, doc_id: str) -> bool:
        session, close = self._session()
        try:
            res = await session.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.id == doc_id,
                    KnowledgeDocument.business_id == business_id,
                )
            )
            doc = res.scalar_one_or_none()
            if not doc:
                return False
            await self._delete_chunks(business_id, doc_id)
            await session.delete(doc)
            if close:
                await session.commit()
            return True
        except Exception as e:
            logger.error("[kb] delete failed: {}", e)
            if close:
                await session.rollback()
            raise
        finally:
            if close:
                await session.close()


# Module-level helper
_kb: Optional[KnowledgeBase] = None


def get_knowledge_base(db: Optional[AsyncSession] = None) -> KnowledgeBase:
    """Get a KnowledgeBase instance. Pass db to share the session."""
    return KnowledgeBase(db=db)
