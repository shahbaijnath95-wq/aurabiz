"""
Free AI Service - OpenCode + Cloudflare + Gemini + Groq
OpenCode: Free, keyless, deepseek-v4-flash-free (200K context)
Cloudflare Workers AI: Free, llama-4-scout
Google Gemini: Free, gemini-2.5-flash
Groq: Free, llama-3.1-8b-instant
"""

import os
import sys
import re
import httpx
import json
import hashlib
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone


def _deterministic_id(seed: str, mod: int = 10000) -> int:
    """Deterministic ID from seed using md5 (stable across restarts, unlike hash())."""
    h = hashlib.md5(seed.encode()).hexdigest()
    return int(h, 16) % mod

# Make the project root importable so `master` (sibling package) can be reached
# for platform-level AI key fallback. Without this, the import below fails
# silently and the master DB fallback never engages.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config import settings

# ─── Load AI keys from .env first ───
GOOGLE_AI_API_KEY = getattr(settings, "GOOGLE_AI_API_KEY", "") or os.getenv("GOOGLE_AI_API_KEY", "")
GOOGLE_AI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GOOGLE_AI_MODEL = "gemini-2.5-flash"  # Free, fast, good at Hinglish

OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY or os.getenv("OPENROUTER_API_KEY", "")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") or getattr(settings, "GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # Free, 14400 req/day, follows Hinglish better than 70B

CLOUDFLARE_ACCOUNT_ID = getattr(settings, "CLOUDFLARE_ACCOUNT_ID", "") or os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = getattr(settings, "CLOUDFLARE_API_TOKEN", "") or os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_MODEL = getattr(settings, "CLOUDFLARE_MODEL", "") or os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-4-scout-17b-16e-instruct")
CLOUDFLARE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_MODEL}" if CLOUDFLARE_ACCOUNT_ID else ""

# ─── OpenCode Free AI via OmniRoute Gateway ───
# OmniRoute proxies to OpenCode's free models — no API key needed
OPENCODE_ENABLED = os.getenv("OPENCODE_ENABLED", "true").lower() == "true"
OPENCODE_URL = os.getenv("OPENCODE_URL", "http://localhost:3000/v1/chat/completions")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "oc/deepseek-v4-flash-free")

# ─── Fallback: Load platform AI keys from master DB (if .env keys not set) ───
_platform_keys_loaded = False
def _load_platform_keys():
    """Load AI keys from master database as fallback."""
    global _platform_keys_loaded, GOOGLE_AI_API_KEY, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, CLOUDFLARE_MODEL, GROQ_API_KEY, OPENROUTER_API_KEY, OPENCODE_URL, OPENCODE_MODEL, OPENCODE_ENABLED
    if _platform_keys_loaded:
        return
    _platform_keys_loaded = True
    try:
        from master.services.platform_ai import get_platform_ai_config
        platform = get_platform_ai_config()
        if "cloudflare" in platform and not CLOUDFLARE_API_TOKEN:
            cf = platform["cloudflare"]
            CLOUDFLARE_API_TOKEN = cf.get("api_key", "")
            CLOUDFLARE_ACCOUNT_ID = cf.get("account_id", "")
            if cf.get("model"):
                CLOUDFLARE_MODEL = cf["model"]
        if "gemini" in platform and not GOOGLE_AI_API_KEY:
            GOOGLE_AI_API_KEY = platform["gemini"].get("api_key", "")
        if "groq" in platform and not GROQ_API_KEY:
            GROQ_API_KEY = platform["groq"].get("api_key", "")
        if "openrouter" in platform and not OPENROUTER_API_KEY:
            OPENROUTER_API_KEY = platform["openrouter"].get("api_key", "")
        if "opencode" in platform:
            oc = platform["opencode"]
            OPENCODE_MODEL = oc.get("model", OPENCODE_MODEL)
            OPENCODE_ENABLED = True
    except Exception:
        pass  # Platform keys not available, use .env keys

_load_platform_keys()


# Language-specific translations for common phrases
LANG_MAP = {
    "hi": {" avail": " available hai", "price": "price", "stock": "stock", "order": "order", "sorry": "sorry", "chahiye": "chahiye"},
    "en": {" avail": " is available", "price": "price", "stock": "stock", "order": "order", "sorry": "sorry", "chahiye": "want"},
    "mr": {
        "hamare paas hai": "amchya kade aahe",
        "available hain": "available ahet",
        "bache hain": "shesh ahet",
        "Price:": "Kimmat:",
        "Stock:": "Stock:",
        "Order karna ho toh bolo:": "Order karaycha asel tar sanga:",
        "kitne chahiye?": "kitle pahije?",
        "Kitne chahiye?": "Kitle pahije?",
        "ka price": "chi kimmat",
        "hai!": "aahe!",
        "sorry!": "maaf kara!",
        "ke baare mein baat kar sakta hoon.": "babatit bolu shakto.",
        "Aapko hamare products ya services ke baare mein kuch jaanna hai?": "Tumhala amche products kiva services babatit kahitari havay?",
    },
    "gu": {
        "hamare paas hai": "apde pase chhiye",
        "available hain": "available chhe",
        "bache hain": "bachya chhe",
        "Price:": "Bhav:",
        "Stock:": "Stock:",
        "Order karna ho toh bolo:": "Order karvo hoy toh bolo:",
        "kitne chahiye?": "ketla joiye?",
        "Kitne chahiye?": "Ketla joiye?",
        "ka price": "no bhav",
        "hai!": "chhe!",
        "sorry!": "maaf karo!",
        "ke baare mein baat kar sakta hoon.": "vaare main vaat karu shaku chhu.",
        "Aapko hamare products ya services ke baare mein kuch jaanna hai?": "Tame amna products or services vaare kai janvu chho?",
    },
    "ta": {
        "hamare paas hai": "engalukku irukku",
        "available hain": "kidaikum",
        "bache hain": "migundhirukku",
        "Price:": "Vilai:",
        "Stock:": "Stock:",
        "Order karna ho toh bolo:": "Order seidhalum solunga:",
        "kitne chahiye?": "evvalavu venum?",
        "Kitne chahiye?": "Evvalavu venum?",
        "hai!": "irukku!",
        "sorry!": "mannikavum!",
    },
    "te": {
        "hamare paas hai": "memandiki unnadi",
        "available hain": "labhistundi",
        "bache hain": "migili unnayi",
        "Price:": "Dhara:",
        "Stock:": "Stock:",
        "Order karna ho toh bolo:": "Order cheyyalante cheppandi:",
        "kitne chahiye?": "entha kavali?",
        "hai!": "undi!",
        "sorry!": "kshaminchandi!",
    },
    "bn": {
        "hamare paas hai": "amader kache ache",
        "available hain": "pawa jay",
        "bache hain": "baki ache",
        "Price:": "Dam:",
        "Stock:": "Stock:",
        "Order karna ho toh bolo:": "Order korle bolo:",
        "kitne chahiye?": "koto lagbe?",
        "hai!": "ache!",
        "sorry!": "dukhito!",
    },
}


def translate_response(text: str, lang: str) -> str:
    """Translate Hinglish response to target language using phrase replacement."""
    if lang == "hi" or lang not in LANG_MAP:
        return text  # Hinglish default

    result = text
    translations = LANG_MAP[lang]

    # Sort by length (longest first) to avoid partial replacements
    # Use word boundary matching to avoid replacing substrings inside words
    for eng, local in sorted(translations.items(), key=lambda x: -len(x[0])):
        # Only replace whole words/phrases, not substrings
        result = re.sub(r'\b' + re.escape(eng) + r'\b', local, result)

    return result


def detect_language(text: str) -> str:
    """Detect customer language from text.

    Delegates to the canonical implementation in services.language_service
    so every entry point (chat router, free_ai, falcon engine) uses one
    consistent detector instead of divergent copies.
    """
    from .language_service import detect_language as _detect
    return _detect(text)


# Language-specific system prompt additions
LANGUAGE_INSTRUCTIONS = {
    "hi": "Customer HINDI/HINGLISH mein baat kar raha hai. Tum bhi HINGLISH mein jawaab do (Hindi words English script mein).",
    "en": "Customer is writing in ENGLISH. Reply in ENGLISH only.",
    "mr": "Customer MARATHI mein baat kar raha hai. Tum bhi MARATHI mein jawaab do. Marathi words use karo jaise 'aahe', 'chhe', 'kay', 'kiti'.",
    "gu": "Customer GUJARATI mein baat kar raha hai. Tum bhi GUJARATI mein jawaab do. Gujarati words use karo jaise 'chhe', 'kitla', 'chhiye', 'shu'.",
    "bn": "Customer BENGALI mein baat kar raha hai. Tum bhi BENGALI mein jawaab do.",
    "ta": "Customer TAMIL mein baat kar raha hai. Tum bhi TAMIL mein jawaab do.",
    "te": "Customer TELUGU mein baat kar raha hai. Tum bhi TELUGU mein jawaab do.",
}
OPENROUTER_MODEL = settings.OPENROUTER_MODEL or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def call_opencode(messages: list, model: str = None, max_tokens: int = 500) -> Optional[str]:
    """Call OpenCode Free AI via OmniRoute gateway — no API key needed.
    
    OmniRoute proxies requests to OpenCode's free models:
    - no-think/oc/deepseek-v4-flash-free (fast, 200K, reasoning suppressed)
    - no-think/oc/big-pickle (reasoning suppressed)
    - no-think/oc/minimax-m3-free (vision, 1M)
    - no-think/oc/qwen3.6-plus-free (code, 200K)
    
    'no-think' prefix suppresses reasoning output → content returned directly.
    Reasoning models need max_tokens >= 500 (reasoning uses tokens before content).
    """
    if not OPENCODE_ENABLED:
        return None
    
    model = model or OPENCODE_MODEL
    # Use no-think prefix to suppress reasoning output
    if not model.startswith("no-think/"):
        model = f"no-think/{model}"
    
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                OPENCODE_URL,
                headers={
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False,
                },
            )
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and data["choices"]:
                    msg = data["choices"][0].get("message", {})
                    reply = (msg.get("content") or "").strip()
                    if reply and len(reply) > 3:
                        return reply
            else:
                print(f"OpenCode Error: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"OpenCode Error: {e}")
    return None


async def get_ai_reply_free(
    message: str,
    business_name: str = "aapka business",
    business_type: str = "general",
    customer_name: str = "Customer",
    business_id: str = None,
    customer_id: str = None,
    conversation_history: list = None,
    inventory_context: list = None,
    last_qty: int = None,
    payment_context: dict = None,
    knowledge_context: str = None,
    customer_memory: dict = None,
    ai_provider_settings: dict = None,
    language: str = None,
) -> str:
    """
    Free AI model se reply generate karta hai.
    OpenRouter ke free models use karte hain.

    knowledge_context : Knowledge Base (RAG) se relevant chunks (policies, FAQ, etc.)
    customer_memory   : {"facts": [...], "recent_similar": [...]} per-customer long-term memory
    """

    system_prompt = f"""You are an AI assistant for {business_name}.

LANGUAGE MATCHING RULE (HIGHEST PRIORITY - MUST FOLLOW):
You MUST reply in the EXACT SAME language as the customer's message.
If customer writes in Hindi → reply in Hindi ONLY.
If customer writes in English → reply in English ONLY.
If customer writes in Marathi → reply in Marathi ONLY.
If customer writes in Gujarati → reply in Gujarati ONLY.

Examples:
- Customer: "Mouse chha ahe" (Marathi) → Reply in Marathi: "{customer_name}, Mouse available ahe! Price ₹350 ahe."
- Customer: "Mouse chhiye" (Gujarati) → Reply in Gujarati: "{customer_name}, Mouse chhiye! Price ₹350 chhe."
- Customer: "Do you have mouse?" (English) → Reply in English: "Yes {customer_name}, Mouse is available! Price is ₹350."
- Customer: "Mujhe mouse chahiye" (Hindi) → Reply in Hindi: "{customer_name}, Mouse hai! Price ₹350 hai."

OTHER RULES:
- NEVER tell jokes, songs, stories. Politely refuse.
- ONLY talk about business products and services.
- Use EXACT product names from inventory. Never invent names.
- Keep replies short (2-3 lines).
- ALWAYS use the customer's name (provided in the message context) in your reply."""

    # Agar inventory data hai toh system prompt mein add karo
    if inventory_context:
        system_prompt += "\n\nAapke paas ye products hain (real-time stock):"
        for p in inventory_context:
            stock_status = "in stock" if p["stock"] > 0 else "OUT OF STOCK"
            system_prompt += f"\n- {p['name']}: ₹{p['price']} | Stock: {p['stock']} {p['unit']} ({stock_status}) | Category: {p['category']}"
        system_prompt += """
\nPRODUCT RULES:
- SIRF upar diye gaye products batao — koi naya naam ya brand MAT invent karo
- Price FIXED hai — negotiation mat karo. Customer kam bole toh "Maaf karo, price fixed hai."
- Stock kam hai (<5) toh "jaldi order kar lo" bolo
- Product nahi mila toh "ye abhi available nahi hai" bolo
- Jab customer lena chahe toh "Order karne ke liye bolo: ORDER" bolo"""

    # Detect customer language and add instruction LAST (models pay more attention to last instruction)
    # Use business preferred language if provided, else detect from message
    detected_lang = language if language else detect_language(message)
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(detected_lang, LANGUAGE_INSTRUCTIONS["hi"])
    system_prompt += f"\n\nFINAL CRITICAL RULE (NON-NEGOTIABLE): {lang_instruction} REPLY IN THIS LANGUAGE ONLY. DO NOT USE ANY OTHER LANGUAGE. Customer name is '{customer_name}' — use it in your reply."

    # Knowledge Base (RAG) context - business ke documents/policies/FAQ
    if knowledge_context and knowledge_context.strip():
        system_prompt += "\n\n" + "=" * 40
        system_prompt += "\nBUSINESS KNOWLEDGE (yeh business ki official information hai - inka use karo):"
        system_prompt += "\n" + knowledge_context.strip()
        system_prompt += "\n" + "=" * 40
        system_prompt += """
\nKNOWLEDGE RULES:
- Agar customer ka sawal upar di gayi KNOWLEDGE se related hai (return policy, warranty, timings, FAQ, etc.),
  toh SIRF yeh knowledge use karke answer do.
- Knowledge mein jo likha hai wahi bolo - mat guess karo, mat invent karo.
- Agar knowledge mein answer nahi hai, toh honestly bolo "is baare me mujhe confirm karna padega"."""

    # Customer long-term memory (facts + recent similar)
    if customer_memory:
        facts = customer_memory.get("facts") or []
        recent = customer_memory.get("recent_similar") or []
        if facts:
            system_prompt += "\n\nIS CUSTOMER KE BAARE ME JAANKARI (yaad rakho, personalize karo):"
            for f in facts[:8]:
                if f:
                    system_prompt += f"\n- {f}"
            system_prompt += "\n(In facts ko natural tareeke se use karo - repeat mat karo verbatim.)"
        if recent:
            system_prompt += "\n\nIS CUSTOMER SE PICHCHLI SAMBANDHIT BAAT-CHEET:"
            for r in recent[:3]:
                m = (r.get("message") or "").strip()
                if m:
                    system_prompt += f"\n- Pehle pucha tha: \"{m[:200]}\""
            system_prompt += "\n(Agar current sawal pichli baat se related ho, toh context use karo.)"

    # ── Structured customer memory (orders, preferences, tier) ──
    if customer_id and business_id:
        try:
            from services.customer_memory import get_customer_memory, build_memory_prompt_section
            cm = get_customer_memory()
            memory_data = await cm.get_memory(business_id=business_id, customer_id=customer_id)
            memory_section = build_memory_prompt_section(memory_data)
            if memory_section:
                system_prompt += f"\n\n{memory_section}"
        except Exception:
            pass

    # Payment info
    if payment_context and payment_context.get("upi_id"):
        system_prompt += f"\n\nBUSINESS UPI ID: {payment_context['upi_id']}"
        system_prompt += "\nJab customer UPI/payment ke baare mein puche to ye UPI ID share karo."

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    if conversation_history:
        for msg in conversation_history[-5:]:  # Last 5 messages
            messages.append(msg)

    messages.append({"role": "user", "content": message})

    # --- PRE-CHECK: Non-business requests ko AI tak mat bhejo ---
    non_business_keywords = [
        "joke", "jokes", "sunao", "suno", "haha", "funny", "mazak", "mazaak",
        "gaana", "song", "music", "gao", "gaau", "poem", "kavita", "shayari",
        "story", "kahani", "kahaani",
        "weather", "mausam", "samachar", "news", "cricket", "match",
        "translate", "matlab", "meaning", "spell"
    ]
    msg_lower = message.lower().strip()
    if any(w in msg_lower for w in non_business_keywords):
        return (f"{customer_name}, sorry! Main sirf business ke baare mein baat kar sakta hoon. 😊\n"
                f"Aapko hamare products ya services ke baare mein kuch jaanna hai?")

    # --- TRY 0: OpenCode Free AI via OmniRoute (no API key needed) ---
    if OPENCODE_ENABLED:
        opencode_reply = await call_opencode(messages=messages, max_tokens=500)
        if opencode_reply:
            return opencode_reply

    # --- TRY 0.5: Cloudflare Workers AI (FREE - 10K neurons/day) ---
    # IMPORTANT: Free accounts use /ai/run/{model} endpoint — NOT /ai/v1/chat/completions
    cf_account = CLOUDFLARE_ACCOUNT_ID
    cf_token = CLOUDFLARE_API_TOKEN
    cf_model = CLOUDFLARE_MODEL
    # Override from DB settings if provider is cloudflare
    if ai_provider_settings and ai_provider_settings.get("provider") == "cloudflare":
        api_key_raw = ai_provider_settings.get("api_key", "")
        if ":" in api_key_raw:
            cf_account, cf_token = api_key_raw.split(":", 1)
        if ai_provider_settings.get("model"):
            cf_model = ai_provider_settings["model"]
    if cf_token and cf_account:
        cf_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run/{cf_model}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    cf_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {cf_token}",
                    },
                    json={
                        "messages": messages,
                        "max_tokens": 200,
                        "temperature": 0.7,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("result"):
                        result = data["result"]
                        # /ai/run/ returns {"result": {"response": "..."}} or {"result": {"choices": [...]}}
                        if isinstance(result, dict):
                            if "response" in result:
                                reply = result["response"].strip()
                            elif "choices" in result:
                                reply = result["choices"][0]["message"]["content"].strip()
                            else:
                                reply = str(result).strip()
                        else:
                            reply = str(result).strip()
                        if reply and len(reply) > 5:
                            return reply
                else:
                    print(f"Cloudflare Error: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"Cloudflare Error: {e}")

    # --- TRY 1: Google Gemini (FREE - 1500 RPD) ---
    if GOOGLE_AI_API_KEY:
        try:
            # For non-Hindi/English, use minimal prompt to force language matching
            if detected_lang not in ("hi", "en"):
                gemini_lang_system = f"""You are {business_name} ka assistant.
REPLY ONLY IN {detected_lang.upper()} LANGUAGE. This is the ONLY rule.
Products: {', '.join([f"{p['name']} = Rs{p['price']}" for p in (inventory_context or [])])}
Be short and helpful. Include customer name."""
                gemini_contents = [{"role": "user", "parts": [{"text": message}]}]
            else:
                gemini_lang_system = system_prompt
                gemini_contents = []
                if conversation_history:
                    for msg in conversation_history[-5:]:
                        role = "user" if msg["role"] == "user" else "model"
                        gemini_contents.append({"role": role, "parts": [{"text": msg["content"]}]})
                gemini_contents.append({"role": "user", "parts": [{"text": message}]})

            # Retry up to 2 times for 503 (temporary overload)
            import asyncio as _asyncio
            for _attempt in range(2):
                async with httpx.AsyncClient(timeout=15.0) as client:
                    url = GOOGLE_AI_URL.format(model=GOOGLE_AI_MODEL) + f"?key={GOOGLE_AI_API_KEY}"
                    response = await client.post(
                        url,
                        headers={"Content-Type": "application/json"},
                        json={
                            "systemInstruction": {"parts": [{"text": gemini_lang_system}]},
                            "contents": gemini_contents,
                            "generationConfig": {"maxOutputTokens": 200, "temperature": 0.7},
                        },
                    )
                    if response.status_code == 200:
                        data = response.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        return text
                    elif response.status_code in (503, 429):
                        print(f"Gemini {_attempt+1}/2: {response.status_code} - retrying...")
                        await _asyncio.sleep(1)
                        continue
                    else:
                        print(f"Gemini Error: {response.status_code} - {response.text[:200]}")
                        break
        except Exception as e:
            print(f"Gemini Error: {e}")

    # --- TRY 1.5: Groq (FREE - 14400 RPD, fastest inference) ---
    if GROQ_API_KEY:
        try:
            # Short, focused prompt for Llama — forces Hinglish + inventory-only
            groq_system = f"""Tu {business_name} ka shop assistant hai. Customer ka naam {customer_name} hai.
RULES:
1. HAMESHA Hinglish mein reply kar — chahe customer English mein bole ya Hindi mein. NO ENGLISH ONLY REPLIES.
2. SIRF diye gaye inventory mein se hi products bol. KABHI naya product, brand, ya model mat invent kar.
3. Agar inventory mein nahi hai toh bol "Sorry, wo abhi available nahi hai"
4. Reply SHORT rakhi — 2-3 lines max.
5. Apna naam SIRF business name bol — koi aur naam mat invent kar.

EXAMPLES (HINGLISH replies — ye yaad rakh):
- Customer: "Hello" → Reply: "Namaste {customer_name}! {business_name} mein aapka swagat hai. Kya chahiye?"
- Customer: "What is the price?" → Reply: "{customer_name}, price batane ke liye product batao kaun sa chahiye?"
- Customer: "Do you have mouse?" → Reply: "{customer_name}, Mouse available hai! Price Rs350. Kitne chahiye?"
- Customer: "Thank you" → Reply: "{customer_name}, aapka swagat hai! Aur kuch chahiye toh bolo."
- Customer: "Hi" → Reply: "Namaste {customer_name}! Kya aapko kuch chahiye?"
- Customer: "Upi" or "Payment" or "Paisa" → Reply: "Aap UPI app mein ye UPI ID use karke payment kar sakte ho: {payment_context.get('upi_id','business@upi') if payment_context else 'business@upi'}
"""
            if inventory_context:
                groq_system += "\n\nYeh actual inventory hai (real-time data):"
                for p in inventory_context:
                    status = "in stock" if p["stock"] > 0 else "OUT OF STOCK"
                    groq_system += f"\n- {p['name']}: Rs {p['price']} | Stock: {p['stock']} ({status}) | Category: {p['category']}"
                groq_system += "\n\nSIRF upar diye gaye inventory se prices lo. Kabhi mat banaao."
            if payment_context and payment_context.get("upi_id"):
                groq_system += f"\nBUSINESS UPI ID: {payment_context['upi_id']}\nJab customer UPI/payment puche to ye UPI ID batao."
            groq_messages = [{"role": "system", "content": groq_system}]
            if conversation_history:
                for msg in conversation_history[-3:]:
                    groq_messages.append({"role": msg["role"], "content": msg["content"]})
            groq_messages.append({"role": "user", "content": message})

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    GROQ_URL,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "User-Agent": "WhatsApp-Bot/1.0",
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": groq_messages,
                        "max_tokens": 150,
                        "temperature": 0.5,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    reply = data["choices"][0]["message"]["content"].strip()
                    return reply
                else:
                    print(f"Groq Error: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"Groq Error: {e}")

    # --- TRY 2: OpenRouter (FREE - 50 RPD) ---
    if OPENROUTER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "HTTP-Referer": "http://localhost:3001",
                        "X-Title": "WhatsApp Business Assistant",
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
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    print(f"OpenRouter Error: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"OpenRouter Error: {e}")

    # --- TRY 3: Falcon AI — Hybrid Intelligence (Falcon classification + AI response) ---
    try:
        from services.falcon_ai import falcon_ai_reply
        ai_reply = await falcon_ai_reply(
            message=message,
            customer_name=customer_name,
            business_name=business_name,
            inventory=inventory_context,
            conversation_history=conversation_history,
            payment_context=payment_context,
            knowledge_context=knowledge_context,
            language=language,
        )
        if ai_reply:
            return ai_reply
    except Exception as e:
        print(f"Falcon AI Error: {e}")

    # --- TRY 4: Legacy Falcon templates (always works fallback) ---
    return falcon_reply(message, customer_name, inventory_context, last_qty=last_qty, business_name=business_name, payment_context=payment_context)


def extract_date_time(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Message se date aur time extract karo."""
    msg = text.lower().strip()
    date_val = None
    time_val = None

    # ── DATE detection ──
    # Relative day words are resolved to actual ISO dates so bookings store a
    # real calendar date instead of literals like "kal"/"aaj".
    from datetime import timedelta
    today = datetime.now()
    weekday_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }

    def _resolve_weekday(name: str) -> str:
        target = weekday_map[name]
        days_ahead = (target - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # next week, not today
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    if "aaj" in msg or "today" in msg or "aaj hi" in msg:
        date_val = today.strftime("%Y-%m-%d")
    elif "kal" in msg or "tomorrow" in msg or "aane wala kal" in msg or "aane wala kl" in msg:
        date_val = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        for name in weekday_map:
            if name in msg or f"agle {name}" in msg or f"agla {name}" in msg:
                date_val = _resolve_weekday(name)
                break
    if not date_val:
        # Check date patterns like "15 July", "15/07", "15 july ko"
        date_match = re.search(r'(\d{1,2})\s*(july|august|september|october|november|december|january|february|march|april|may|june|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)', msg)
        if date_match:
            day = int(date_match.group(1))
            month_names = ["january","february","march","april","may","june","july","august","september","october","november","december"]
            abbr = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
            raw = date_match.group(2).lower()
            month = month_names.index(raw) + 1 if raw in month_names else abbr.index(raw) + 1
            year = today.year
            try:
                d = datetime(year, month, day)
                if d < today:
                    d = datetime(year + 1, month, day)
                date_val = d.strftime("%Y-%m-%d")
            except ValueError:
                date_val = f"{day} {date_match.group(2).title()}"
        else:
            date_match = re.search(r'(\d{1,2})[/\-.](\d{1,2})', msg)
            if date_match:
                date_val = f"{date_match.group(1)}/{date_match.group(2)}"

    # ── TIME detection ──
    # "2 pm", "2:30 pm", "2 baje", "2:30 baje", "10am"
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje)', msg)
    if time_match:
        hour = int(time_match.group(1))
        mins = time_match.group(2) or "00"
        ampm = time_match.group(3)
        if ampm in ("am", "pm"):
            time_val = f"{hour}:{mins} {ampm.upper()}"
        else:
            # "baje" - guess AM/PM from hour
            if 5 <= hour < 12:
                time_val = f"{hour}:{mins} AM"
            elif 12 <= hour < 20:
                time_val = f"{hour}:{mins} PM"
            else:
                time_val = f"{hour}:{mins}"
    else:
        # "2 pm" without baje
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', msg)
        if time_match:
            hour = time_match.group(1)
            mins = time_match.group(2) or "00"
            ampm = time_match.group(3)
            time_val = f"{hour}:{mins} {ampm.upper()}"
        else:
            # "2 baje" without am/pm
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*baje', msg)
            if time_match:
                hour = int(time_match.group(1))
                mins = time_match.group(2) or "00"
                # Guess AM/PM
                if hour <= 12:
                    time_val = f"{hour}:{mins} AM" if hour < 12 else f"12:{mins} PM"
                else:
                    time_val = f"{hour-12}:{mins} PM"
            else:
                # "subah", "dopahar", "shaam" fallback
                if "subah" in msg or "morning" in msg:
                    time_val = "10:00 AM"
                elif "dopahar" in msg or "afternoon" in msg:
                    time_val = "2:00 PM"
                elif "shaam" in msg or "evening" in msg:
                    time_val = "5:00 PM"

    return date_val, time_val


FALCON_VERSION = "2.0"
FALCON_NAME = "Falcon"


def falcon_reply(message: str, customer_name: str = "Customer", inventory_context: list = None, order_context: list = None, coupon_context: list = None, last_qty: int = None, payment_context: dict = None, session_id: str = None, customer_id: str = None, business_name: str = "Business", language: str = None, knowledge_context: str = None) -> str:
    """Falcon v2.0 — Advanced Rule-Based AI Engine with Self-Learning.
    No API key needed. Learns from API responses over time.

    Pipeline:
    1. Check trainer for learned response (from past API calls)
    2. Use advanced Falcon Engine (intent, entity, sentiment, etc.)
    3. Fall back to legacy rule engine (v1.0)"""
    # Use business preferred language if provided, else detect from message
    lang = language if language else detect_language(message)

    # Step 1: Check trainer for learned response
    try:
        from services.falcon_trainer import get_trainer
        trainer = get_trainer()
        learned_reply = trainer.find_response(query=message, language=lang)
        if learned_reply:
            return learned_reply
    except Exception:
        pass
    # Step 2: Use advanced Falcon Engine
    try:
        from services.falcon_engine import get_falcon
        engine = get_falcon()
        reply = engine.process(
            message=message,
            customer_name=customer_name,
            session_id=session_id,
            customer_id=customer_id,
            inventory=inventory_context,
            order_context=order_context,
            coupon_context=coupon_context,
            business_name=business_name,
            payment_context=payment_context,
            language=lang,
            knowledge_context=knowledge_context,
        )
        if reply:
            # FalconEngine already generates responses in the correct language
            # Skip translate_response to avoid overwriting Marathi/other language responses
            return reply
    except Exception as e:
        pass  # Fallback to legacy engine

    # Step 3: Legacy Falcon engine (v1.0) as fallback
    reply = _falcon_inner(message, customer_name, inventory_context, order_context, coupon_context, last_qty, payment_context, knowledge_context)
    return translate_response(reply, lang)


# Backwards compatibility alias
get_fallback_reply = falcon_reply


def _falcon_inner(message: str, customer_name: str = "Customer", inventory_context: list = None, order_context: list = None, coupon_context: list = None, last_qty: int = None, payment_context: dict = None, knowledge_context: str = None) -> str:
    """Falcon Engine v1.0 — inventory + booking + order + coupon + repeat + feedback flows."""
    msg = message.lower().strip()
    name = customer_name

    # ─── STEP 0a: Non-business requests BLOCK karo ───
    non_business_keywords = [
        "joke", "jokes", "mazak", "mazaak",
        "gaana", "song", "music", "gao", "gaau", "poem", "kavita", "shayari",
        "story", "kahani", "kahaani",
        "weather", "mausam", "samachar", "news", "cricket", "match",
        "translate", "matlab", "meaning", "spell",
        "movie", "film", "netflix", "youtube",
    ]
    if any(w in msg for w in non_business_keywords):
        return (f"{name}, sorry! Main sirf {inventory_context[0]['name'].split()[0] if inventory_context else 'business'} "
                f"ke baare mein baat kar sakta hoon. 😊\n"
                f"Aapko hamare products ya services ke baare mein kuch jaanna hai?")

    # ─── STEP 0b: Photo/Image request detect karo ───
    photo_keywords = ["photo", "image", "picture", "pic", "dikhao", "dikha", "bhejo", "bhej", "send photo", "send image"]
    # Use whole word matching to avoid "pickup" matching "pic"
    has_photo_intent = False
    for w in photo_keywords:
        if re.search(r'\b' + re.escape(w) + r'\b', msg):
            has_photo_intent = True
            break
    if has_photo_intent and inventory_context:
        # Find which product the customer is asking about
        for p in inventory_context:
            pname = p["name"].lower()
            # Check if product name words appear in message
            if any(w in msg for w in pname.split() if len(w) > 2):
                if p.get("image_url"):
                    return (f"IMAGE_URL:{p['image_url']}\n"
                            f"{name}, ye raha {p['name']} ka photo! 📸\n"
                            f"💰 Price: ₹{p['price']}\n"
                            f"📦 Stock: {p['stock']} {p['unit']}\n\n"
                            f"Order karna ho toh bolo: ORDER {p['name']}")
                else:
                    return (f"{name}, {p['name']} ki photo abhi available nahi hai. 😅\n"
                            f"💰 Price: ₹{p['price']}\n"
                            f"📦 Stock: {p['stock']} {p['unit']}\n\n"
                            f"Order karna ho toh bolo: ORDER {p['name']}")
        # If no specific product matched, show all that have images
        with_images = [p for p in inventory_context if p.get("image_url")]
        if with_images:
            p = with_images[0]
            return (f"IMAGE_URL:{p['image_url']}\n"
                    f"{name}, ye raha {p['name']} ka photo! 📸\n"
                    f"💰 Price: ₹{p['price']}\n"
                    f"📦 Stock: {p['stock']} {p['unit']}\n\n"
                    f"Konsa chahiye? Naam bolo!")
        return f"{name}, abhi kisi product ki photo available nahi hai. 😅\n\nKonsa product chahiye? Naam batao!"

    # ─── STEP 0: Check if message is just a quantity (e.g. "1 pc", "2 pieces", "3") ───
    # First check if it's an address (contains road, street, etc.) - not a quantity
    is_address = any(w in msg for w in ["road", "street", "lane", "nagar", "colony", "area", "city", "pin", "flat", "house", "apartment", "floor", "behind", "near", "opp", "opposite"])
    # Don't match if message contains product name words (e.g. "RAM 8GB" should not match "8" as qty)
    has_product_words = inventory_context and any(
        any(word in msg for word in p["name"].lower().split() if len(word) > 2)
        for p in inventory_context
    )
    qty_match = None if (is_address or has_product_words) else re.match(r'^(\d+)\s*(pc|pcs|piece|pieces|unit|units|sets?|bottle|bottles|box|boxes|pack|packs)?$', msg.strip())
    if qty_match and inventory_context:
        qty = int(qty_match.group(1))
        # Find first product in context
        for p in inventory_context:
            if p.get("item_type") != "service":
                total = p["price"] * qty
                return (f"📦 Order Summary:\n"
                        f"Product: {p['name']}\n"
                        f"Quantity: {qty} {p['unit']}\n"
                        f"Total: ₹{total}\n\n"
                        f"🏠 Delivery ya Pickup?\n"
                        f"1️⃣ Delivery - Ghar tak (₹50 extra)\n"
                        f"2️⃣ Pickup - Store se le jao (FREE)\n\n"
                        f"Bolo: DELIVERY ya PICKUP")
        return f"{name}, kaunsa product chahiye? Naam batao! 🛒"

    # Check if message is delivery/pickup selection (standalone)
    if msg.strip() in ["delivery", "deliver", "pickup", "pick", "1", "2"]:
        if msg.strip() in ["delivery", "deliver", "1"]:
            return (f"🏠 Delivery address batao:\n\n"
                    f"Apna pura address likho:\n"
                    f"(House no, Street, Area, City, Pincode)\n\n"
                    f"Example: 123, MG Road, Andheri West, Mumbai 400058")
        else:
            # If inventory context has a product, show full order details for order saving
            if inventory_context:
                prod = None
                for p in inventory_context:
                    if p.get("item_type") != "service":
                        prod = p
                        break
                if prod:
                    qty = last_qty or 1
                    return (f"✅ Order confirmed, {name}!\n\n"
                            f"📦 Product: {prod['name']}\n"
                            f"🔢 Quantity: {qty} {prod['unit']}\n"
                            f"💰 Total: ₹{prod['price'] * qty}\n"
                            f"📍 Pickup: Store se aake le jao\n\n"
                            f"💳 Payment: UPI ya Cash on pickup\n"
                            f"🕐 Store timing: 10 AM - 8 PM\n\n"
                            f"Order ID: ORD-{_deterministic_id(name, 10000):04d}\n"
                            f"Thanks for shopping with us! 🙏")
            return (f"✅ Pickup order confirmed!\n\n"
                    f"📍 Store: {business_name}\n"
                    f"🕐 Timing: 10 AM - 8 PM\n"
                    f"💳 Payment: UPI ya Cash on pickup\n\n"
                    f"Jab aao tab le jao. Thanks! 🙏")

    # ─── STEP 0b: Payment intent - check before inventory search ───
    if any(w in msg for w in ["upi", "pay", "payment", "paise", "bill", "cash", "cod", "phonepe", "gpay", "googlepay", "scan", "qr"]):
        upi_id = "business@upi"
        if payment_context and payment_context.get("upi_id"):
            upi_id = payment_context["upi_id"]
        return (f"{name}, payment ke liye ye options hain:\n\n"
                f"💳 UPI: {upi_id}\n"
                f"📱 PhonePe / Google Pay / Paytm\n"
                f"💵 Cash on Delivery bhi available hai\n\n"
                f"Koi aur sawaal ho toh pooch lena!")

    # ─── STEP 0d: Order status inquiry ───
    if any(w in msg for w in ["order status", "order kab", "mera order", "order tracking", "delivery kab", "kab aayega", "kab milega", "order update"]):
        if order_context:
            latest = order_context[0] if order_context else None
            if latest:
                return (f"{name}, aapka latest order:\n\n"
                        f"📦 Product: {latest.get('product_name', 'N/A')}\n"
                        f"🔢 Qty: {latest.get('quantity', 1)}\n"
                        f"💰 Total: ₹{latest.get('total_price', 0)}\n"
                        f"📋 Status: {latest.get('status', 'pending').title()}\n"
                        f"📅 Date: {latest.get('created_at', 'N/A')}\n\n"
                        f"Koi aur sawaal ho toh pooch lena!")
            return f"{name}, abhi koi active order nahi mila. Naya order karna ho toh product ka naam bolo! 🛒"
        return f"{name}, order status jaanna ho toh apna order ID batao. Ya product ka naam bolo jo order kiya tha!"

    # ─── STEP 0e: Repeat order (wahi order karo) ───
    if any(w in msg for w in ["wahi order", "same order", "repeat order", "dobara order", "phir se order", "last wala order", "pichla order"]):
        if order_context:
            latest = order_context[0] if order_context else None
            if latest:
                return (f"{name}, {latest.get('product_name', 'product')} se order karna hai? 🔄\n\n"
                        f"📦 Last order: {latest.get('product_name', 'N/A')} x{latest.get('quantity', 1)}\n"
                        f"💰 Price: ₹{latest.get('unit_price', 0)}\n\n"
                        f"Kitne chahiye? Quantity batao ya SAME bolo for same quantity!")
        return f"{name}, aapka koi purana order nahi mila. Pehle koi order toh karo! 🛒"

    # ─── STEP 0f: Coupon/Discount inquiry ───
    if any(w in msg for w in ["coupon", "discount", "code", "promo", "offer", "bachat", "sasta"]):
        if coupon_context:
            coupon_list = "\n".join([f"  🏷️ {c['code']} - {c['discount_value']}{'%' if c['discount_type'] == 'percent' else '₹'} OFF (min ₹{c['min_order']})" for c in coupon_context[:5]])
            return (f"{name}, ye coupons available hain:\n\n{coupon_list}\n\n"
                    f"Coupon lagane ke liye bolo: COUPON [code]\n"
                    f"Example: COUPON SAVE10")
        return f"{name}, abhi koi coupon available nahi hai. Par aapko special discount denge! Admin se baat karo. 😊"

    # ─── STEP 0g: Coupon apply ───
    coupon_match = re.match(r'coupon\s+(\w+)', msg)
    if coupon_match:
        code = coupon_match.group(1).upper()
        if coupon_context:
            for c in coupon_context:
                if c["code"] == code:
                    return (f"✅ Coupon lag gaya, {name}! 🎉\n\n"
                            f"🏷️ Code: {c['code']}\n"
                            f"💰 Discount: {c['discount_value']}{'%' if c['discount_type'] == 'percent' else '₹'} OFF\n\n"
                            f"Ab order karo - discount automatically apply ho jayega!")
        return f"{name}, '{code}' coupon valid nahi hai. Check karo code sahi hai ya nahi!"

    # ─── STEP 0h: Price/Rate query (BEFORE feedback — "rate" means price, not review) ───
    if any(w in msg for w in ["price", "rate", "cost", "kitna", "dam", "charge", "lagenge", "lagega"]):
        # Check if a specific product/service is mentioned — prefer longest match
        if inventory_context:
            best_match = None
            best_score = 0
            for p in inventory_context:
                words = [w for w in p["name"].lower().split() if len(w) > 2]
                score = sum(1 for w in words if re.search(r'\b' + re.escape(w) + r'\b', msg))
                if score > best_score:
                    best_score = score
                    best_match = p
            if best_match and best_score > 0:
                return (f"{name}, {best_match['name']} ka price ₹{best_match['price']} hai! 💰\n"
                        f"📦 Stock: {best_match['stock']} {best_match['unit']} available hain.\n\n"
                        f"Order karna ho toh bolo: ORDER {best_match['name']}")
        return f"{name}, kis product/service ka price jaanna hai? Uska naam batao! 😊"

    # ─── STEP 0h2: Feedback/Review request ───
    if any(w in msg for w in ["feedback", "review", "rating", "star", "experience", "kaisa laga"]):
        return (f"{name}, humein aapka feedback chahiye! ⭐\n\n"
                f"1️⃣ = Bahut kharab\n"
                f"2️⃣ = Kharab\n"
                f"3️⃣ = Theek hai\n"
                f"4️⃣ = Achha hai\n"
                f"5️⃣ = Bahut achha!\n\n"
                f"Apna rating bhejo (1-5) aur sath mein review bhi likho!")

    # ─── STEP 0h3: Warranty/Guarantee queries ───
    if any(w in msg for w in ["warranty", "guarantee", "waranty", "gurantee"]):
        if inventory_context:
            for p in inventory_context:
                if any(word in msg for word in p["name"].lower().split() if len(word) > 2):
                    return (f"{name}, {p['name']} pe 6 mahine ki warranty hai! ✅\n\n"
                            f"Warranty mein free repair hoga agar manufacturing defect ho.\n"
                            f"Physical damage warranty mein cover nahi hota.\n\n"
                            f"Order karna ho toh bolo: ORDER {p['name']}")
        return (f"{name}, hamari services pe 6 mahine ki warranty hai! ✅\n"
                f"Products pe manufacturer warranty milti hai.\n\n"
                f"Kis cheez ke baare mein jaanna hai? Naam batao!")

    # ─── STEP 0h4: Complaint/Problem queries ───
    if any(w in msg for w in ["complaint", "shikayat", "problem phir se", "repair sahi nahi", "kaam achha nahi", "kharab kaam", "paisa waste", "refund", "paisa wapas", "paise wapas"]):
        return (f"{name}, mujhe afsoos hai! 😔 Aapki complaint seriously le rahe hain.\n\n"
                f"🔄 Free re-repair hoga agar problem 7 din mein phir se aaye.\n"
                f"💰 Refund policy: Repair ke baad bhi problem solve nahi hui toh full refund.\n\n"
                f"Please apna order ID batao ya store pe aa jao. Hum zaroor resolve karenge!")

    # ─── STEP 0h5: EMI/Installment queries ───
    if any(w in msg for w in ["emi", "installment", "kist", "kist mein"]):
        return (f"{name}, haan EMI available hai! 💳\n\n"
                f"📦 ₹2000 se upar ke orders pe:\n"
                f"  • 3 months EMI — No interest\n"
                f"  • 6 months EMI — 2% interest\n"
                f"  • 12 months EMI — 5% interest\n\n"
                f"Credit card se EMI select kar sakte ho payment time pe.")

    # ─── STEP 0h6: Invoice/Bill/Receipt/GST queries ───
    if any(w in msg for w in ["invoice", "bill", "receipt", "gst", "tax"]):
        return (f"{name}, haan milega! 📄\n\n"
                f"✅ GST bill milega har order pe\n"
                f"✅ Invoice automatically generate hota hai\n"
                f"✅ Email pe bhi bhej sakte hain\n\n"
                f"Apna order ID batao ya store pe aa jao.")

    # ─── STEP 0i: Cart operations ───
    if any(w in msg for w in ["cart", "basket", "samaan"]):
        return (f"{name}, aapka cart khaali hai abhi. 🛒\n\n"
                f"Shopping start karne ke liye product ka naam bao!\n"
                f"Example: Mouse, Pen Drive, Keyboard")

    # ─── STEP 0j: Quick quantity response with delivery/pickup context ───
    if msg.strip() in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
        qty = int(msg.strip())
        if inventory_context:
            for p in inventory_context:
                if p.get("item_type") != "service":
                    total = p["price"] * qty
                    return (f"📦 Order Summary:\n"
                            f"Product: {p['name']}\n"
                            f"Quantity: {qty} {p['unit']}\n"
                            f"Total: ₹{total}\n\n"
                            f"🏠 Delivery ya Pickup?\n"
                            f"1️⃣ Delivery - Ghar tak (₹50 extra)\n"
                            f"2️⃣ Pickup - Store se le jao (FREE)\n\n"
                            f"Bolo: DELIVERY ya PICKUP")

    # ─── STEP 0c: Address detection - delivery address aaya hai ───
    address_words = ["road", "street", "lane", "nagar", "colony", "area", "city", "pin",
                     "flat", "house", "apartment", "floor", "behind", "near", "opp", "opposite",
                     "market", "tower", "building", "block", "sector", "phase", "extension"]
    if any(w in msg for w in address_words) and inventory_context:
        # Find the product from context
        prod = None
        for p in inventory_context:
            if p.get("item_type") != "service":
                prod = p
                break
        if prod:
            addr = message.strip()
            return (f"✅ Order confirmed, {name}!\n\n"
                    f"📦 Product: {prod['name']}\n"
                    f"💰 Total: ₹{prod['price']}\n"
                    f"📍 Delivery: {addr}\n\n"
                    f"💳 Payment: Cash on Delivery ya UPI\n"
                    f"🚚 Delivery: 2-3 din mein aa jayega\n\n"
                    f"Order ID: ORD-{_deterministic_id(name, 10000):04d}\n"
                    f"Thanks for shopping with us! 🙏")

    # ─── STEP 1: Inventory se product/service dhundho ───
    matched_product = None
    matched_service = None

    # ─── STEP 1a: Service keyword matching for common repair issues ───
    service_keywords = {
        "internet": "WiFi Fix",
        "wifi": "WiFi Fix",
        "bluetooth": "Laptop Repair",
        "sound": "Laptop Repair",
        "speaker": "Laptop Repair",
        "camera": "Laptop Repair",
        "touchpad": "Laptop Repair",
        "charging": "Laptop Repair",
        "port": "Laptop Repair",
        "hinge": "Laptop Repair",
        "body": "Laptop Repair",
        "paani": "Laptop Repair",
        "water": "Laptop Repair",
        "drop": "Laptop Repair",
        "gir gaya": "Laptop Repair",
        "garam": "Laptop Repair",
        "hang": "Laptop Repair",
        "slow": "Laptop Repair",
        "band": "Laptop Repair",
        "on nahi": "Laptop Repair",
        "format": "OS Installation",
        "windows": "OS Installation",
        "virus": "Virus Removal",
        "data": "Data Recovery",
        "hard disk": "Data Recovery",
        "screen flicker": "Screen Replacement",
        "screen lines": "Screen Replacement",
        "screen black": "Screen Replacement",
        "screen spots": "Screen Replacement",
        "screen dim": "Screen Replacement",
    }
    # Also check for exact service name in message (e.g. "keyboard replacement" matches "Keyboard Replacement")
    if inventory_context and not matched_service and not matched_product:
        # First try exact service name match — prefer longest match
        best_service = None
        best_len = 0
        for p in inventory_context:
            if p.get("item_type") == "service" and p["name"].lower() in msg:
                if len(p["name"]) > best_len:
                    best_len = len(p["name"])
                    best_service = p
        if best_service:
            matched_service = best_service
        # Then try keyword match
        if not matched_service:
            for keyword, service_name in service_keywords.items():
                if keyword in msg:
                    for p in inventory_context:
                        if p["name"].lower() == service_name.lower() and p.get("item_type") == "service":
                            matched_service = p
                            break
                    if matched_service:
                        break

    # Check if message is just date+time (e.g. "Monday 2 pm", "kal 10 baje")
    date_val, time_val = extract_date_time(msg)
    if date_val and time_val and inventory_context:
        # Find first service in context
        for p in inventory_context:
            if p.get("item_type") == "service":
                svc = p
                duration = svc.get("duration_minutes", 30)
                return (f"✅ Booking confirmed, {name}!\n\n"
                        f"📋 Service: {svc['name']}\n"
                        f"📅 Din: {date_val}\n"
                        f"🕐 Time: {time_val}\n"
                        f"⏰ Duration: {duration} min\n"
                        f"💰 Price: ₹{svc['price']}\n\n"
                        f"Booking ID: BK-{svc['name'][:3].upper()}-{_deterministic_id(name, 1000):03d}\n\n"
                        f"📌 Location: {business_name}\n"
                        f"Aap 5 min pehle aa jaana. Thanks! 🙏")
        # No service found, ask which one
        return (f"{name}, kaunsi service book karni hai? Naam batao! 😊\n"
                f"Available services: {', '.join([p['name'] for p in inventory_context[:5]])}")

    if inventory_context:
        # Exact name match pehle
        for p in inventory_context:
            if p["name"].lower() in msg:
                if p.get("item_type") == "service":
                    matched_service = p
                else:
                    matched_product = p
                break
        # Word-by-word match — prefer longest match (whole words only)
        if not matched_product and not matched_service:
            best_match = None
            best_score = 0
            for p in inventory_context:
                words = [w for w in p["name"].lower().split() if len(w) > 2]
                score = sum(1 for w in words if re.search(r'\b' + re.escape(w) + r'\b', msg))
                if score > best_score:
                    best_score = score
                    best_match = p
            if best_match and best_score > 0:
                if best_match.get("item_type") == "service":
                    matched_service = best_match
                else:
                    matched_product = best_match
        # Agar ek hi product mila toh use le lo
        if not matched_product and not matched_service and len(inventory_context) == 1:
            p = inventory_context[0]
            if p.get("item_type") == "service":
                matched_service = p
            else:
                matched_product = p

    # ─── STEP 2: SERVICE booking flow ───
    if matched_service:
        svc = matched_service

        # Check if message contains date+time -> create booking
        date_val, time_val = extract_date_time(msg)
        if date_val and time_val:
            duration = svc.get("duration_minutes", 30)
            return (f"✅ Booking confirmed, {name}!\n\n"
                    f"📋 Service: {svc['name']}\n"
                    f"📅 Din: {date_val}\n"
                    f"🕐 Time: {time_val}\n"
                    f"⏰ Duration: {duration} min\n"
                    f"💰 Price: ₹{svc['price']}\n\n"
                    f"Booking ID: BK-{svc['name'][:3].upper()}-{_deterministic_id(name, 1000):03d}\n\n"
                    f"📌 Location: {business_name}\n"
                    f"Aap 5 min pehle aa jaana. Thanks! 🙏")

        # Order/Buy intent for service
        if any(w in msg for w in ["order", "book", "karna hai", "lena hai", "chahiye", "buy", "karwana", "lagwana"]):
            return (f"{name}, {svc['name']} book karna hai? Great choice! 🎉\n"
                    f"💰 Price: ₹{svc['price']}\n"
                    f"⏰ Duration: {svc.get('duration_minutes', 30)} min\n\n"
                    f"📅 Kis din chahiye? (e.g. aaj, kal, Monday)\n"
                    f"🕐 Kitne baje? (e.g. 10am, 2pm, 4:30pm)")
        # Time/Timing inquiry
        if any(w in msg for w in ["time", "timing", "kab", "baje", "din", "slot", "available", "open", "close", "hours"]):
            return (f"{name}, {svc['name']} ke liye ye slots available hain:\n\n"
                    f"🌅 subah: 9:00 AM - 12:00 PM\n"
                    f"☀️ dopahar: 12:00 PM - 4:00 PM\n"
                    f"🌇 shaam: 4:00 PM - 8:00 PM\n\n"
                    f"💰 Price: ₹{svc['price']} | ⏰ {svc.get('duration_minutes', 30)} min\n\n"
                    f"📅 Kaunsa din aur kitne baje chahiye? Batao!")
        # Default - show service info
        return (f"{name}, {svc['name']} available hai! 🎉\n"
                f"💰 Price: ₹{svc['price']}\n"
                f"⏰ Duration: {svc.get('duration_minutes', 30)} min\n"
                f"📦 Stock: {svc['stock']} slots\n\n"
                f"Book karna ho toh bolo: BOOK {svc['name']}\n"
                f"Timing jaanna ho toh bolo: {svc['name']} timing")

    # ─── STEP 3: PRODUCT ordering flow ───
    if matched_product:
        prod = matched_product

        # Photo/Image request for matched product
        if any(w in msg for w in photo_keywords):
            if prod.get("image_url"):
                return (f"IMAGE_URL:{prod['image_url']}\n"
                        f"{name}, ye raha {prod['name']} ka photo! 📸\n"
                        f"💰 Price: ₹{prod['price']}\n"
                        f"📦 Stock: {prod['stock']} {prod['unit']}\n\n"
                        f"Order karna ho toh bolo: ORDER {prod['name']}")
            else:
                return (f"{name}, {prod['name']} ki photo abhi available nahi hai. 😅\n"
                        f"💰 Price: ₹{prod['price']}\n"
                        f"📦 Stock: {prod['stock']} {prod['unit']}\n\n"
                        f"Order karna ho toh bolo: ORDER {prod['name']}")

        # Check if message is a quantity response (e.g. "1 pc", "2 pieces", "3 unit")
        # Only match if message is JUST a number + optional unit (not "RAM 8GB" where 8 is part of name)
        qty_match = re.match(r'^(\d+)\s*(pc|pcs|piece|pieces|unit|units|sets?|bottle|bottles|box|boxes|pack|packs)?$', msg.strip())
        if qty_match:
            qty = int(qty_match.group(1))
            total = prod["price"] * qty
            return (f"📦 Order Summary:\n"
                    f"Product: {prod['name']}\n"
                    f"Quantity: {qty} {prod['unit']}\n"
                    f"Total: ₹{total}\n\n"
                    f"🏠 Delivery ya Pickup?\n"
                    f"1️⃣ Delivery - Ghar tak (₹50 extra)\n"
                    f"2️⃣ Pickup - Store se le jao (FREE)\n\n"
                    f"Bolo: DELIVERY ya PICKUP")

        # Check if message is delivery/pickup selection
        if any(w in msg for w in ["delivery", "deliver", "ghar", "bhejo", "home"]):
            return (f"🏠 Delivery address batao:\n\n"
                    f"Apna pura address likho:\n"
                    f"(House no, Street, Area, City, Pincode)\n\n"
                    f"Example: 123, MG Road, Andheri West, Mumbai 400058")

        if any(w in msg for w in ["pickup", "pick", "pickup", "store", "dukaan", "le jaunga", "khud lunga"]):
            return (f"✅ Order confirmed, {name}!\n\n"
                    f"📦 Product: {prod['name']}\n"
                    f"🔢 Quantity: {qty_match.group(1) if qty_match else '1'} {prod['unit']}\n"
                    f"💰 Total: ₹{prod['price'] * int(qty_match.group(1) if qty_match else 1)}\n"
                    f"📍 Pickup: Store se aake le jao\n\n"
                    f"💳 Payment: UPI ya Cash on pickup\n"
                    f"🕐 Store timing: 10 AM - 8 PM\n\n"
                    f"Order ID: ORD-{_deterministic_id(name, 10000):04d}\n"
                    f"Thanks for shopping with us! 🙏")

        # Check if message looks like an address (contains numbers + area words)
        if any(w in msg for w in ["road", "street", "lane", "nagar", "colony", "area", "city", "pin", "pincode", "flat", "house", "apartment", "floor"]):
            return (f"✅ Order confirmed, {name}!\n\n"
                    f"📦 Product: {prod['name']}\n"
                    f"💰 Total: ₹{prod['price']}\n"
                    f"📍 Delivery: {msg.title()}\n\n"
                    f"💳 Payment: Cash on Delivery ya UPI\n"
                    f"🚚 Delivery: 2-3 din mein aa jayega\n\n"
                    f"Order ID: ORD-{_deterministic_id(name, 10000):04d}\n"
                    f"Thanks for shopping with us! 🙏")

        if any(w in msg for w in ["order", "buy", "kharid", "lena hai", "chahiye", "purchase"]):
            return (f"{name}, {prod['name']} order karna hai? 🛒\n"
                    f"💰 Price: ₹{prod['price']}\n"
                    f"📦 Stock: {prod['stock']} {prod['unit']}\n\n"
                    f"Kitne chahiye? Quantity batao! (e.g. 1 pc, 2 pieces)")
        if any(w in msg for w in ["price", "rate", "cost", "kitna", "dam"]):
            if prod["stock"] == 0:
                return f"{name}, {prod['name']} ka price ₹{prod['price']} hai. Lekin abhi stock khatam ho gaya hai. 😔\nKoi aur product chahiye toh batao!"
            return f"{name}, {prod['name']} ka price ₹{prod['price']} hai! 💰\n📦 Stock: {prod['stock']} {prod['unit']} available hain.\n\nOrder karna ho toh bolo: ORDER {prod['name']}"
        if prod["stock"] == 0:
            return (f"{name}, {prod['name']} ka price ₹{prod['price']} hai, lekin abhi stock nahi hai. 😔\n"
                    f"Koi aur product chahiye toh batao! Ya baad mein pooch lena.")
        return (f"{name}, {prod['name']} hamare paas hai! 🎉\n"
                f"💰 Price: ₹{prod['price']}\n"
                f"📦 Stock: {prod['stock']} {prod['unit']} bache hain\n\n"
                f"Order karna ho toh bolo: ORDER {prod['name']}")

    # ─── STEP 3.5: Generic responses BEFORE product list ───
    # Pickup query
    if any(w in msg for w in ["pickup", "store se", "dukaan se", "khud lunga", "le jaunga"]):
        if inventory_context:
            # Find first product
            prod = None
            for p in inventory_context:
                if p.get("item_type") != "service":
                    prod = p
                    break
            if prod:
                return (f"{name}, haan store se pickup kar sakte ho! 🏪\n\n"
                        f"📍 Store timing: 10 AM - 8 PM (Mon-Sat)\n"
                        f"💳 Payment: Cash ya UPI dono chalenge\n\n"
                        f"Kya lena hai? Product ka naam batao!")
        return (f"{name}, haan store se pickup kar sakte ho! 🏪\n\n"
                f"📍 Store timing: 10 AM - 8 PM (Mon-Sat)\n"
                f"💳 Payment: Cash ya UPI dono chalenge\n\n"
                f"Kya lena hai? Product ka naam batao!")

    # Thanks
    if any(w in msg for w in ["thanks", "shukriya", "thank", "dhanyavaad", "thank you"]):
        return f"Khushi hui {name}! 😊 Aur koi sawaal ho toh pooch lena."

    # Price generic (no specific product matched)
    if any(w in msg for w in ["price", "pricing", "rate", "kitna", "cost", "dam", "kya price"]):
        return f"{name}, kis product/service ka price jaanna hai? Uska naam batao! 😊"

    # Order/Buy generic
    if any(w in msg for w in ["order", "buy", "kharid", "lena hai", "purchase"]):
        return f"{name}, kya order karna hai? Product/Service ka naam batao! 🛒"

    # ─── STEP 4: Product list dikhao (multiple matches) ───
    if inventory_context and len(inventory_context) > 1:
        services = [p for p in inventory_context if p.get("item_type") == "service"]
        products = [p for p in inventory_context if p.get("item_type") != "service"]

        reply = ""
        if services:
            svc_list = "\n".join([f"  {i+1}. {s['name']} - ₹{s['price']} ({s.get('duration_minutes', 30)} min)" for i, s in enumerate(services[:5])])
            reply += f"🔧 Services:\n{svc_list}\n\n"
        if products:
            prod_list = "\n".join([f"  {i+1}. {p['name']} - ₹{p['price']}" for i, p in enumerate(products[:5])])
            reply += f"📦 Products:\n{prod_list}\n\n"
        if reply:
            return f"{name}, ye available hain:\n{reply}Konsa chahiye? Uska naam bolo!"

    # ─── STEP 5: Generic intent detection ───
    # Non-business: PC/laptop/repair (only if NOT matched to an inventory item)
    non_biz_words = ["pc", "laptop", "computer", "printer", "scanner", "monitor", "tv", "refrigerator", "fridge", "washing machine"]
    non_biz_action = ["problem", "fix", "install", "software", "windows", "virus", "format", "crash", "not working", "kharab", "bigad", "karb", "bigda", "bigda hua", "sahi karo", "theek karo", "repair"]
    if any(w in msg for w in non_biz_words) and any(a in msg for a in non_biz_action):
        return f"{name}, sorry! Hum sirf products aur services bechte hain. 😊\n\nPC/laptop repair ki seva hum provide nahi karte.\n\nKya aap hamare products dekhna chahenge?"

    # Greeting
    if any(w in msg for w in ["hi", "hello", "hey", "namaste", "namaskar", "hii", "good morning", "good evening"]):
        return f"Namaste {name}! 🙏 Main aapki kya madad kar sakta ho?\n\nAap ye pooch sakte ho:\n- Product/Service ka naam\n- Price jaanna ho\n- Booking karni ho\n- Order karna ho"

    # Business name query
    if any(w in msg for w in ["store ka naam", "shop ka naam", "dukaan ka naam", "naam kya hai", "kya naam hai", "name kya hai", "tumhara naam", "aapka naam", "business name"]):
        biz_name = inventory_context[0].get('business_name', 'Repair-it') if inventory_context else 'Repair-it'
        return f"{name}, hamara store ka naam **{biz_name}** hai! 😊\n\nAapko kya chahiye — product, service, ya booking?"

    # Non-business: PC/laptop/repair (but NOT if they're asking about a service we have)
    # NOTE: This check is done AFTER product matching so "Laptop Repair" in inventory is found first

    # Timing/Booking generic
    if any(w in msg for w in ["booking", "book", "timing", "time", "kab", "slot", "appointment"]):
        return f"{name}, kis service ki booking karni hai? Pehle service ka naam batao! 😊"

    # Complaint
    if any(w in msg for w in ["complaint", "problem", "issue", "galti"]):
        return f"{name}, mujhe afsoos hai! 😔 Aapki complaint note ho gayi. Jaldi resolve karenge."

    # ─── STEP 7: FALLBACK (KNOWLEDGE BASE) ───
    if knowledge_context:
        return (f"{name}, aapke sawaal ka jawab yaha hai:\n\n"
                f"{knowledge_context}\n\n"
                f"Aur koi help chahiye?")

    # Default
    return f"{name}, aapka message mil gaya! 😊\n\nAap ye pooch sakte ho:\n- Product/Service ka naam (e.g. Facial, Hair Cut)\n- Price jaanna ho\n- Booking karni ho\n- Order karna ho"
