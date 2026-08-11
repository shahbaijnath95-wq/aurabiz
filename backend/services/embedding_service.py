"""
Embedding Service - Knowledge Base aur Memory ke liye real vector embeddings.

Primary: Google Gemini `text-embedding-004` (768-dim, free tier).
Fallback: deterministic in-process hashing vector (jab API key/naatak fail ho).

Yeh real semantic search deta hai (meaning match), fake hash vector nahi.
"""

import os
import hashlib
from typing import List, Optional
import httpx
from loguru import logger

from config import settings


GEMINI_EMBEDDING_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"
)
GEMINI_SINGLE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
)

EMBEDDING_DIM = int(getattr(settings, "EMBEDDING_DIM", 768))


def _gemini_key() -> str:
    return (
        getattr(settings, "GOOGLE_AI_API_KEY", "")
        or os.getenv("GOOGLE_AI_API_KEY", "")
    )


def _hash_fallback_vector(text: str) -> List[float]:
    """
    Deterministic fallback vector jab Gemini API available na ho.
    Yeh semantic search itni achhi nahi deta, par system break nahi hota
    aur cosine similarity me stable rehta hai (same text => same vector).
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vec = [float(b) / 255.0 for b in h]
    # 768-dim tak extend (cycle)
    while len(vec) < EMBEDDING_DIM:
        h = hashlib.sha256(h).digest()
        vec.extend(float(b) / 255.0 for b in h)
    return vec[:EMBEDDING_DIM]


async def embed_text(text: str) -> List[float]:
    """Single text ka embedding vector return karta hai."""
    text = (text or "").strip()
    if not text:
        return _hash_fallback_vector("")

    key = _gemini_key()
    model = getattr(settings, "EMBEDDING_MODEL", "text-embedding-004")
    provider = getattr(settings, "EMBEDDING_PROVIDER", "gemini")

    if provider != "gemini" or not key:
        return _hash_fallback_vector(text)

    try:
        url = GEMINI_SINGLE_URL.format(model=model)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                url,
                params={"key": key},
                json={
                    "content": {"parts": [{"text": text}]},
                    "taskType": "RETRIEVAL_DOCUMENT",
                },
            )
        if resp.status_code == 200:
            data = resp.json()
            emb = data.get("embedding", {}).get("values")
            if emb and len(emb) > 0:
                return emb
        logger.warning("[embedding] Gemini single failed: {} - fallback", resp.status_code)
    except Exception as e:
        logger.warning("[embedding] Gemini single error: {} - fallback", e)

    return _hash_fallback_vector(text)


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Batch embedding (zyada efficient API ke liye).
    Gemini batchEmbedContents ek call me multiple texts handle karta hai.
    """
    texts = [(t or "").strip() for t in texts]
    if not texts:
        return []

    key = _gemini_key()
    model = getattr(settings, "EMBEDDING_MODEL", "text-embedding-004")
    provider = getattr(settings, "EMBEDDING_PROVIDER", "gemini")

    if provider != "gemini" or not key:
        return [await embed_text(t) for t in texts]

    # Gemini batch limit ~100 requests; chunks of 50 safe
    results: List[List[float]] = []
    try:
        url = GEMINI_EMBEDDING_URL.format(model=model)
        async with httpx.AsyncClient(timeout=30) as client:
            for i in range(0, len(texts), 50):
                batch = texts[i : i + 50]
                resp = await client.post(
                    url,
                    params={"key": key},
                    json={
                        "requests": [
                            {
                                "model": f"models/{model}",
                                "content": {"parts": [{"text": t}]},
                                "taskType": "RETRIEVAL_DOCUMENT",
                            }
                            for t in batch
                        ]
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    embs = data.get("embeddings", [])
                    for e in embs:
                        vals = e.get("values") or []
                        results.append(vals if vals else _hash_fallback_vector(batch[len(results) % len(batch)]))
                else:
                    logger.warning("[embedding] Gemini batch {} failed: {}", i, resp.status_code)
                    for t in batch:
                        results.append(await embed_text(t))
    except Exception as e:
        logger.warning("[embedding] Gemini batch error: {} - fallback per-text", e)
        return [await embed_text(t) for t in texts]

    # Pad/truncate to fixed dim
    norm = []
    for v in results:
        if len(v) < EMBEDDING_DIM:
            v = v + [0.0] * (EMBEDDING_DIM - len(v))
        norm.append(v[:EMBEDDING_DIM])
    return norm


async def embed_query(text: str) -> List[float]:
    """
    Search query ke liye embedding (RETRIEVAL_QUERY task type).
    Ingestion ke time RETRIEVAL_DOCUMENT use hota hai, search me RETRIVAL_QUERY -
    yeh asymmetry Gemini me relevance improve karti hai.
    """
    text = (text or "").strip()
    key = _gemini_key()
    model = getattr(settings, "EMBEDDING_MODEL", "text-embedding-004")
    provider = getattr(settings, "EMBEDDING_PROVIDER", "gemini")

    if provider != "gemini" or not key:
        return await embed_text(text)

    try:
        url = GEMINI_SINGLE_URL.format(model=model)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                url,
                params={"key": key},
                json={
                    "content": {"parts": [{"text": text}]},
                    "taskType": "RETRIEVAL_QUERY",
                },
            )
        if resp.status_code == 200:
            emb = resp.json().get("embedding", {}).get("values")
            if emb and len(emb) > 0:
                return emb
    except Exception as e:
        logger.warning("[embedding] Gemini query error: {} - fallback", e)

    return await embed_text(text)
