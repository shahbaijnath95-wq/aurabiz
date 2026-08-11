"""
Falcon Smart v3.0 — Ultra-Intelligent Reply Engine
====================================================
Makes Falcon replies contextual, personalized, emotional, and human-like.

Components:
1. SmartResponder — Deep contextual reply generation
2. ConversationMemory — Full conversation tracking with context
3. EmotionalIntelligence — Mood detection + empathetic responses
4. BusinessIntelligence — Smart upsell, discounts, proactive suggestions
5. CulturalAwareness — Indian customs, festivals, time-based greetings
6. SmartSuggestions — Proactive product/service recommendations
7. NaturalLanguage — Varied, human-like, non-robotic responses

Author: Falcon AI Engine
Version: 3.0
"""

import re
import json
import hashlib
import random
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict


# ============================================================
# 1. CONVERSATION MEMORY — Full Context Tracking
# ============================================================

class ConversationMemory:
    """Tracks full conversation context, not just keywords."""

    def __init__(self):
        self._conversations: Dict[str, Dict] = {}

    def get(self, session_id: str) -> Dict:
        """Get full conversation context."""
        if session_id not in self._conversations:
            self._conversations[session_id] = {
                "messages": [],           # Full message history
                "intents": [],            # Intent history
                "products_discussed": [], # Products mentioned
                "customer_mood": "neutral",  # Current mood
                "mood_history": [],       # Mood changes
                "stage": "initial",       # Conversation stage
                "turn_count": 0,
                "customer_preferences": {},  # Learned preferences
                "last_product": None,     # Last product discussed
                "last_price": None,       # Last price mentioned
                "last_quantity": None,    # Last quantity mentioned
                "delivery_preference": None,  # delivery/pickup
                "address": None,
                "complaints": [],         # Complaint history
                "positive_feedback": [],  # Positive feedback
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "topics_discussed": set(),
                "questions_asked": [],    # Questions customer asked
                "objections": [],         # Customer objections (price, etc.)
            }
        return self._conversations[session_id]

    def update(self, session_id: str, message: str, intent: str = None,
               product: str = None, price: float = None, quantity: int = None,
               mood: str = None, delivery: str = None, address: str = None):
        """Update conversation with new message."""
        ctx = self.get(session_id)
        ctx["messages"].append({
            "text": message,
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
        })
        ctx["turn_count"] += 1
        ctx["last_seen"] = datetime.now().isoformat()

        if intent:
            ctx["intents"].append(intent)
        if product:
            ctx["products_discussed"].append(product)
            ctx["last_product"] = product
        if price:
            ctx["last_price"] = price
        if quantity:
            ctx["last_quantity"] = quantity
        if mood:
            ctx["customer_mood"] = mood
            ctx["mood_history"].append(mood)
        if delivery:
            ctx["delivery_preference"] = delivery
        if address:
            ctx["address"] = address

        # Keep only last 30 messages
        if len(ctx["messages"]) > 30:
            ctx["messages"] = ctx["messages"][-30:]

        # Track topics
        if intent:
            ctx["topics_discussed"].add(intent)

    def get_recent(self, session_id: str, count: int = 5) -> List[str]:
        """Get recent messages."""
        ctx = self.get(session_id)
        return [m["text"] for m in ctx["messages"][-count:]]

    def get_context_summary(self, session_id: str) -> str:
        """Get human-readable context summary."""
        ctx = self.get(session_id)
        parts = []
        if ctx["last_product"]:
            parts.append(f"Product: {ctx['last_product']}")
        if ctx["last_price"]:
            parts.append(f"Price: Rs.{ctx['last_price']}")
        if ctx["last_quantity"]:
            parts.append(f"Qty: {ctx['last_quantity']}")
        if ctx["delivery_preference"]:
            parts.append(f"Delivery: {ctx['delivery_preference']}")
        if ctx["customer_mood"] != "neutral":
            parts.append(f"Mood: {ctx['customer_mood']}")
        return " | ".join(parts) if parts else "No context"


# ============================================================
# 2. EMOTIONAL INTELLIGENCE — Mood Detection + Empathy
# ============================================================

class EmotionalIntelligence:
    """Detects customer mood and generates empathetic responses."""

    MOOD_PATTERNS = {
        "frustrated": {
            "keywords": ["pareshan", "pareshaan", "pak gaya", "pak gai", "thak gaya",
                        "thak gai", "bor ho gaya", "frustrated", "irritated", "annoyed",
                        "bar bar", "baar baar", "kitni baar", "kab se", "kab tak"],
            "weight": 1.3,
        },
        "angry": {
            "keywords": ["gussa", "naraz", "narazgi", "bekar", "bakwas", "fraud",
                        "cheat", "dhoka", "worst", "bura", "kharab", "ghatiya",
                        "paisa barbad", "time barbad", "complaint", "shikayat",
                        "refund", "paisa wapas", "paisa do", "action lunga"],
            "weight": 1.5,
        },
        "sad": {
            "keywords": ["dukhi", "dukh", "sad", "rona", "roye", "ro raha", "ro rahi",
                        "bura laga", "bura laga", "miss", "yaad", "akela", "akeli",
                        "koi nahi", "kuch nahi"],
            "weight": 1.2,
        },
        "happy": {
            "keywords": ["khush", "happy", "accha", "badhiya", "mast", "zabardast",
                        "shandar", "best", "amazing", "wonderful", "excellent", "perfect",
                        "zakkas", "ek number", "first class", "super", "wow"],
            "weight": 1.0,
        },
        "confused": {
            "keywords": ["samajh nahi", "kya hai", "kya matlab", "confused", "samjha nahi",
                        "explain", "detail", "clear nahi", "kaise", "kya kya",
                        "samajh nahi aaya", "pata nahi", "mujhe nahi pata"],
            "weight": 0.8,
        },
        "urgent": {
            "keywords": ["jaldi", "turant", "abhi", "emergency", "urgent", "jaldi karo",
                        "jaldi chahiye", "abhi chahiye", "turant chahiye", "late hoga",
                        "deri", "time nahi", "jaldi batao", "abhi batao"],
            "weight": 1.3,
        },
        "suspicious": {
            "keywords": ["sahi hai", "pakka", "yakeen", "vishwas", "trust", "fraud nahi",
                        "sach mein", "asli", "nakli", "original", "duplicate", "fake"],
            "weight": 1.1,
        },
        "bargaining": {
            "keywords": ["kam karo", "sasta", "discount", "offer", "deal", "negotiate",
                        "kuch kam", "kuch sasta", "rate kam", "price kam", "adjust"],
            "weight": 1.0,
        },
    }

    EMPATHY_RESPONSES = {
        "frustrated": [
            "Samajh sakta hoon {name}, aap pareshan hain. Main aapki puri help karunga!",
            "{name}, mujhe pata hai frustrating hai. Chinta mat karo, solve karenge!",
            "Sorry {name} ke aapko pareshani ho rahi hai. Bataiye kya hua?",
        ],
        "angry": [
            "Maaf karo {name}! Aapka gussa bilkul justified hai. Main solve karta hoon.",
            "{name}, mujhe pata hai aap naraz hain. Humari team aapki help karegi.",
            "Sorry {name}! Ye galat hua. Main complaint file karta hoon abhi.",
        ],
        "sad": [
            "Kya hua {name}? Bataiye, main help karunga. Aap akela nahi hain!",
            "{name}, sad mat ho. Hum hain na! Bataiye kya chahiye?",
            "Dukhi mat ho {name}. Sab theek ho jayega. Bataiye kaise help karu?",
        ],
        "happy": [
            "Bahut accha {name}! Khushi hui sun ke! 😊",
            "Wow {name}, great! Aur kuch chahiye toh batao!",
            "{name}, ye sun ke maza aa gaya! Aur kya help karu?",
        ],
        "confused": [
            "Koi baat nahi {name}, main samjha deta hoon. Dhyan se suno!",
            "{name}, confusion ho gayi? Koi nahi, step by step samjhata hoon.",
            "Samajh nahi aaya {name}? Main detail mein bataata hoon.",
        ],
        "urgent": [
            "Turant {name}! Main abhi dekhta hoon. Jaldi solve karenge!",
            "Haan {name}, jaldi! Abhi process karta hoon.",
            "Bilkul {name}, urgent hai na? Abhi kar deta hoon!",
        ],
        "suspicious": [
            "Pakka {name}! Hum 100% genuine hain. Aap check kar sakte hain.",
            "{name}, trust karo. Humara business 5 saal se chal raha hai.",
            "Bilkul asli {name}! Aap store pe aa ke dekh sakte hain.",
        ],
        "bargaining": [
            "Samajh sakta hoon {name}. Lekin price fixed hai. Quality ke liye sahi rate hai!",
            "{name}, price toh fixed hai. Lekin combo offer de sakta hoon!",
            "Maaf karo {name}, price kam nahi hoga. Lekin bulk order pe discount milega!",
        ],
    }

    def detect(self, message: str) -> Tuple[str, float]:
        """Detect customer mood from message."""
        msg = message.lower().strip()
        scores = {}

        for mood, config in self.MOOD_PATTERNS.items():
            score = 0.0
            for kw in config["keywords"]:
                if kw in msg:
                    score += config["weight"]
            if score > 0:
                scores[mood] = score

        if not scores:
            return ("neutral", 0.0)

        best = max(scores, key=scores.get)
        return (best, round(scores[best], 2))

    def respond(self, mood: str, name: str) -> Optional[str]:
        """Get empathetic response for detected mood."""
        if mood in self.EMPATHY_RESPONSES:
            templates = self.EMPATHY_RESPONSES[mood]
            return random.choice(templates).format(name=name)
        return None


# ============================================================
# 3. BUSINESS INTELLIGENCE — Smart Upsell & Suggestions
# ============================================================

class BusinessIntelligence:
    """Smart business logic: upsell, cross-sell, discounts, proactive suggestions."""

    # Product relationships for smart suggestions
    PRODUCT_RELATIONS = {
        "laptop": {
            "related": ["laptop bag", "laptop stand", "cooling pad", "mouse", "keyboard"],
            "upsell": ["SSD upgrade", "RAM upgrade", "antivirus"],
            "maintenance": ["virus removal", "data recovery", "software install"],
        },
        "mobile": {
            "related": ["cover", "tempered glass", "charger", "earphone", "power bank"],
            "upsell": ["screen guard", "wireless charger", "bluetooth earphone"],
            "maintenance": ["screen repair", "battery replacement", "software update"],
        },
        "haircut": {
            "related": ["hair spa", "hair oil", "shampoo", "conditioner"],
            "upsell": ["facial", "cleanup", "head massage"],
            "maintenance": ["hair treatment", "dandruff treatment"],
        },
        "facial": {
            "related": ["cleanup", "face pack", "moisturizer", "sunscreen"],
            "upsell": ["bridal facial", "gold facial", "diamond facial"],
            "maintenance": ["skin treatment", "acne treatment"],
        },
        "mouse": {
            "related": ["keyboard", "mouse pad", "usb hub"],
            "upsell": ["wireless mouse", "gaming mouse"],
            "maintenance": [],
        },
        "keyboard": {
            "related": ["mouse", "keyboard cover", "wrist rest"],
            "upsell": ["mechanical keyboard", "wireless keyboard"],
            "maintenance": [],
        },
        "printer": {
            "related": ["paper", "ink cartridge", "toner"],
            "upsell": ["scanner", "copier"],
            "maintenance": ["printer repair", "cartridge refill"],
        },
    }

    # Discount rules
    DISCOUNT_RULES = {
        "bulk": {"min_qty": 5, "discount": 10, "message": "Bulk order ke liye {discount}% discount milega!"},
        "loyalty": {"min_visits": 3, "discount": 5, "message": "Aap regular customer hain — {discount}% special discount!"},
        "first_time": {"discount": 10, "message": "Pehli baar aaye ho — {discount}% welcome discount!"},
        "combo": {"discount": 15, "message": "Combo offer: {discount}% off!"},
    }

    def get_suggestion(self, product: str, inventory: list = None) -> Optional[str]:
        """Get smart business suggestion based on product."""
        product_lower = product.lower()

        for key, relations in self.PRODUCT_RELATIONS.items():
            if key in product_lower:
                # Cross-sell related products
                related = relations.get("related", [])
                if related and inventory:
                    for r in related:
                        for item in inventory:
                            if r in item["name"].lower():
                                return f"{item['name']} bhi le lo — combo price Rs.{item['price']}! Saath mein use karoge toh aur accha lagega."

                # Upsell suggestions
                upsell = relations.get("upsell", [])
                if upsell:
                    return f"{product} ke saath {upsell[0]} bhi try karo — bahut difference aayega!"

                # Maintenance suggestions
                maintenance = relations.get("maintenance", [])
                if maintenance:
                    return f"Regular {maintenance[0]} karwao — {product} ki life badh jayegi!"

        return None

    def get_discount_offer(self, customer_type: str = "regular", quantity: int = 1,
                           total_spent: float = 0, visit_count: int = 1) -> Optional[str]:
        """Get discount offer based on customer profile."""
        offers = []

        # Bulk discount
        if quantity >= self.DISCOUNT_RULES["bulk"]["min_qty"]:
            discount = self.DISCOUNT_RULES["bulk"]["discount"]
            offers.append(f"Bulk order: {quantity} pieces ke liye {discount}% off!")

        # Loyalty discount
        if visit_count >= self.DISCOUNT_RULES["loyalty"]["min_visits"]:
            discount = self.DISCOUNT_RULES["loyalty"]["discount"]
            offers.append(f"Regular customer: {discount}% special discount!")

        # First-time discount
        if visit_count == 1:
            discount = self.DISCOUNT_RULES["first_time"]["discount"]
            offers.append(f"Welcome offer: {discount}% off on first order!")

        # Combo discount
        if quantity >= 2:
            discount = self.DISCOUNT_RULES["combo"]["discount"]
            offers.append(f"Combo offer: {discount}% off on 2+ items!")

        return " | ".join(offers) if offers else None

    def get_proactive_suggestion(self, context: Dict) -> Optional[str]:
        """Get proactive suggestion based on conversation context."""
        # Customer discussed product but didn't order
        if context.get("last_product") and context.get("turn_count", 0) > 3:
            if "order" not in context.get("intents", []):
                return f"Agar {context['last_product']} pasand aaya toh order karo — jaldi deliver ho jayega!"

        # Customer asked about price multiple times
        price_intents = [i for i in context.get("intents", []) if i == "price_inquiry"]
        if len(price_intents) >= 2:
            return "Price kaafi baar pucha hai — kya koi doubt hai? Detail mein bataata hoon!"

        # Customer has complaints
        if len(context.get("complaints", [])) > 0:
            return "Pehle complaint thi — kya ab sab theek hai? Feedback do!"

        return None


# ============================================================
# 4. CULTURAL AWARENESS — Indian Business Customs
# ============================================================

class CulturalAwareness:
    """Indian business customs, festivals, time-based greetings."""

    def get_greeting(self, name: str, business_name: str = "Business") -> str:
        """Get culturally appropriate greeting based on time."""
        hour = datetime.now().hour
        month = datetime.now().month
        day = datetime.now().day

        # Time-based greeting
        if hour < 12:
            time_greeting = "Subah"
            emoji = "🌅"
        elif hour < 17:
            time_greeting = "Dopahar"
            emoji = "☀️"
        elif hour < 21:
            time_greeting = "Shaam"
            emoji = "🌇"
        else:
            time_greeting = "Raat"
            emoji = "🌙"

        # Festival detection (Indian festivals by month)
        festival = self._detect_festival(month, day)

        if festival:
            return f"{emoji} {festival} {name} ji! {business_name} mein aapka swagat hai! Kya chahiye?"

        # Regular time-based greeting
        greetings = [
            f"{emoji} {time_greeting} {name} ji! {business_name} mein swagat hai! Kya help karu?",
            f"Namaste {name} ji! {time_greeting} hai — kya order karna hai?",
            f"{emoji} {name} ji, {time_greeting}! Bataiye kya chahiye aapko?",
            f"Ji {name} ji! {time_greeting} — kaise help kar sakta hoon?",
        ]
        return random.choice(greetings)

    def _detect_festival(self, month: int, day: int) -> Optional[str]:
        """Detect Indian festivals by approximate date."""
        festivals = {
            (1, 1): "Happy New Year",
            (1, 14): "Makar Sankranti",
            (1, 26): "Republic Day",
            (3, 8): "Holi",
            (3, 15): "Holi",
            (4, 14): "Baisakhi",
            (4, 15): "Baisakhi",
            (5, 1): "May Day",
            (8, 15): "Independence Day",
            (8, 19): "Raksha Bandhan",
            (8, 20): "Raksha Bandhan",
            (9, 5): "Teacher's Day",
            (9, 15): "Ganesh Chaturthi",
            (10, 2): "Gandhi Jayanti",
            (10, 15): "Dussehra",
            (10, 20): "Dussehra",
            (10, 24): "Diwali",
            (10, 25): "Diwali",
            (10, 26): "Diwali",
            (11, 1): "Diwali",
            (11, 12): "Diwali",
            (12, 25): "Christmas",
        }
        return festivals.get((month, day))

    def get_time_context(self) -> Dict:
        """Get time-based context for responses."""
        now = datetime.now()
        return {
            "hour": now.hour,
            "is_morning": 6 <= now.hour < 12,
            "is_afternoon": 12 <= now.hour < 17,
            "is_evening": 17 <= now.hour < 21,
            "is_night": now.hour >= 21 or now.hour < 6,
            "is_weekend": now.weekday() >= 5,
            "is_month_end": now.day >= 28,
            "is_salary_week": now.day <= 7,
        }


# ============================================================
# 5. SMART SUGGESTIONS — Proactive Recommendations
# ============================================================

class SmartSuggestions:
    """Proactive product/service recommendations."""

    # Seasonal suggestions
    SEASONAL = {
        "summer": {
            "months": [3, 4, 5, 6],
            "suggestions": ["AC repair", "cooler", "fan", "water bottle", "sunscreen", "sunglasses"],
        },
        "monsoon": {
            "months": [6, 7, 8, 9],
            "suggestions": ["umbrella", "raincoat", "waterproof cover", "waterproof bag"],
        },
        "winter": {
            "months": [10, 11, 12, 1, 2],
            "suggestions": ["heater", "blanket", "jacket", "thermos", "hot water bag"],
        },
    }

    # Time-based suggestions
    TIME_SUGGESTIONS = {
        "morning": ["breakfast", "tea", "coffee", "newspaper"],
        "afternoon": ["lunch", "cold drink", "ice cream"],
        "evening": ["snacks", "tea", "biscuit"],
        "night": ["dinner", "milk", "bread"],
    }

    def get_seasonal(self) -> Optional[str]:
        """Get seasonal product suggestion."""
        month = datetime.now().month
        for season, data in self.SEASONAL.items():
            if month in data["months"]:
                items = random.sample(data["suggestions"], min(2, len(data["suggestions"])))
                return f"Season special: {', '.join(items)} available hai!"
        return None

    def get_time_based(self) -> Optional[str]:
        """Get time-based suggestion."""
        hour = datetime.now().hour
        if hour < 12:
            period = "morning"
        elif hour < 17:
            period = "afternoon"
        elif hour < 21:
            period = "evening"
        else:
            period = "night"

        items = self.TIME_SUGGESTIONS.get(period, [])
        if items:
            item = random.choice(items)
            return f"{period.title()} ke liye {item} bhi chahiye?"
        return None

    def get_repeat_suggestion(self, product: str, visit_count: int) -> Optional[str]:
        """Suggest repeat purchase or related product."""
        if visit_count >= 3:
            return f"Phir se {product} chahiye? Aap toh regular customer hain — special price dunga!"
        if visit_count >= 2:
            return f"{product} fir se? Pasand aaya na! Same order kar du?"
        return None


# ============================================================
# 6. NATURAL LANGUAGE — Varied, Human-like Responses
# ============================================================

class NaturalLanguage:
    """Generates varied, human-like, non-robotic responses."""

    # Response templates with variations
    TEMPLATES = {
        "greeting": {
            "formal": [
                "Namaste {name} ji! 🙏 {biz} mein aapka swagat hai. Kaise help kar sakta hoon?",
                "Ji {name} ji! {biz} se bol raha hoon. Bataiye kya chahiye?",
                "{name} ji, namaste! {biz} mein aapka swagat hai. Kya order karna hai?",
            ],
            "casual": [
                "Hey {name}! Kya haal hai? {biz} se bol raha hoon!",
                "Hello {name}! Bataiye kya chahiye aaj?",
                "Hi {name}! Kaise ho? Kya help karu?",
            ],
            "repeat_customer": [
                "Fir se aaye {name} ji! 🙏 Kya chahiye aaj?",
                "{name} ji! Aapka swagat hai fir se. Bataiye kya order karna hai?",
                "Welcome back {name}! Aaj kya chahiye?",
            ],
        },
        "product_found": {
            "enthusiastic": [
                "Haan {name}! {product} available hai! 💰 Rs.{price} ka hai. Stock mein hai!",
                "Bilkul {name}! {product} hai hamare paas — Rs.{price}. Abhi le lo!",
                "{name}, good news! {product} hai — Rs.{price}. Pasand aayega!",
            ],
            "informative": [
                "{name}, {product} available hai. Price: Rs.{price}. Stock: {stock} pieces.",
                "Ji {name}, {product} hai. Rs.{price} ka hai. {stock} pieces bache hain.",
                "{name}, {product} mil jayega — Rs.{price} ka hai.",
            ],
            "casual": [
                "Haan bhai {name}, {product} hai! Rs.{price} ka hai. Le lo!",
                "{name}, {product} toh hai hi! Rs.{price}. Pasand aaya?",
                "Bilkul {name}! {product} — Rs.{price}. Stock hai!",
            ],
        },
        "out_of_stock": {
            "apologetic": [
                "Maaf karo {name}, {product} abhi stock mein nahi hai. 😔 Jaldi aayega!",
                "Sorry {name}, {product} khatam ho gaya. Kal tak aa jayega!",
                "{name}, {product} abhi nahi hai. Next week tak aayega. Wait karo!",
            ],
            "helpful": [
                "{name}, {product} toh nahi hai abhi. Lekin {alternate} hai — woh le lo!",
                "Sorry {name}, {product} out of stock hai. {alternate} try karo!",
                "{name}, {product} nahi hai. Lekin similar product hai — {alternate}!",
            ],
        },
        "order_confirm": {
            "excited": [
                "Order confirm ho gaya {name}! 🎉 {product} x{qty} = Rs.{total}. Payment karo!",
                "Done {name}! 🎉 Aapka order pakka: {product} x{qty} = Rs.{total}!",
                "Badhiya {name}! Order set hai! {product} x{qty} = Rs.{total}!",
            ],
            "professional": [
                "{name}, order confirm: {product} x{qty}. Total: Rs.{total}. Payment link bhej raha hoon.",
                "Order placed {name}! {product} x{qty} = Rs.{total}. Payment karo.",
                "{name}, order successful: {product} x{qty} = Rs.{total}.",
            ],
        },
        "price_inquiry": {
            "detailed": [
                "{name}, {product} ka price Rs.{price} hai. Ismein sab kuch included hai!",
                "Ji {name}, {product} Rs.{price} ka hai. Quality best hai!",
                "{name}, {product} ka rate Rs.{price} hai. Market se kam hai!",
            ],
            "negotiation": [
                "{name}, price Rs.{price} hai — fixed hai. Quality ke liye sahi rate hai!",
                "Maaf karo {name}, price toh Rs.{price} hi hai. Lekin combo offer de sakta hoon!",
                "{name}, Rs.{price} ka hai. Kam nahi hoga, lekin value bahut acchi hai!",
            ],
        },
        "complaint": {
            "empathetic": [
                "Maaf karo {name}! 😔 Ye galat hua. Main solve karta hoon. Bataiye kya problem hai?",
                "{name}, mujhe pata hai aap pareshan hain. Chinta mat karo — hum solve karenge!",
                "Sorry {name}! Aapko pareshani hui. Main complaint file karta hoon.",
            ],
            "action_oriented": [
                "{name}, turant action leta hoon. Bataiye kya hua?",
                "Haan {name}, ye galat hua. Abhi solve karta hoon!",
                "{name}, main dekhta hoon. Bataiye detail mein kya problem hai?",
            ],
        },
        "non_business": {
            "polite": [
                "Maaf karo {name}, sirf business ke baare mein baat kar sakta hoon. 😊",
                "Sorry {name}, yeh mere scope mein nahi hai. Product ya service ke baare mein pucho!",
                "{name}, main sirf business help ke liye hoon. Kya product chahiye?",
            ],
        },
        "thanks": {
            "warm": [
                "Khushi hui {name}! 😊 Aur kuch chahiye toh batao!",
                "Shukriya {name}! 🙏 Aapka feedback humari team ke liye bahut zaroori hai.",
                "Thanks {name}! Aap jaise customers se humara business chalta hai! 🙏",
            ],
        },
    }

    def generate(self, template_key: str, style: str = None, **kwargs) -> str:
        """Generate a natural, varied response."""
        if template_key not in self.TEMPLATES:
            return f"{kwargs.get('name', 'Customer')}, kya help chahiye? 🤔"

        templates = self.TEMPLATES[template_key]

        # Select style
        if style and style in templates:
            options = templates[style]
        else:
            # Random style selection
            all_styles = list(templates.values())
            options = random.choice(all_styles)

        # Select template
        template = random.choice(options)

        # Fill in variables
        try:
            return template.format(**kwargs)
        except KeyError:
            return template


# ============================================================
# 7. SMART RESPONDER — Main Orchestrator
# ============================================================

class SmartResponder:
    """
    Main smart reply generator. Orchestrates all components
    for ultra-intelligent, contextual, human-like responses.
    """

    def __init__(self):
        self.memory = ConversationMemory()
        self.emotion = EmotionalIntelligence()
        self.business = BusinessIntelligence()
        self.culture = CulturalAwareness()
        self.suggestions = SmartSuggestions()
        self.natural = NaturalLanguage()

    def respond(
        self,
        message: str,
        customer_name: str = "Customer",
        session_id: str = None,
        customer_id: str = None,
        inventory: list = None,
        business_name: str = "Business",
        intent: str = "unknown",
        entities: Dict = None,
        sentiment: str = "neutral",
        visit_count: int = 1,
        language: str = "hi",
        knowledge_context: str = None,
    ) -> Optional[str]:
        """
        Generate a smart, contextual reply.

        Pipeline:
        1. Update conversation memory
        2. Detect emotional state
        3. Check for context-aware responses
        4. Generate natural response
        5. Add business intelligence (upsell, suggestions)
        """
        # SmartResponder only has Hindi/English templates
        # For other languages, return None so Falcon engine uses main handler
        if language not in ("hi", "en"):
            return None

        entities = entities or {}
        session_id = session_id or f"default_{customer_name}"

        # Step 1: Update conversation memory
        self.memory.update(
            session_id,
            message=message,
            intent=intent,
            product=entities.get("product", {}).get("name") if entities.get("product") else None,
            price=entities.get("product", {}).get("price") if entities.get("product") else None,
            quantity=entities.get("quantity"),
        )

        # Step 2: Detect emotional state
        mood, mood_score = self.emotion.detect(message)
        ctx = self.memory.get(session_id)

        # Step 3: Handle emotional responses first
        if mood in ("angry", "frustrated", "sad") and mood_score > 1.0:
            empathy = self.emotion.respond(mood, customer_name)
            if empathy:
                # Add context-aware follow-up
                if ctx.get("last_product"):
                    empathy += f"\n\n{ctx['last_product']} ke baare mein bataiye — main solve karta hoon."
                return empathy

        # Step 4: Handle based on intent
        response = None

        if intent == "greeting":
            if visit_count >= 3:
                response = self.natural.generate("greeting", "repeat_customer",
                                                  name=customer_name, biz=business_name)
            elif visit_count >= 2:
                response = self.natural.generate("greeting", "casual",
                                                  name=customer_name, biz=business_name)
            else:
                response = self.natural.generate("greeting", "formal",
                                                  name=customer_name, biz=business_name)

        elif intent == "product_inquiry":
            product = entities.get("product")
            if product:
                if product.get("stock", 0) == 0:
                    response = self.natural.generate("out_of_stock", "apologetic",
                                                      name=customer_name, product=product["name"])
                else:
                    style = "enthusiastic" if mood == "happy" else "informative"
                    response = self.natural.generate("product_found", style,
                                                      name=customer_name,
                                                      product=product["name"],
                                                      price=product["price"],
                                                      stock=product.get("stock", 0))

        elif intent == "price_inquiry":
            product = entities.get("product")
            if product:
                style = "negotiation" if mood == "bargaining" else "detailed"
                response = self.natural.generate("price_inquiry", style,
                                                  name=customer_name,
                                                  product=product["name"],
                                                  price=product["price"])

        elif intent == "order_intent":
            product = entities.get("product")
            if product:
                qty = entities.get("quantity", 1)
                total = product["price"] * qty
                response = self.natural.generate("order_confirm", "excited",
                                                  name=customer_name,
                                                  product=product["name"],
                                                  qty=qty, total=total)

        elif intent == "complaint":
            response = self.natural.generate("complaint", "empathetic",
                                              name=customer_name)
            ctx["complaints"].append(message)

        elif intent == "non_business":
            response = self.natural.generate("non_business", "polite",
                                              name=customer_name)

        elif intent == "feedback":
            response = self.natural.generate("thanks", "warm",
                                              name=customer_name)
            ctx["positive_feedback"].append(message)

        # Step 5: Add business intelligence
        if response:
            # Add upsell suggestion
            product = entities.get("product")
            if product and intent in ("order_intent", "product_inquiry"):
                suggestion = self.business.get_suggestion(product.get("name", ""), inventory)
                if suggestion:
                    response += f"\n\n💡 {suggestion}"

            # Add discount offer
            discount = self.business.get_discount_offer(
                quantity=entities.get("quantity", 1),
                visit_count=visit_count,
            )
            if discount and intent in ("order_intent", "discount_inquiry"):
                response += f"\n\n🎁 {discount}"

            # Add proactive suggestion
            proactive = self.business.get_proactive_suggestion(ctx)
            if proactive and ctx["turn_count"] > 2:
                response += f"\n\n{proactive}"

        return response


# ============================================================
# GLOBAL INSTANCE
# ============================================================

_smart_responder = None

def get_smart_responder() -> SmartResponder:
    """Get singleton Smart Responder instance."""
    global _smart_responder
    if _smart_responder is None:
        _smart_responder = SmartResponder()
    return _smart_responder
