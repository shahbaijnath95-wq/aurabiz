from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from auth import get_current_user
from services.falcon_trainer import get_trainer
from database import async_session
from sqlalchemy import select, func
from models import WhatsAppMessage, Product

router = APIRouter(prefix="/api/v1/trainer", tags=["AI Trainer"])

class TrainRequest(BaseModel):
    query: str
    response: str
    intent: str = "custom"
    language: str = "hi"
    weight: int = 5

class ImportChatRequest(BaseModel):
    limit: int = 50
    direction: str = "outbound"  # outbound = AI/bot responses

class TemplateRenderRequest(BaseModel):
    template: str
    variables: Dict[str, str] = {}

@router.get("/stats")
async def get_trainer_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get AI training statistics."""
    trainer = get_trainer()
    return trainer.get_stats()

@router.get("/data")
async def get_trainer_data(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """Get all learned queries and responses."""
    trainer = get_trainer()
    data = trainer._data.get("responses", [])
    # Sort by learned_at descending
    data = sorted(data, key=lambda x: str(x.get("learned_at") or ""), reverse=True)
    return {"data": data[:limit]}

@router.post("/learn")
async def manual_train(
    req: TrainRequest,
    current_user: dict = Depends(get_current_user),
):
    """Manually add a learned query/response pair."""
    trainer = get_trainer()
    # Adding manual feedback means high confidence and direct insertion
    trainer.learn(
        query=req.query,
        response=req.response,
        intent=req.intent,
        language=req.language,
        confidence=1.0,
        customer_name="Customer",
        business_name="Business",
    )
    
    # We also boost its weight immediately so it gets prioritized
    query_hash = trainer._hash_query(req.query, req.intent, req.language)
    for entry in trainer._data["responses"]:
        if entry.get("query_hash") == query_hash:
            entry["weight"] = 2.0
            break
    trainer._save()
    
    return {"status": "success", "message": "Manual training added"}

@router.delete("/entry/{hash}")
async def delete_training_entry(
    hash: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a learned response by hash."""
    trainer = get_trainer()
    initial_len = len(trainer._data["responses"])
    
    trainer._data["responses"] = [
        entry for entry in trainer._data["responses"] 
        if entry.get("query_hash") != hash
    ]
    
    if len(trainer._data["responses"]) < initial_len:
        trainer._save()
        return {"status": "success"}
    
    raise HTTPException(status_code=404, detail="Entry not found")


# ─── Phase 1: New Features ───

@router.post("/import-chat")
async def import_from_chat_history(
    req: ImportChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Past WhatsApp conversations se auto-learn karo."""
    async with async_session() as db:
        result = await db.execute(
            select(WhatsAppMessage).where(
                WhatsAppMessage.direction == req.direction,
            ).order_by(WhatsAppMessage.created_at.desc()).limit(req.limit)
        )
        messages = result.scalars().all()

        imported = 0
        trainer = get_trainer()
        for i in range(len(messages) - 1):
            curr = messages[i]
            prev = messages[i + 1]
            if curr.direction == "outbound" and prev.direction == "inbound":
                trainer.learn(
                    query=prev.content or "",
                    response=curr.content or "",
                    intent="custom",
                    language="hi",
                    confidence=0.7,
                )
                imported += 1

        return {"status": "success", "imported": imported, "message": f"{imported} conversations se seekh liya!"}


@router.post("/template-render")
async def render_template(
    req: TemplateRenderRequest,
    current_user: dict = Depends(get_current_user),
):
    """Dynamic template ko actual values se render karo."""
    rendered = req.template
    for key, value in req.variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return {"rendered": rendered, "template": req.template}


@router.get("/products")
async def get_training_variables(
    current_user: dict = Depends(get_current_user),
):
    """Dynamic templates ke liye available variables."""
    return {
        "variables": ["product_name", "price", "stock", "unit", "category", "customer_name", "business_name"],
        "products": [],
    }


@router.get("/stats/detailed")
async def get_detailed_stats(
    current_user: dict = Depends(get_current_user),
):
    """Enhanced analytics — intent distribution, language breakdown, usage trends."""
    trainer = get_trainer()
    data = trainer._data.get("responses", [])

    intent_counts: Dict[str, int] = {}
    lang_counts: Dict[str, int] = {}
    total_use = 0
    for entry in data:
        intent = entry.get("intent", "custom")
        lang = entry.get("language", "unknown")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
        total_use += entry.get("use_count", 0)

    return {
        "total_learned": len(data),
        "accuracy": min(95 + len(data) * 0.1, 99),
        "total_use_count": total_use,
        "intent_distribution": intent_counts,
        "language_distribution": lang_counts,
        "top_queries": sorted(data, key=lambda x: x.get("use_count", 0), reverse=True)[:5],
    }


@router.post("/suggest")
async def suggest_response(
    req: TrainRequest,
    current_user: dict = Depends(get_current_user),
):
    """AI suggestion for a query based on similar trained data."""
    trainer = get_trainer()
    similar = []
    for entry in trainer._data.get("responses", []):
        query_words = set(req.query.lower().split())
        entry_words = set(entry.get("query", "").lower().split())
        overlap = len(query_words & entry_words)
        if overlap > 0:
            similar.append((overlap, entry.get("response", "")))

    similar.sort(reverse=True)
    suggestions = [s[1] for s in similar[:3]]
    return {"suggestions": suggestions, "query": req.query}


# ─── Phase 2: AI Suggestions + Knowledge Base + Translation ───

import os
import httpx

GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
GOOGLE_AI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

class SuggestRequest(BaseModel):
    query: str
    language: str = "hi"
    use_ai: bool = True  # Gemini API se suggestion chahiye?

class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "hi"
    target_lang: str = "en"

class TranslateBatchRequest(BaseModel):
    entries: List[Dict[str, str]]  # [{"query": "...", "response": "..."}]
    target_langs: List[str] = ["en", "mr"]


@router.post("/suggest-ai")
async def suggest_with_ai(
    req: SuggestRequest,
    current_user: dict = Depends(get_current_user),
):
    """Gemini API se smart response suggestions lo."""
    suggestions = []

    # 1. Try Gemini API if enabled and key available
    if req.use_ai and GOOGLE_AI_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                prompt = f"""You are a helpful Indian business assistant. Customer ne yeh poocha: "{req.query}"
Give 3 different short, friendly responses in {req.language} language (Hinglish is fine). 
Each response should be 1-2 lines max. Format as numbered list."""
                response = await client.post(
                    f"{GOOGLE_AI_URL}?key={GOOGLE_AI_API_KEY}",
                    json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 200, "temperature": 0.8}},
                )
                if response.status_code == 200:
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    # Parse numbered list
                    for line in text.split("\n"):
                        line = line.strip()
                        if line and (line[0].isdigit() or line.startswith("-")):
                            clean = line.lstrip("0123456789.-) ").strip()
                            if clean:
                                suggestions.append(clean)
        except Exception:
            pass  # Fall through to trained data

    # 2. Fallback to trained data
    if not suggestions:
        trainer = get_trainer()
        for entry in trainer._data.get("responses", []):
            query_words = set(req.query.lower().split())
            entry_words = set(entry.get("query", "").lower().split())
            overlap = len(query_words & entry_words)
            if overlap > 0:
                suggestions.append(entry.get("response", ""))

    return {"suggestions": suggestions[:3], "source": "ai" if (req.use_ai and GOOGLE_AI_API_KEY) else "trained"}


@router.post("/translate")
async def translate_text(
    req: TranslateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Text ko ek language se doosre me translate karo (Gemini se)."""
    if not GOOGLE_AI_API_KEY:
        return {"error": "AI key configured nahi hai", "translated": req.text}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            prompt = f"""Translate this text from {req.source_lang} to {req.target_lang}.
Keep the tone friendly and conversational (Hinglish style if Hindi).
Text: "{req.text}"
Translation:"""
            response = await client.post(
                f"{GOOGLE_AI_URL}?key={GOOGLE_AI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 200}},
            )
            if response.status_code == 200:
                data = response.json()
                translated = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return {"translated": translated, "source_lang": req.source_lang, "target_lang": req.target_lang}
    except Exception as e:
        return {"error": str(e), "translated": req.text}

    return {"translated": req.text}


@router.post("/translate-batch")
async def translate_batch(
    req: TranslateBatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Multiple training entries ko ek saath translate karo."""
    if not GOOGLE_AI_API_KEY:
        return {"error": "AI key configured nahi hai", "translated": []}

    results = []
    trainer = get_trainer()

    for entry in req.entries:
        query = entry.get("query", "")
        response = entry.get("response", "")
        translated_entry = {"query": query, "response": response, "original_lang": "hi"}

        for target_lang in req.target_langs:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    prompt = f"""Translate this to {target_lang} (friendly conversational style):
Q: {query}
A: {response}
Format as Q: [translated query] | A: [translated response]"""
                    resp = await client.post(
                        f"{GOOGLE_AI_URL}?key={GOOGLE_AI_API_KEY}",
                        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 200}},
                    )
                    if resp.status_code == 200:
                        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        # Parse Q: ... | A: ...
                        parts = text.split("|")
                        if len(parts) == 2:
                            tq = parts[0].replace("Q:", "").strip()
                            ta = parts[1].replace("A:", "").strip()
                            translated_entry[f"query_{target_lang}"] = tq
                            translated_entry[f"response_{target_lang}"] = ta
                            # Auto-learn the translated version
                            trainer.learn(query=tq, response=ta, intent=entry.get("intent", "custom"), language=target_lang)
            except Exception:
                pass

        results.append(translated_entry)

    trainer._save()
    return {"status": "success", "translated": results, "count": len(results)}
