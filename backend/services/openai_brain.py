import os
import json
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from .prompt_manager import PromptManager


class OpenAIBrain:
    """Real OpenAI integration for generating Hinglish responses."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", "")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.prompt_manager = PromptManager()
        self._response_cache: Dict[str, str] = {}

    async def generate_response(
        self,
        message: str,
        context: Dict[str, Any],
        intent: str = "general",
        sentiment: str = "neutral",
        customer_name: str = "Customer",
        business_name: str = "Business",
    ) -> str:
        """Generate a Hinglish response based on message, context, and intent."""

        # If no API key, use template-based fallback
        if not self.client:
            return self._fallback_response(intent, message, customer_name)

        # Check cache — use full message hash to avoid prefix collisions
        import hashlib
        msg_hash = hashlib.sha256(message.encode()).hexdigest()[:16]
        cache_key = f"{intent}:{msg_hash}"
        if cache_key in self._response_cache:
            return self._response_cache[cache_key]

        try:
            system_prompt = self._build_system_prompt(business_name, context)
            user_prompt = self._build_user_prompt(
                message, intent, sentiment, customer_name, context
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=300,
            )

            reply = response.choices[0].message.content.strip()
            self._response_cache[cache_key] = reply
            return reply

        except Exception as e:
            print(f"OpenAI error: {e}")
            return self._fallback_response(intent, message, customer_name)

    def _build_system_prompt(self, business_name: str, context: Dict[str, Any]) -> str:
        """Build the system prompt for Hinglish responses."""
        products = context.get("products", [])
        is_wholesaler = context.get("is_wholesaler", False)
        products_text = ""
        if products:
            if is_wholesaler:
                product_lines = [f"- {p.get('name', 'Item')}: Wholesale ₹{p.get('wholesale_price') or p.get('price', 0)} (Retail ₹{p.get('price', 0)}) ({p.get('stock', 0)} in stock)" for p in products[:10]]
            else:
                product_lines = [f"- {p.get('name', 'Item')}: ₹{p.get('price', 0)} ({p.get('stock', 0)} in stock)" for p in products[:10]]
            products_text = "\n".join(product_lines)
            
        wholesaler_instruction = ""
        if is_wholesaler:
            wholesaler_instruction = "\n- Yeh customer ek WHOLESALER hai. Unko hamesha wholesale price (agar available hai) batayein aur batao ki yeh unka special rate hai."

        return f"""Aap {business_name} ka AI customer service assistant ho.
Aap Hinglish mein baat karte ho - Hindi words English script mein.
Aap friendly, helpful aur professional ho.

Rules:
- Hamesha Hinglish mein jawaab do (Hindi words in English script)
- Chhote aur clear sentences mein baat karo
- Customer ko politely handle karo
- Agar koi cheez samajh nahi aaye toh politely pucho
- Prices aur products ke baare mein accurate info do
- WhatsApp style messages bhejo - emojis use karo but zyada nahi{wholesaler_instruction}

Available Products:
{products_text if products_text else "Products abhi available nahi hain."}

Response format: Sirf reply text do, koi extra formatting nahi."""

    def _build_user_prompt(
        self,
        message: str,
        intent: str,
        sentiment: str,
        customer_name: str,
        context: Dict[str, Any],
    ) -> str:
        """Build the user prompt with context."""
        recent = context.get("recent_messages", [])
        recent_text = ""
        if recent:
            recent_text = "\n".join([f"{'Customer' if m.get('role') == 'user' else 'Bot'}: {m.get('text', '')}" for m in recent[-5:]])

        return f"""Customer: {customer_name}
Intent detected: {intent}
Sentiment: {sentiment}

Recent conversation:
{recent_text if recent_text else "Naya conversation hai."}

Customer ka message: "{message}"

Aapka jawaab (Hinglish mein):"""

    def _fallback_response(self, intent: str, message: str, customer_name: str) -> str:
        """Template-based fallback when OpenAI is not available."""
        templates = {
            "greeting": f"Namaste {customer_name}! 🙏 Kaise ho? Hum aapki kya madad kar sakte hain?",
            "price_inquiry": "Haan bilkul! Price batata hoon - products humari website pe dekh sakte ho ya mujhse pucho kiska price chahiye. 😊",
            "order_status": "Aapka order track kar raha hoon... Order ID batao please? 📦",
            "catalog_browse": "Humari products dekho: \n🥛 Dairy items\n🍪 Biscuits & Snacks\n🥤 Beverages\nKya chahiye batao! 🛒",
            "payment_query": "Payment related kya puchna hai? UPI, cards, ya cash on delivery - sab options available hain! 💳",
            "feedback": "Aapka feedback humari value hai! Kaisa raha aapka experience? ⭐",
            "support": "Koi problem hai? Batao main help karta hoon! 💪",
            "appointment": "Appointment book karna hai? Kaunsa slot chahiye? Main check karta hoon. 📅",
            "general": f"Namaste {customer_name}! Kya help chahiye? Main yahan hoon aapki madad ke liye! 😊",
        }
        return templates.get(intent, templates["general"])

    async def classify_intent(self, message: str) -> str:
        """Classify message intent using OpenAI or rule-based fallback."""
        if not self.client:
            return self._rule_based_intent(message)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Classify this customer message into one of these intents:
greeting, price_inquiry, order_status, catalog_browse, payment_query, feedback, support, appointment, escalation, general

Return ONLY the intent name, nothing else."""
                    },
                    {"role": "user", "content": message},
                ],
                temperature=0.1,
                max_tokens=20,
            )
            return response.choices[0].message.content.strip().lower()
        except Exception:
            return self._rule_based_intent(message)

    def _rule_based_intent(self, message: str) -> str:
        """Simple rule-based intent classification."""
        msg = message.lower()
        if any(w in msg for w in ["hi", "hello", "namaste", "hey"]):
            return "greeting"
        if any(w in msg for w in ["price", "rate", "kitna", "daam", "cost"]):
            return "price_inquiry"
        if any(w in msg for w in ["order", "delivery", "kab", "where"]):
            return "order_status"
        if any(w in msg for w in ["product", "catalog", "list", "dikhao"]):
            return "catalog_browse"
        if any(w in msg for w in ["pay", "payment", "upi", "card", "cash"]):
            return "payment_query"
        if any(w in msg for w in ["feedback", "review", "experience"]):
            return "feedback"
        if any(w in msg for w in ["help", "problem", "issue", "nahi"]):
            return "support"
        if any(w in msg for w in ["book", "appointment", "slot", "time"]):
            return "appointment"
        if any(w in msg for w in ["manager", "human", "person", "call"]):
            return "escalation"
        return "general"

    async def analyze_sentiment(self, message: str) -> str:
        """Analyze sentiment of the message."""
        if not self.client:
            return self._rule_based_sentiment(message)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze sentiment. Return ONLY: positive, negative, or neutral."
                    },
                    {"role": "user", "content": message},
                ],
                temperature=0.1,
                max_tokens=10,
            )
            return response.choices[0].message.content.strip().lower()
        except Exception:
            return self._rule_based_sentiment(message)

    def _rule_based_sentiment(self, message: str) -> str:
        """Simple rule-based sentiment analysis."""
        msg = message.lower()
        positive = ["thanks", "thank you", "accha", "great", "awesome", "love", "best", "happy"]
        negative = ["bad", "worst", "problem", "issue", "complaint", "angry", "frustrated", "disappointed"]
        if any(w in msg for w in positive):
            return "positive"
        if any(w in msg for w in negative):
            return "negative"
        return "neutral"


# Singleton
openai_brain = OpenAIBrain()
