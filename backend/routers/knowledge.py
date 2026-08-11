"""
Knowledge Base RAG — Document upload se AI ko business knowledge sikhao.
Documents upload karo → Chunk karo → Embed karo → Query karo → AI answers deta hai.
"""
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy import select

from auth import get_current_user, verify_business_access
from database import async_session
from models import KnowledgeDocument

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Base"])

# In-memory storage for chunks (production me Qdrant/Postgres use karo)
_knowledge_chunks: List[Dict[str, Any]] = []


async def _check_business_access(current_user, business_id: str) -> None:
    """Verify the user owns the business — 403 otherwise. Empty business_id = no check."""
    if not business_id:
        return
    async with async_session() as db:
        if not await verify_business_access(current_user, business_id, db):
            raise HTTPException(status_code=403, detail="Access denied")


class DocumentResponse(BaseModel):
    id: str
    title: str
    file_type: str
    chunk_count: int
    created_at: str


class QueryRequest(BaseModel):
    query: str
    top_k: int = 3


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    business_id: str = "",
    current_user: dict = Depends(get_current_user),
):
    """Document upload karo (PDF, DOCX, TXT) → chunk → embed → store."""
    await _check_business_access(current_user, business_id)
    import tempfile
    content = await file.read()

    # Save to temp file for document parser
    suffix = os.path.splitext(file.filename)[1] or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    # Parse using document_parser service
    try:
        from services.document_parser import parse_file, chunk_text
        text = parse_file(tmp_path)
        chunks = chunk_text(text)
    except Exception as e:
        # Fallback for TXT files
        text = content.decode("utf-8", errors="ignore")
        chunks = [c.strip() for c in text.split("\n\n") if c.strip() and len(c.strip()) > 20]
    finally:
        os.unlink(tmp_path)  # cleanup

    doc_id = str(uuid.uuid4())
    for chunk in chunks:
        _knowledge_chunks.append({
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "title": title or file.filename,
            "text": chunk,
            "business_id": business_id,
            "created_at": datetime.utcnow().isoformat(),
        })

    return {
        "status": "success",
        "document_id": doc_id,
        "title": title or file.filename,
        "chunk_count": len(chunks),
        "message": f"{len(chunks)} chunks me process ho gaya!",
    }


@router.get("/documents")
async def list_documents(
    business_id: str = "",
    current_user: dict = Depends(get_current_user),
):
    """Saare uploaded documents list karo."""
    await _check_business_access(current_user, business_id)
    docs: Dict[str, Any] = {}
    for chunk in _knowledge_chunks:
        if chunk["business_id"] == business_id or not business_id:
            doc_id = chunk["document_id"]
            if doc_id not in docs:
                docs[doc_id] = {"id": doc_id, "title": chunk["title"], "chunk_count": 0}
            docs[doc_id]["chunk_count"] += 1

    return {"documents": list(docs.values())}


@router.post("/query")
async def query_knowledge_base(
    req: QueryRequest,
    business_id: str = "",
    current_user: dict = Depends(get_current_user),
):
    """Knowledge base se relevant chunks nikal aur AI se jawab bana."""
    await _check_business_access(current_user, business_id)
    # Simple keyword search (production me vector similarity use karo)
    query_words = set(req.query.lower().split())
    scored = []
    for chunk in _knowledge_chunks:
        if business_id and chunk.get("business_id") != business_id:
            continue
        chunk_words = set(chunk["text"].lower().split())
        overlap = len(query_words & chunk_words)
        if overlap > 0:
            scored.append((overlap, chunk["text"]))

    scored.sort(reverse=True, key=lambda x: x[0])
    relevant_chunks = [s[1] for s in scored[:req.top_k]]

    answer = ""
    if relevant_chunks:
        context = "\n".join(relevant_chunks)
        # Use Gemini to generate answer
        google_key = os.getenv("GOOGLE_AI_API_KEY", "")
        if google_key:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=15.0) as client:
                    prompt = f"""Based on this business information, answer the customer's question in friendly Hinglish:
Business Info: {context}
Question: {req.query}
Answer (short, 2-3 lines):"""
                    resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={google_key}",
                        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 200}},
                    )
                    if resp.status_code == 200:
                        answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                pass

    return {
        "answer": answer,
        "sources": [{"text": c[:100] + "..."} for c in relevant_chunks],
        "chunks_found": len(relevant_chunks),
    }


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Document delete karo."""
    global _knowledge_chunks
    doc_business = next((c.get("business_id", "") for c in _knowledge_chunks if c.get("document_id") == doc_id), "")
    await _check_business_access(current_user, doc_business)
    initial = len(_knowledge_chunks)
    _knowledge_chunks = [c for c in _knowledge_chunks if c["document_id"] != doc_id]
    deleted = initial - len(_knowledge_chunks)
    return {"status": "success", "deleted_chunks": deleted}
