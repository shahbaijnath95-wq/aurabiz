"""
Falcon AI — Hybrid Intelligence Engine
=======================================
Combines Falcon's rule-based classification with real AI response generation.

Pipeline:
1. Falcon classifies intent, extracts entities, detects sentiment
2. Smart prompt built from classification + inventory + history + customer profile
3. Real AI (Gemini → Groq → OpenRouter) generates natural response
4. Falls back to Falcon templates if all AI providers down

Result: Best of both worlds — intelligent classification + natural AI responses.
"""
import os
import httpx
from typing import Optional, Dict, Any

# ─── Import Falcon's classifiers (free, no API key) ───
from services.falcon_engine import get_falcon, _falcon_inner

# ─── AI Provider Config (from settings/env) ───
from config import settings

GOOGLE_AI_API_KEY = settings.GOOGLE_AI_API_KEY or os.getenv("GOOGLE_AI_API_KEY", "")
GOOGLE_AI_MODEL = "gemini-2.5-flash"
GOOGLE_AI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GOOGLE_AI_MODEL}:generateContent"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") or getattr(settings, "GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = getattr(settings, "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")


def _build_ai_prompt(
    message: str,
    intent: str,
    entities: Dict[str, Any],
    sentiment: str,
    inventory: list = None,
    customer_name: str = "Customer",
    business_name: str = "Business",
    conversation_history: list = None,
    payment_context: dict = None,
    knowledge_context: str = None,
    language: str = "hi",
    memory_text: str = "",
) -> list:
    """Build a smart system prompt + conversation for AI based on Falcon's classification."""

    # ─── Inventory context ───
    inventory_text = ""
    if inventory:
        inventory_text = "\n\nAapke paas ye products hain (real-time stock):\n"
        for p in inventory:
            stock_status = "in stock" if p.get("stock", 0) > 0 else "OUT OF STOCK"
            inventory_text += f"- {p['name']}: ₹{p['price']} | Stock: {p.get('stock', 0)} {p.get('unit', 'piece')} ({stock_status})\n"
        inventory_text += "\nSIRF upar diye gaye products mein se batao. Koi naya product mat invent karo."

    # ─── Payment context ───
    payment_text = ""
    if payment_context and payment_context.get("upi_id"):
        payment_text = f"\n\nBUSINESS UPI ID: {payment_context['upi_id']}\nJab customer payment puche to ye UPI ID batao."

    # ─── Knowledge context ───
    knowledge_text = ""
    if knowledge_context and knowledge_context.strip():
        knowledge_text = f"\n\nBUSINESS KNOWLEDGE (official info):\n{knowledge_context.strip()}"

    # ─── Entity hints ───
    entity_hint = ""
    if entities:
        if entities.get("product"):
            entity_hint = f"\n[Customer ne poocha hai: {entities['product']}]"
        if entities.get("quantity"):
            entity_hint += f"\n[Quantity: {entities['quantity']}]"

    # ─── Customer memory (long-term) ───
    memory_section = ""
    if memory_text:
        memory_section = f"\n\n{memory_text}"

    # ─── Build system prompt ───
    system_prompt = f"""You are {business_name}'s AI assistant. Customer ka naam {customer_name} hai.
Sentiment: {sentiment}
Intent: {intent}{entity_hint}

RULES:
1. HAMESHA Hinglish mein reply karo (Hindi + English mix) — chahe customer kisi bhi language mein bole
2. SIRF business ke products/services ke baare mein baat karo
3. Short reply rakho (2-3 lines max)
4. Customer ka naam use karo
5. Agar product available nahi hai toh politely batao
6. Price fixed hai — negotiation mat karo
7. Jab customer order kare toh confirm karo
8. Agar customer purana hai toh uske past orders ke hisaab se personalize karo

{inventory_text}{payment_text}{knowledge_text}{memory_section}"""

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history (last 5 messages)
    if conversation_history:
        for msg in conversation_history[-5:]:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": message})
    return messages


async def _call_gemini(messages: list) -> Optional[str]:
    """Call Google Gemini API."""
    if not GOOGLE_AI_API_KEY:
        return None
    try:
        # Extract system prompt + build Gemini contents
        system_text = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        contents = []
        for msg in messages[1:]:
            if msg["role"] == "system":
                continue
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GOOGLE_AI_URL + f"?key={GOOGLE_AI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "systemInstruction": {"parts": [{"text": system_text}]},
                    "contents": contents,
                    "generationConfig": {"maxOutputTokens": 200, "temperature": 0.7},
                },
            )
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text if len(text) > 3 else None
            else:
                print(f"Falcon AI → Gemini error: {response.status_code}")
    except Exception as e:
        print(f"Falcon AI → Gemini exception: {e}")
    return None


async def _call_groq(messages: list) -> Optional[str]:
    """Call Groq API (fastest free inference)."""
    if not GROQ_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GROQ_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 150,
                    "temperature": 0.7,
                },
            )
            if response.status_code == 200:
                data = response.json()
                reply = data["choices"][0]["message"]["content"].strip()
                return reply if len(reply) > 3 else None
            else:
                print(f"Falcon AI → Groq error: {response.status_code}")
    except Exception as e:
        print(f"Falcon AI → Groq exception: {e}")
    return None


async def _call_openrouter(messages: list) -> Optional[str]:
    """Call OpenRouter API."""
    if not OPENROUTER_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost:3001",
                    "X-Title": "AuraBiz AI Assistant",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": messages,
                    "max_tokens": 200,
                    "temperature": 0.7,
                },
            )
            if response.status_code == 200:
                data = response.json()
                reply = data["choices"][0]["message"]["content"].strip()
                return reply if len(reply) > 3 else None
            else:
                print(f"Falcon AI → OpenRouter error: {response.status_code}")
    except Exception as e:
        print(f"Falcon AI → OpenRouter exception: {e}")
    return None


async def falcon_ai_reply(
    message: str,
    customer_name: str = "Customer",
    business_name: str = "Business",
    business_type: str = "general",
    inventory: list = None,
    conversation_history: list = None,
    payment_context: dict = None,
    knowledge_context: str = None,
    language: str = "hi",
    session_id: str = None,
    customer_id: str = None,
) -> str:
    """
    AI-Powered Falcon Reply.

    1. Falcon classifies intent, extracts entities, detects sentiment
    2. Smart prompt built from classification
    3. Real AI (Gemini → Groq → OpenRouter) generates natural response
    4. Falls back to Falcon templates if all AI providers down
    """

    # ─── Step 1: Falcon classification (free, instant) ───
    engine = get_falcon()
    corrected = engine.fuzzy.correct(message)
    intent, confidence = engine.intent.classify(corrected)
    sentiment, _ = engine.sentiment.detect(message)
    entities = engine.entity.extract(corrected, inventory)

    # ─── Step 2: Build smart prompt (with customer memory) ───
    memory_text = ""
    if customer_id:
        try:
            from services.customer_memory import get_customer_memory, build_memory_prompt_section
            cm = get_customer_memory()
            memory_data = await cm.get_memory(business_id=business_id, customer_id=customer_id)
            memory_text = build_memory_prompt_section(memory_data)
        except Exception:
            pass  # Memory failure should never break the chat

    messages = _build_ai_prompt(
        message=message,
        intent=intent,
        entities=entities,
        sentiment=sentiment,
        inventory=inventory,
        customer_name=customer_name,
        business_name=business_name,
        conversation_history=conversation_history,
        payment_context=payment_context,
        knowledge_context=knowledge_context,
        language=language,
        memory_text=memory_text,
    )

    # ─── Step 3: Try AI providers in order ───

    # Try Gemini (1500/day free)
    reply = await _call_gemini(messages)
    if reply:
        return reply

    # Try Groq (14400/day free, fastest)
    reply = await _call_groq(messages)
    if reply:
        return reply

    # Try OpenRouter (50/day free)
    reply = await _call_openrouter(messages)
    if reply:
        return reply

    # ─── Step 4: Fallback to Falcon templates (always works) ───
    return _falcon_inner(
        message=message,
        customer_name=customer_name,
        inventory_context=inventory,
        payment_context=payment_context,
        knowledge_context=knowledge_context,
        business_name=business_name,
    )
