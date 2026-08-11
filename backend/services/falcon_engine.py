"""
Falcon Engine v2.0 — Advanced Rule-Based AI Engine
====================================================
No API key needed. Pure Python intelligence.

Features:
1. Intent Classifier — weighted scoring, 15+ intents
2. Entity Extraction — product, qty, price, date, time, address
3. Context Memory — conversation state across messages
4. Fuzzy Matching — typo tolerance (maus → Mouse)
5. Sentiment Detection — angry/happy/confused/urgent
6. Multi-turn Flow — booking → confirmation → payment state machine
7. Response Variations — natural, varied responses
8. Upsell Engine — combo suggestions, cross-selling
9. Customer Profiling — repeat customer VIP treatment
10. Analytics — track queries, products, conversion

Author: Falcon AI Engine
Version: 2.0
"""

import re
import json
import hashlib
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict


# ============================================================
# 1. INTENT CLASSIFIER — Weighted Scoring
# ============================================================

class IntentClassifier:
    """Classifies customer intent using weighted keyword scoring."""

    INTENTS = {
        "greeting": {
            "keywords": {
                "hello": 1.0, "hi": 1.0, "hey": 1.0, "namaste": 1.0, "namaskar": 1.0,
                "good morning": 0.9, "good evening": 0.9, "good afternoon": 0.9,
                "kaise ho": 0.8, "kaisa hai": 0.8, "kya haal": 0.8,
                "hii": 1.0, "helo": 0.8, "hlw": 0.8, "hlo": 0.8,
            },
            "priority": 1,
        },
        "product_inquiry": {
            "keywords": {
                "chahiye": 0.9, "kya hai": 0.8, "kya hai": 0.8, "hai kya": 0.8,
                "do you have": 0.9, "available": 0.8, "stock": 0.7, "mil": 0.7,
                "product": 0.6, "item": 0.6, "maal": 0.7, "saman": 0.6,
                "dikhao": 0.8, "batao": 0.6, "bata": 0.5,
            },
            "priority": 2,
        },
        "price_inquiry": {
            "keywords": {
                "price": 1.0, "kitna": 0.9, "kitne": 0.9, "kya price": 1.0,
                "rate": 0.8, "cost": 0.8, "dam": 0.7, "kimat": 0.8,
                "value": 0.6, "lag": 0.6, "lagta": 0.6, "lagna": 0.6,
                "kitne ka": 1.0, "kya rate": 0.9, "kya dam": 0.8,
            },
            "priority": 2,
        },
        "order_intent": {
            "keywords": {
                "order": 1.0, "buy": 1.0, "kharid": 0.9, "lena hai": 0.9,
                "le lunga": 0.8, "kar do": 0.7, "de do": 0.7, "pack karo": 0.8,
                "purchase": 0.9, "book": 0.8, "order karo": 1.0, "dedo": 0.7,
                "chahiye tha": 0.8, "mujhe chahiye": 0.9, "muje chahiye": 0.9,
                "mujhe ye chahiye": 0.9, "ye chahiye": 0.8,
                "karna hai": 0.9, "karvana hai": 0.9, "karwana hai": 0.9,
                "karna chahta": 0.8, "karna chahti": 0.8, "karunga": 0.7,
                "mujha": 0.7, "mujhe": 0.7, "muje": 0.7, "hume": 0.7,
            },
            "priority": 3,
        },
        "quantity_specify": {
            "keywords": {
                "1": 0.6, "2": 0.6, "3": 0.6, "4": 0.6, "5": 0.6,
                "ek": 0.7, "do": 0.6, "teen": 0.6, "char": 0.6, "paanch": 0.6,
                "10": 0.5, "20": 0.5, "50": 0.5, "100": 0.5,
                "piece": 0.7, "pieces": 0.7, "pc": 0.7, "pcs": 0.7,
                "unit": 0.7, "box": 0.6, "pack": 0.6, "packet": 0.6,
            },
            "priority": 4,
        },
        "delivery_inquiry": {
            "keywords": {
                "delivery": 1.0, "deliver": 0.9, "ghar": 0.7, "bhejo": 0.8,
                "home": 0.7, "address": 0.8, "pata": 0.6, "bhej": 0.7,
                "courier": 0.8, "ship": 0.7, "shipping": 0.7,
                "cod": 0.8, "cash on delivery": 1.0,
            },
            "priority": 3,
        },
        "pickup_inquiry": {
            "keywords": {
                "pickup": 1.0, "pick": 0.7, "store": 0.7, "dukaan": 0.8,
                "le jaunga": 0.9, "khud lunga": 0.9, "aake lunga": 0.8,
                "aakar lunga": 0.8, "counter": 0.7,
            },
            "priority": 3,
        },
        "service_booking": {
            "keywords": {
                "book": 1.0, "booking": 1.0, "appointment": 0.9, "slot": 0.8,
                "kab": 0.6, "time": 0.6, "timing": 0.7, "din": 0.5,
                "kal": 0.6, "aaj": 0.6, "subah": 0.6, "shaam": 0.6,
                "facial": 0.8, "haircut": 0.8, "massage": 0.8, "spa": 0.8,
            },
            "priority": 3,
        },
        "complaint": {
            "keywords": {
                "complaint": 1.0, "shikayat": 0.9, "problem": 0.8, "issue": 0.8,
                "kharab": 0.8, "kharab hai": 0.9, "theek nahi": 0.8,
                "kaam nahi": 0.8, "nahi chal": 0.7, "nahi ho": 0.6,
                "gussa": 0.7, "naraz": 0.7, "pareshan": 0.6,
                "refund": 0.9, "exchange": 0.8, "replace": 0.8, "warranty": 0.8,
            },
            "priority": 5,
        },
        "feedback": {
            "keywords": {
                "feedback": 1.0, "review": 0.9, "rating": 0.8, "kaisa laga": 0.8,
                "accha hai": 0.7, "bahut accha": 0.8, "best": 0.7, "worst": 0.8,
                "thanks": 0.6, "thank you": 0.7, "shukriya": 0.6, "dhanyavaad": 0.6,
                "badhiya": 0.7, "mast": 0.6, "zabardast": 0.7,
            },
            "priority": 4,
        },
        "discount_inquiry": {
            "keywords": {
                "discount": 1.0, "offer": 0.9, "sasta": 0.8, "sasti": 0.8,
                "kam": 0.6, "kam karo": 0.8, "negotiate": 0.8, "deal": 0.7,
                "coupon": 0.9, "promo": 0.8, "sale": 0.7, "offer hai": 0.8,
                "kuch kam": 0.8, "kuch discount": 0.9, "kuch sasta": 0.9,
            },
            "priority": 3,
        },
        "payment_inquiry": {
            "keywords": {
                "payment": 1.0, "pay": 0.7, "upi": 0.9, "gpay": 0.9, "phonepe": 0.9,
                "paytm": 0.9, "online": 0.6, "cash": 0.7, "card": 0.7,
                "kaise pay": 0.9, "kaise pay karu": 1.0, "payment kaise": 0.9,
                "account": 0.6, "bank": 0.6, "transfer": 0.7,
            },
            "priority": 3,
        },
        "location_inquiry": {
            "keywords": {
                "kahan": 0.8, "kaha": 0.7, "kaha hai": 0.8, "location": 0.9,
                "address": 0.8, "map": 0.7, "direction": 0.7, "kaise aau": 0.9,
                "google maps": 0.8, "shop": 0.5, "store": 0.5,
            },
            "priority": 2,
        },
        "hours_inquiry": {
            "keywords": {
                "timing": 0.9, "kab khula": 0.9, "kab band": 0.9, "kab tak": 0.8,
                "kitne baje": 0.8, "open": 0.6, "close": 0.6, "hours": 0.7,
                "sunday": 0.6, "holiday": 0.7, "chhuti": 0.6,
            },
            "priority": 2,
        },
        "non_business": {
            "keywords": {
                "joke": 0.9, "mazak": 0.8, "hasi": 0.7, "funny": 0.7,
                "story": 0.7, "kahani": 0.7, "song": 0.7, "gaana": 0.7,
                "poem": 0.7, "shayari": 0.7, "cricket": 0.7, "movie": 0.7,
                "politics": 0.7, "news": 0.6, "weather": 0.6,
            },
            "priority": 0,
        },
    }

    def classify(self, message: str) -> Tuple[str, float]:
        """Classify message intent. Returns (intent, confidence)."""
        msg = message.lower().strip()
        scores = {}

        for intent, config in self.INTENTS.items():
            score = 0.0
            for keyword, weight in config["keywords"].items():
                if keyword in msg:
                    score += weight
            if score > 0:
                scores[intent] = score * config["priority"]

        if not scores:
            return ("unknown", 0.0)

        best_intent = max(scores, key=scores.get)
        max_possible = max(config["priority"] * len(config["keywords"]) for config in self.INTENTS.values())
        confidence = min(scores[best_intent] / max_possible * 10, 1.0)
        return (best_intent, round(confidence, 2))


# ============================================================
# 2. ENTITY EXTRACTION
# ============================================================

class EntityExtractor:
    """Extracts entities from messages: product, qty, price, date, time, address."""

    def extract(self, message: str, inventory: list = None) -> Dict[str, Any]:
        """Extract all entities from message."""
        entities = {}

        # Quantity
        qty = self._extract_quantity(message)
        if qty:
            entities["quantity"] = qty

        # Price mention
        price = self._extract_price(message)
        if price:
            entities["mentioned_price"] = price

        # Date
        date_val = self._extract_date(message)
        if date_val:
            entities["date"] = date_val

        # Time
        time_val = self._extract_time(message)
        if time_val:
            entities["time"] = time_val

        # Address
        address = self._extract_address(message)
        if address:
            entities["address"] = address

        # Product match from inventory
        if inventory:
            product = self._match_product(message, inventory)
            if product:
                entities["product"] = product

        # Phone number
        phone = self._extract_phone(message)
        if phone:
            entities["phone"] = phone

        return entities

    def _extract_quantity(self, msg: str) -> Optional[int]:
        """Extract quantity from message."""
        # Direct number patterns
        patterns = [
            r'(\d+)\s*(?:pc|pcs|piece|pieces|unit|units|box|boxes|pack|packs|packet|packets|set|sets|bottle|bottles)',
            r'(?:qty|quantity|kitna|kitne|kitni)\s*[:=]?\s*(\d+)',
            r'^(?:x|×)?(\d+)$',  # Just a number
        ]
        for pattern in patterns:
            m = re.search(pattern, msg.lower())
            if m:
                return int(m.group(1))

        # Hindi number words
        hindi_nums = {"ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
                      "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10}
        for word, num in hindi_nums.items():
            if re.search(r'\b' + word + r'\b', msg.lower()):
                return num

        return None

    def _extract_price(self, msg: str) -> Optional[float]:
        """Extract price mentioned by customer."""
        patterns = [
            r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rupaye|rupees|rs|inr)',
            r'(?:price|rate|cost|kitna|kitne)\s*[:=]?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        ]
        for pattern in patterns:
            m = re.search(pattern, msg.lower())
            if m:
                price_str = m.group(1).replace(",", "")
                try:
                    return float(price_str)
                except ValueError:
                    continue
        return None

    def _extract_date(self, msg: str) -> Optional[str]:
        """Extract date from message."""
        msg_lower = msg.lower().strip()
        today = datetime.now()

        if "aaj" in msg_lower or "today" in msg_lower:
            return today.strftime("%Y-%m-%d")
        if "kal" in msg_lower or "tomorrow" in msg_lower:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        if "parson" in msg_lower:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")

        # Day names
        days = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6,
                "somvar": 0, "mangalvar": 1, "budhvar": 2, "guruvar": 3,
                "shukravar": 4, "shanivar": 5, "ravivar": 6}
        for day_name, day_num in days.items():
            if day_name in msg_lower:
                current_day = today.weekday()
                days_ahead = (day_num - current_day) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        # Date patterns: DD/MM, DD-MM-YYYY
        m = re.search(r'(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?', msg)
        if m:
            day, month = int(m.group(1)), int(m.group(2))
            year = int(m.group(3)) if m.group(3) else today.year
            if year < 100:
                year += 2000
            try:
                return f"{year}-{month:02d}-{day:02d}"
            except ValueError:
                pass

        return None

    def _extract_time(self, msg: str) -> Optional[str]:
        """Extract time from message."""
        msg_lower = msg.lower().strip()

        # Time patterns
        patterns = [
            (r'(\d{1,2}):(\d{2})\s*(am|pm)', lambda m: f"{int(m.group(1))}:{m.group(2)} {m.group(3).upper()}"),
            (r'(\d{1,2})\s*(am|pm)', lambda m: f"{int(m.group(1))}:00 {m.group(2).upper()}"),
            (r'(\d{1,2})\s*baje', lambda m: f"{int(m.group(1))}:00"),
            (r'(\d{1,2})\s*baj', lambda m: f"{int(m.group(1))}:00"),
            (r'subah\s*(\d{1,2})', lambda m: f"{int(m.group(1))}:00 AM"),
            (r'dopahar\s*(\d{1,2})', lambda m: f"{int(m.group(1))}:00 PM"),
            (r'shaam\s*(\d{1,2})', lambda m: f"{int(m.group(1))}:00 PM"),
            (r'raat\s*(\d{1,2})', lambda m: f"{int(m.group(1))}:00 PM"),
        ]
        for pattern, formatter in patterns:
            m = re.search(pattern, msg_lower)
            if m:
                return formatter(m)

        return None

    def _extract_address(self, msg: str) -> Optional[str]:
        """Extract address from message."""
        address_keywords = ["road", "street", "lane", "nagar", "colony", "area",
                           "city", "pin", "pincode", "flat", "house", "apartment",
                           "floor", "building", "society", "sector", "block",
                           "mandir", "masjid", "school", "hospital", "market"]
        msg_lower = msg.lower()
        if any(kw in msg_lower for kw in address_keywords):
            # Check if it looks like an address (has numbers + area words)
            if re.search(r'\d+.*(?:road|street|lane|nagar|colony|area|flat|house|building)', msg_lower):
                return msg.strip()
            if len(msg.split()) >= 4:  # Multi-word with address keywords
                return msg.strip()
        return None

    def _extract_phone(self, msg: str) -> Optional[str]:
        """Extract phone number from message."""
        m = re.search(r'(\+91|91|0)?(\d{10})', msg)
        if m:
            return m.group(2)
        return None

    def _match_product(self, msg: str, inventory: list) -> Optional[Dict]:
        """Match product from inventory using fuzzy matching."""
        msg_lower = msg.lower().strip()
        best_match = None
        best_score = 0.0

        for item in inventory:
            name_lower = item["name"].lower()

            # Exact match
            if name_lower in msg_lower or msg_lower in name_lower:
                return item

            # Word-by-word match
            item_words = set(name_lower.split())
            msg_words = set(msg_lower.split())
            common = item_words & msg_words
            if common and len(common) / len(item_words) > 0.5:
                score = len(common) / len(item_words)
                if score > best_score:
                    best_score = score
                    best_match = item

            # Fuzzy match
            ratio = SequenceMatcher(None, name_lower, msg_lower).ratio()
            if ratio > 0.5 and ratio > best_score:
                best_score = ratio
                best_match = item

        return best_match


# ============================================================
# 3. CONTEXT MEMORY
# ============================================================

class ContextMemory:
    """Tracks conversation state across messages."""

    def __init__(self):
        self._sessions: Dict[str, Dict] = {}

    def get_context(self, session_id: str) -> Dict:
        """Get conversation context for session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "messages": [],
                "current_intent": None,
                "current_product": None,
                "current_quantity": None,
                "current_price": None,
                "delivery_type": None,
                "address": None,
                "date": None,
                "time": None,
                "stage": "initial",  # initial → product_selected → quantity_set → delivery_chosen → confirmed
                "turn_count": 0,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "topics": [],
            }
        return self._sessions[session_id]

    def update(self, session_id: str, **kwargs):
        """Update conversation context."""
        ctx = self.get_context(session_id)
        ctx.update(kwargs)
        ctx["turn_count"] += 1
        ctx["last_seen"] = datetime.now().isoformat()
        ctx["messages"].append(kwargs.get("message", ""))
        if len(ctx["messages"]) > 20:
            ctx["messages"] = ctx["messages"][-20:]

    def set_stage(self, session_id: str, stage: str):
        """Update conversation stage."""
        ctx = self.get_context(session_id)
        ctx["stage"] = stage

    def get_stage(self, session_id: str) -> str:
        """Get current conversation stage."""
        return self.get_context(session_id)["stage"]

    def clear(self, session_id: str):
        """Clear session context."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_recent_messages(self, session_id: str, count: int = 5) -> List[str]:
        """Get recent messages from context."""
        ctx = self.get_context(session_id)
        return ctx["messages"][-count:]


# ============================================================
# 4. FUZZY MATCHER
# ============================================================

class FuzzyMatcher:
    """Typo tolerance for product names and commands."""

    # Common typo corrections
    TYPO_MAP = {
        "maus": "mouse", "mause": "mouse", "mos": "mouse", "mous": "mouse",
        "keybord": "keyboard", "keybrd": "keyboard", "keyb": "keyboard",
        "lapy": "laptop", "laprop": "laptop", "labtop": "laptop", "laptp": "laptop",
        "moniter": "monitor", "monitor": "monitor", "montr": "monitor",
        "priter": "printer", "prnter": "printer", "printr": "printer",
        "tabllet": "tablet", "tabl": "tablet", "tablit": "tablet",
        "mobil": "mobile", "mobail": "mobile", "moble": "mobile",
        "hedphone": "headphone", "headfone": "headphone", "headfon": "headphone",
        "camra": "camera", "cam": "camera",
        "speeker": "speaker", "spkr": "speaker", "spkr": "speaker",
        "chargr": "charger", "charger": "charger", "chargar": "charger",
        "cabl": "cable", "cabel": "cable",
        "bag": "bag", "beg": "bag",
        "shoo": "shoe", "shu": "shoe",
        "wach": "watch", "watch": "watch", "wotch": "watch",
        "accha": "accha", "acha": "accha", "achha": "accha",
        "kharab": "kharab", "khrab": "kharab", "kharb": "kharab",
        "facial": "facial", "faisal": "facial", "faciel": "facial",
        "haircut": "haircut", "hairkat": "haircut", "hairkt": "haircut",
        "masaj": "massage", "masage": "massage", "msg": "massage",
    }

    def correct(self, text: str) -> str:
        """Correct common typos in text."""
        words = text.lower().split()
        corrected = []
        for word in words:
            clean = re.sub(r'[^\w]', '', word)
            if clean in self.TYPO_MAP:
                corrected.append(self.TYPO_MAP[clean])
            else:
                corrected.append(word)
        return " ".join(corrected)

    def match_product(self, query: str, inventory: list, threshold: float = 0.5) -> Optional[Dict]:
        """Match product from inventory with typo tolerance."""
        query_corrected = self.correct(query.lower())
        query_words = set(query_corrected.split())

        best_match = None
        best_score = 0.0

        for item in inventory:
            name_lower = item["name"].lower()
            name_words = set(name_lower.split())

            # Exact match after correction
            if name_lower in query_corrected or query_corrected in name_lower:
                return item

            # Word overlap
            common = query_words & name_words
            if common:
                score = len(common) / max(len(query_words), len(name_words))
                if score > best_score:
                    best_score = score
                    best_match = item

            # Fuzzy match on full string
            ratio = SequenceMatcher(None, name_lower, query_corrected).ratio()
            if ratio > threshold and ratio > best_score:
                best_score = ratio
                best_match = item

        return best_match if best_score >= threshold else None


# ============================================================
# 5. SENTIMENT DETECTOR
# ============================================================

class SentimentDetector:
    """Detects customer sentiment: angry, happy, confused, urgent, neutral."""

    PATTERNS = {
        "angry": {
            "keywords": ["gussa", "naraz", "pareshan", "bekar", "bakwas", "fraud",
                        "cheat", "dhoka", "worst", "bad", "bura", "kharab", "ghatiya",
                        "complaint", "shikayat", "refund", "paisa wapas", "paisa do"],
            "emojis": ["😡", "🤬", "😤", "💢"],
            "weight": 1.5,
        },
        "happy": {
            "keywords": ["accha", "badhiya", "mast", "zabardast", "shandar", "best",
                        "amazing", "wonderful", "excellent", "perfect", "zakkas",
                        "khush", "happy", "thanks", "thank you", "shukriya"],
            "emojis": ["😊", "😄", "👍", "❤️", "🥰", "😍"],
            "weight": 1.0,
        },
        "confused": {
            "keywords": ["samajh nahi", "kya hai", "kya matlab", "confused",
                        "samjha nahi", "explain", "detail", "clear nahi",
                        "kaise", "kya kya", "samajh nahi aaya"],
            "emojis": ["😕", "🤔", "❓"],
            "weight": 0.8,
        },
        "urgent": {
            "keywords": ["jaldi", "turant", "abhi", "emergency", "urgent",
                        "jaldi karo", "jaldi chahiye", "abhi chahiye", "turant chahiye",
                        "late hoga", "deri", "time nahi"],
            "emojis": ["⚡", "🚨", "⏰"],
            "weight": 1.3,
        },
    }

    def detect(self, message: str) -> Tuple[str, float]:
        """Detect sentiment. Returns (sentiment, score)."""
        msg = message.lower().strip()
        scores = {}

        for sentiment, config in self.PATTERNS.items():
            score = 0.0
            for kw in config["keywords"]:
                if kw in msg:
                    score += config["weight"]
            for emoji in config["emojis"]:
                if emoji in message:
                    score += 0.5
            if score > 0:
                scores[sentiment] = score

        if not scores:
            return ("neutral", 0.0)

        best = max(scores, key=scores.get)
        return (best, round(scores[best], 2))


# ============================================================
# 6. MULTI-TURN FLOW (State Machine)
# ============================================================

class MultiTurnFlow:
    """Manages conversation flow states: product → qty → delivery → confirm."""

    STAGES = [
        "initial",
        "product_selected",
        "quantity_set",
        "delivery_chosen",
        "address_provided",
        "confirmed",
    ]

    TRANSITIONS = {
        "initial": {
            "product_inquiry": "product_selected",
            "order_intent": "product_selected",
            "service_booking": "product_selected",
        },
        "product_selected": {
            "quantity_specify": "quantity_set",
            "order_intent": "quantity_set",
        },
        "quantity_set": {
            "delivery_inquiry": "delivery_chosen",
            "pickup_inquiry": "delivery_chosen",
        },
        "delivery_chosen": {
            "address_provided": "address_provided",
            "confirm": "confirmed",
        },
        "address_provided": {
            "confirm": "confirmed",
        },
    }

    def get_next_stage(self, current_stage: str, intent: str) -> Optional[str]:
        """Get next stage based on current stage and intent."""
        if current_stage in self.TRANSITIONS:
            return self.TRANSITIONS[current_stage].get(intent)
        return None

    def get_stage_prompt(self, stage: str, context: Dict) -> str:
        """Get prompt for current stage."""
        prompts = {
            "initial": "Kya chahiye aapko? Product ka naam batao!",
            "product_selected": f"Aapko {context.get('current_product', 'ye product')} chahiye. Kitne pieces?",
            "quantity_set": f"{context.get('current_quantity', 1)} piece. Delivery ya Pickup?",
            "delivery_chosen": "Address batao ya 'Pickup' bolo store se lene ke liye.",
            "address_provided": "Order confirm karna hai? Haan bolo!",
        }
        return prompts.get(stage, "Kya help chahiye?")


# ============================================================
# 7. RESPONSE VARIATOR
# ============================================================

class ResponseVariator:
    """Generates natural, varied responses so bot doesn't sound robotic."""

    TEMPLATES = {
        "greeting": [
            "Namaste {name}! 🙏 Kaise help kar sakta hoon?",
            "Hello {name}! 🙏 {biz} mein aapka swagat hai!",
            "Hi {name}! 🙏 Bataiye kya chahiye aapko?",
            "Namaste {name} ji! 🙏 Aaj kya order karna hai?",
            "Hey {name}! 🙏 Kya haal hai? Bataiye kya madad chahiye?",
        ],
        "product_found": [
            "{name}, {product} available hai! 💰 Price: ₹{price}",
            "Haan {name}, {product} hai hamare paas! 💰 ₹{price}",
            "{name}, {product} mil jayega! 💰 Price ₹{price} hai.",
            "Ji {name}, {product} stock mein hai! 💰 ₹{price}",
        ],
        "out_of_stock": [
            "Maaf karo {name}, {product} abhi stock mein nahi hai. 😔",
            "Sorry {name}, {product} khatam ho gaya. Jaldi aayega! 😊",
            "{name}, {product} abhi nahi hai. Baad mein try karo ya koi aur product dekho!",
        ],
        "order_confirm": [
            "Order confirm ho gaya {name}! 🎉 {product} x{qty} = ₹{total}",
            "Badhiya {name}! 🎉 Aapka order pakka: {product} x{qty} = ₹{total}",
            "Done {name}! 🎉 {product} x{qty} ka order set hai. Total: ₹{total}",
        ],
        "ask_quantity": [
            "{name}, {product} kitne chahiye? Quantity batao!",
            "Kitne pieces chahiye {name}? 🤔",
            "{name}, {product} ke liye quantity batao!",
        ],
        "ask_delivery": [
            "Delivery chahiye ya Pickup? 🤔",
            "{name}, ghar bhej du ya store se le jayenge?",
            "Delivery (₹50 extra) ya Pickup (FREE) — kya pasand?",
        ],
        "non_business": [
            "Maaf karo {name}, sirf business se related baatein kar sakta hoon. 😊",
            "Sorry {name}, yeh mere scope mein nahi hai. Product ya service ke baare mein pucho!",
            "{name}, main sirf business help ke liye hoon. Kya product chahiye?",
        ],
        "feedback_thanks": [
            "Thanks {name}! 🙏 Feedback ke liye shukriya!",
            "Bahut accha {name}! 😊 Aapka feedback humari team ke liye bahut zaroori hai.",
            "Shukriya {name}! 🙏 Aur koi help chahiye?",
        ],
    }

    # Marathi templates — भारतीय ग्राहकांसाठी मराठी उत्तरे
    TEMPLATES_MR = {
        "greeting": [
            "नमस्कार {name}! 🙏 कशी मदत करू?",
            "नमस्कार {name}! 🙏 {biz} मध्ये आपले स्वागत आहे!",
            "नमस्कार {name}! 🙏 सांगा काय पाहिजे तुम्हाला?",
            "नमस्कार {name}! 🙏 आज काय ऑर्डर करायचे आहे?",
            "हॅलो {name}! 🙏 काय चालले आहे? कशी मदत करू?",
        ],
        "product_found": [
            "{name}, {product} उपलब्ध आहे! 💰 किंमत: ₹{price}",
            "हो {name}, {product} आमच्याकडे आहे! 💰 ₹{price}",
            "{name}, {product} मिळेल! 💰 किंमत ₹{price} आहे.",
            "जी {name}, {product} स्टॉकमध्ये आहे! 💰 ₹{price}",
        ],
        "out_of_stock": [
            "माफ करा {name}, {product} आत्ता स्टॉकमध्ये नाही. 😔",
            "सॉरी {name}, {product} संपले. लवकर येणार! 😊",
            "{name}, {product} आत्ता नाही. नंतर बघा किंवा दुसरे प्रोडक्ट पहा!",
        ],
        "order_confirm": [
            "ऑर्डर कन्फर्म झाला {name}! 🎉 {product} x{qty} = ₹{total}",
            "छान {name}! 🎉 तुमचा ऑर्डर पक्का: {product} x{qty} = ₹{total}",
            "झालं {name}! 🎉 {product} x{qty} ऑर्डर सेट आहे. एकूण: ₹{total}",
        ],
        "ask_quantity": [
            "{name}, {product} किती पाहिजे? प्रमाण सांगा!",
            "किती पीस पाहिजे {name}? 🤔",
            "{name}, {product} साठी प्रमाण सांगा!",
        ],
        "ask_delivery": [
            "डिलिव्हरी पाहिजे की पिकअप? 🤔",
            "{name}, घरी पाठवू की स्टोअरवरून घ्याल?",
            "डिलिव्हरी (₹50 अतिरिक्त) किंवा पिकअप (FREE) — काय हवे?",
        ],
        "non_business": [
            "माफ करा {name}, मी फक्त व्यवसायाशी संबंधित गोष्टी बोलू शकतो. 😊",
            "सॉरी {name}, हे माझ्या व्याप्तीत नाही. प्रोडक्ट किंवा सेवेबद्दल विचारा!",
            "{name}, मी फक्त व्यवसाय मदतीसाठी आहे. काय प्रोडक्ट हवे?",
        ],
        "feedback_thanks": [
            "धन्यवाद {name}! 🙏 अभिप्रायासाठी मनःपूर्वक धन्यवाद!",
            "खूप छान {name}! 😊 तुमचा अभिप्राय आमच्या टीमसाठी खूप महत्त्वाचा आहे.",
            "धन्यवाद {name}! 🙏 आणखी काही मदत हवी?",
        ],
    }

    def vary(self, template_key: str, language: str = "hi", **kwargs) -> str:
        """Get a varied response for template key. language='mr' for Marathi."""
        if language == "mr":
            templates = self.TEMPLATES_MR.get(template_key)
        else:
            templates = None
        if not templates:
            templates = self.TEMPLATES.get(template_key, ["{name}, kya help chahiye? 🤔"])
        # Use hash of context to pick consistent but varied response
        hash_input = json.dumps(kwargs, sort_keys=True).encode()
        idx = int(hashlib.md5(hash_input).hexdigest(), 16) % len(templates)
        template = templates[idx]
        try:
            return template.format(**kwargs)
        except KeyError:
            return template


# ============================================================
# 8. UPSELL ENGINE
# ============================================================

class UpsellEngine:
    """Suggests combos, cross-sells, and upsells."""

    # Product combo rules (product_a → suggest product_b)
    COMBO_RULES = {
        "mouse": ["keyboard", "mouse pad", "usb hub"],
        "keyboard": ["mouse", "keyboard cover", "wrist rest"],
        "laptop": ["laptop bag", "laptop stand", "cooling pad", "mouse"],
        "mobile": ["cover", "tempered glass", "charger", "earphone"],
        "earphone": ["earphone case", "earphone cover"],
        "charger": ["cable", "power bank"],
        "haircut": ["hair spa", "hair oil", "shampoo"],
        "facial": ["cleanup", "face pack", "moisturizer"],
        "massage": ["oil", "cream", "spa"],
    }

    # Price-based upsell thresholds
    UPSELL_THRESHOLDS = [
        (500, "Sirf ₹{diff} aur lagao to {upgrade} bhi mil jayega! 🎁"),
        (1000, "₹{diff} extra mein {upgrade} le lo — bahut accha combo hai! 🎁"),
        (2000, "₹{diff} aur lagao to premium {upgrade} free milega! 🎁"),
    ]

    def get_suggestion(self, product_name: str, current_total: float, inventory: list = None) -> Optional[str]:
        """Get upsell/cross-sell suggestion."""
        product_lower = product_name.lower()

        # Combo suggestions
        for key, suggestions in self.COMBO_RULES.items():
            if key in product_lower:
                if inventory:
                    for suggestion in suggestions:
                        for item in inventory:
                            if suggestion in item["name"].lower():
                                return f"💡 {product_name} ke saath {item['name']} bhi le lo — combo price: ₹{item['price']}!"
                return f"💡 {product_name} ke saath {', '.join(suggestions[:2])} bhi available hai!"

        return None

    def get_quantity_suggestion(self, product_name: str, price: float, qty: int) -> Optional[str]:
        """Suggest bulk discount if applicable."""
        if qty >= 10:
            return f"📦 Bulk order ke liye special price — {qty} pieces ke liye contact karo!"
        if qty >= 5:
            discount = min(qty * 2, 15)  # 2% per item, max 15%
            return f"📦 {qty} pieces ke liye {discount}% discount milega! 🎁"
        return None


# ============================================================
# 9. CUSTOMER PROFILER
# ============================================================

class CustomerProfiler:
    """Tracks repeat customers and provides VIP treatment."""

    def __init__(self):
        self._profiles: Dict[str, Dict] = {}

    def get_profile(self, customer_id: str) -> Dict:
        """Get customer profile."""
        if customer_id not in self._profiles:
            self._profiles[customer_id] = {
                "visit_count": 0,
                "total_spent": 0.0,
                "last_visit": None,
                "favorite_products": [],
                "tier": "regular",  # regular, returning, vip, premium
                "complaints": 0,
                "satisfaction": "neutral",
            }
        return self._profiles[customer_id]

    def record_visit(self, customer_id: str, product: str = None, amount: float = 0):
        """Record customer visit."""
        profile = self.get_profile(customer_id)
        profile["visit_count"] += 1
        profile["total_spent"] += amount
        profile["last_visit"] = datetime.now().isoformat()

        if product:
            if product not in profile["favorite_products"]:
                profile["favorite_products"].append(product)
            if len(profile["favorite_products"]) > 5:
                profile["favorite_products"] = profile["favorite_products"][-5:]

        # Update tier
        if profile["visit_count"] >= 20 or profile["total_spent"] >= 10000:
            profile["tier"] = "premium"
        elif profile["visit_count"] >= 10 or profile["total_spent"] >= 5000:
            profile["tier"] = "vip"
        elif profile["visit_count"] >= 3:
            profile["tier"] = "returning"

    def get_greeting(self, customer_id: str, name: str) -> Optional[str]:
        """Get personalized greeting for returning customer."""
        profile = self.get_profile(customer_id)
        tier = profile["tier"]

        if tier == "premium":
            return f"🌟 Welcome back {name} ji! Aap hamare premium customer hain. Aaj kya chahiye?"
        elif tier == "vip":
            return f"⭐ {name} ji! Aapka swagat hai. Pichli baar {profile['favorite_products'][-1] if profile['favorite_products'] else 'kuch'} liya tha — aaj kya chahiye?"
        elif tier == "returning":
            return f"🙏 {name} ji, fir se aaye! Kya order karna hai aaj?"
        return None

    def get_profile_summary(self, customer_id: str) -> str:
        """Get customer profile summary."""
        profile = self.get_profile(customer_id)
        return (
            f"Customer: {customer_id}\n"
            f"Visits: {profile['visit_count']}\n"
            f"Total Spent: ₹{profile['total_spent']}\n"
            f"Tier: {profile['tier']}\n"
            f"Favorites: {', '.join(profile['favorite_products'][-3:])}"
        )


# ============================================================
# 10. FALCON ANALYTICS
# ============================================================

class FalconAnalytics:
    """Tracks queries, products, conversion for analytics."""

    def __init__(self):
        self._data = {
            "total_queries": 0,
            "intents": defaultdict(int),
            "products_queried": defaultdict(int),
            "orders_started": 0,
            "orders_completed": 0,
            "complaints": 0,
            "sentiments": defaultdict(int),
            "hourly_distribution": defaultdict(int),
            "daily_queries": defaultdict(int),
        }

    def track(self, intent: str, product: str = None, sentiment: str = None, converted: bool = False):
        """Track a query event."""
        self._data["total_queries"] += 1
        self._data["intents"][intent] += 1

        if product:
            self._data["products_queried"][product] += 1

        if sentiment:
            self._data["sentiments"][sentiment] += 1

        if intent == "order_intent":
            self._data["orders_started"] += 1

        if converted:
            self._data["orders_completed"] += 1

        if intent == "complaint":
            self._data["complaints"] += 1

        # Hourly distribution
        hour = datetime.now().hour
        self._data["hourly_distribution"][hour] += 1

        # Daily
        day = datetime.now().strftime("%Y-%m-%d")
        self._data["daily_queries"][day] += 1

    def get_summary(self) -> Dict:
        """Get analytics summary."""
        d = self._data
        conversion_rate = (d["orders_completed"] / d["orders_started"] * 100) if d["orders_started"] > 0 else 0
        return {
            "total_queries": d["total_queries"],
            "top_intents": dict(sorted(d["intents"].items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_products": dict(sorted(d["products_queried"].items(), key=lambda x: x[1], reverse=True)[:5]),
            "orders_started": d["orders_started"],
            "orders_completed": d["orders_completed"],
            "conversion_rate": round(conversion_rate, 1),
            "complaints": d["complaints"],
            "sentiment_breakdown": dict(d["sentiments"]),
            "peak_hour": max(d["hourly_distribution"], key=d["hourly_distribution"].get) if d["hourly_distribution"] else None,
        }


# ============================================================
# FALCON ENGINE — Main Orchestrator
# ============================================================

class FalconEngine:
    """
    Falcon Engine v2.0 — Advanced Rule-Based AI Engine
    Orchestrates all components for intelligent customer interaction.
    """

    def __init__(self):
        self.intent = IntentClassifier()
        self.entity = EntityExtractor()
        self.memory = ContextMemory()
        self.fuzzy = FuzzyMatcher()
        self.sentiment = SentimentDetector()
        self.flow = MultiTurnFlow()
        self.variator = ResponseVariator()
        self.upsell = UpsellEngine()
        self.profiler = CustomerProfiler()
        self.analytics = FalconAnalytics()

        # Smart Responder v3.0
        try:
            from services.falcon_smart import get_smart_responder
            self.smart = get_smart_responder()
        except Exception:
            self.smart = None

    def process(
        self,
        message: str,
        customer_name: str = "Customer",
        session_id: str = None,
        customer_id: str = None,
        inventory: list = None,
        order_context: list = None,
        coupon_context: list = None,
        business_name: str = "Business",
        payment_context: dict = None,
        language: str = "hi",
        knowledge_context: str = None,
    ) -> str:
        """
        Main processing pipeline. Takes customer message, returns intelligent reply.
        """
        # Step 0: Smart Responder v3.0 (contextual, emotional, cultural)
        if self.smart:
            try:
                # Correct typos first
                corrected = self.fuzzy.correct(message)
                intent, confidence = self.intent.classify(corrected)
                sentiment, _ = self.sentiment.detect(message)
                entities = self.entity.extract(corrected, inventory)

                smart_reply = self.smart.respond(
                    message=message,
                    customer_name=customer_name,
                    session_id=session_id,
                    customer_id=customer_id,
                    inventory=inventory,
                    business_name=business_name,
                    intent=intent,
                    entities=entities,
                    sentiment=sentiment,
                    visit_count=1,
                    language=language,
                    knowledge_context=knowledge_context,
                )
                if smart_reply:
                    return smart_reply
            except Exception:
                pass  # Fall back to existing logic

        # Step 1: Correct typos
        corrected = self.fuzzy.correct(message)

        # Step 2: Classify intent
        intent, confidence = self.intent.classify(corrected)

        # Step 3: Detect sentiment
        sentiment, sentiment_score = self.sentiment.detect(message)

        # Step 4: Extract entities
        entities = self.entity.extract(corrected, inventory)

        # Step 5: Track analytics
        self.analytics.track(
            intent=intent,
            product=entities.get("product", {}).get("name") if entities.get("product") else None,
            sentiment=sentiment,
        )

        # Step 6: Update context memory
        if session_id:
            self.memory.update(
                session_id,
                message=message,
                intent=intent,
                entities=entities,
                sentiment=sentiment,
            )

        # Step 7: Get customer profile greeting (if returning customer)
        if customer_id:
            profile_greeting = self.profiler.get_greeting(customer_id, customer_name)
            if profile_greeting and intent == "greeting":
                return profile_greeting

        # Step 8: Handle non-business requests
        if intent == "non_business":
            return self.variator.vary("non_business", language=language, name=customer_name)

        # Step 9: Handle sentiment-specific responses
        if sentiment == "angry":
            return self._handle_angry(message, customer_name, entities, inventory)
        if sentiment == "urgent":
            return self._handle_urgent(message, customer_name, entities, inventory)

        # Step 10: Multi-turn flow (if session exists)
        if session_id:
            stage = self.memory.get_stage(session_id)
            next_stage = self.flow.get_next_stage(stage, intent)
            if next_stage:
                self.memory.set_stage(session_id, next_stage)

        # Step 11: Route to intent handler
        response = self._route_intent(intent, message, customer_name, entities,
                                       inventory, order_context, coupon_context,
                                       business_name, payment_context, session_id,
                                       confidence, sentiment, language, knowledge_context)

        # Step 12: Add upsell if applicable
        if entities.get("product") and intent in ("order_intent", "product_inquiry"):
            upsell = self.upsell.get_suggestion(
                entities["product"]["name"],
                entities["product"].get("price", 0) * entities.get("quantity", 1),
                inventory
            )
            if upsell:
                response += f"\n\n{upsell}"

        # Step 13: Record visit if customer_id exists
        if customer_id and entities.get("product"):
            self.profiler.record_visit(
                customer_id,
                product=entities["product"]["name"],
                amount=entities["product"].get("price", 0) * entities.get("quantity", 1),
            )

        return response

    def _route_intent(self, intent, message, name, entities, inventory,
                      order_context, coupon_context, business_name,
                      payment_context, session_id, confidence, sentiment,
                      language="hi", knowledge_context=None):
        """Route to appropriate handler based on intent."""
        mr = (language == "mr")

        # Low confidence → ask for clarification
        if confidence < 0.1 and intent == "unknown":
            return self.variator.vary("greeting", language=language, name=name, biz=business_name)

        # Greeting
        if intent == "greeting":
            return self.variator.vary("greeting", language=language, name=name, biz=business_name)

        # Price inquiry
        if intent == "price_inquiry":
            return self._handle_price(message, name, entities, inventory, language)

        # Product inquiry
        if intent == "product_inquiry":
            return self._handle_product(message, name, entities, inventory, language)

        # Order intent
        if intent == "order_intent":
            return self._handle_order(message, name, entities, inventory, language)

        # Delivery inquiry
        if intent == "delivery_inquiry":
            if mr:
                return f"{name}, डिलिव्हरी उपलब्ध आहे! 🚚\n📦 ₹50 अतिरिक्त शुल्क\n🏠 पत्ता सांगा तर पाठवू देतो.\n\nकिंवा स्टोअरवरून पिकअप FREE आहे!"
            return f"{name}, delivery available hai! 🚚\n📦 ₹50 extra charge\n🏠 Address batao toh bhej dete hain.\n\nYa store se pickup FREE hai!"

        # Pickup inquiry
        if intent == "pickup_inquiry":
            if mr:
                return f"{name}, स्टोअरवरून पिकअप FREE आहे! 🏪\n🕐 वेळ: 10 AM - 8 PM (Mon-Sat)\n💳 कॅश किंवा UPI दोन्ही चालतील."
            return f"{name}, store se pickup FREE hai! 🏪\n🕐 Timing: 10 AM - 8 PM (Mon-Sat)\n💳 Cash ya UPI dono chalenge."

        # Service booking
        if intent == "service_booking":
            return self._handle_booking(message, name, entities, inventory, language)

        # Complaint
        if intent == "complaint":
            return self._handle_complaint(message, name, entities, language)

        # Feedback
        if intent == "feedback":
            return self.variator.vary("feedback_thanks", language=language, name=name)

        # Discount inquiry
        if intent == "discount_inquiry":
            return self._handle_discount(message, name, coupon_context, language)

        # Payment inquiry
        if intent == "payment_inquiry":
            return self._handle_payment(message, name, payment_context, language)

        # Location inquiry
        if intent == "location_inquiry":
            if mr:
                return f"{name}, आमचे स्टोअर येथे आहे: 📍\nGoogle Maps वर शोधा किंवा पत्ता शेअर करा!"
            return f"{name}, hamara store yahan hai: 📍\nGoogle Maps pe search karo ya location share karo!"

        # Hours inquiry
        if intent == "hours_inquiry":
            if mr:
                return f"{name}, आमचे वेळापत्रक:\n🕐 सोम - शनि: 10 AM - 8 PM\n🕐 रविवार: बंद\n\nकाय हवे तुम्हाला?"
            return f"{name}, hamara timing:\n🕐 Monday - Saturday: 10 AM - 8 PM\n🕐 Sunday: Closed\n\nKya chahiye aapko?"

        # Fallback
        if knowledge_context:
            mr = (language == "mr")
            if mr:
                return (f"{name}, तुमच्या प्रश्नाचे उत्तर येथे आहे:\n\n"
                        f"{knowledge_context}\n\n"
                        f"आणखी काही मदत हवी आहे का?")
            return (f"{name}, aapke sawaal ka jawab yaha hai:\n\n"
                    f"{knowledge_context}\n\n"
                    f"Aur koi help chahiye?")

        return self.variator.vary("greeting", language=language, name=name, biz=business_name)

    def _handle_price(self, message, name, entities, inventory, language="hi"):
        """Handle price inquiry."""
        mr = (language == "mr")
        if entities.get("product"):
            p = entities["product"]
            if p.get("stock", 0) == 0:
                return self.variator.vary("out_of_stock", language=language, name=name, product=p["name"])
            return self.variator.vary("product_found", language=language, name=name, product=p["name"], price=p["price"])
        if mr:
            return f"{name}, कोणत्या प्रोडक्टची किंमत जाणून घ्यायची आहे? नाव सांगा! 💰"
        return f"{name}, kis product ka price jaanna hai? Naam batao! 💰"

    def _handle_product(self, message, name, entities, inventory, language="hi"):
        """Handle product inquiry."""
        mr = (language == "mr")
        if entities.get("product"):
            p = entities["product"]
            if p.get("stock", 0) == 0:
                return self.variator.vary("out_of_stock", language=language, name=name, product=p["name"])
            return self.variator.vary("product_found", language=language, name=name, product=p["name"], price=p["price"])
        if inventory:
            products = [f"- {p['name']} ₹{p['price']}" for p in inventory[:5]]
            if mr:
                return f"{name}, आमच्याकडे हे प्रोडक्ट्स आहेत:\n" + "\n".join(products) + "\n\nकाय हवे?"
            return f"{name}, hamare paas ye products hain:\n" + "\n".join(products) + "\n\nKya chahiye?"
        if mr:
            return f"{name}, काय प्रोडक्ट हवे? नाव सांगा!"
        return f"{name}, kya product chahiye? Naam batao!"

    def _handle_order(self, message, name, entities, inventory, language="hi"):
        """Handle order intent."""
        mr = (language == "mr")
        if entities.get("product"):
            p = entities["product"]
            if p.get("stock", 0) == 0:
                return self.variator.vary("out_of_stock", language=language, name=name, product=p["name"])
            qty = entities.get("quantity", 1)
            total = p["price"] * qty
            return self.variator.vary("ask_quantity", language=language, name=name, product=p["name"])
        if mr:
            return f"{name}, काय ऑर्डर करायचे? प्रोडक्टचे नाव सांगा! 🛒"
        return f"{name}, kya order karna hai? Product ka naam batao! 🛒"

    def _handle_booking(self, message, name, entities, inventory, language="hi"):
        """Handle service booking."""
        mr = (language == "mr")
        if entities.get("product"):
            svc = entities["product"]
            date_val = entities.get("date")
            time_val = entities.get("time")
            if date_val and time_val:
                return self.variator.vary("order_confirm", language=language, name=name, product=svc["name"],
                                          qty="1", total=svc["price"])
            if mr:
                return f"{name}, {svc['name']} बुक करायचे! 📅\nकोणत्या दिवशी आणि किती वाजता हवे?"
            return f"{name}, {svc['name']} book karna hai! 📅\nKis din aur kitne baje chahiye?"
        if mr:
            return f"{name}, काय सेवा बुक करायची? नाव सांगा! 📋"
        return f"{name}, kya service book karna hai? Naam batao! 📋"

    def _handle_complaint(self, message, name, entities, language="hi"):
        """Handle complaint with empathy."""
        mr = (language == "mr")
        product_info = ""
        if entities.get("product"):
            product_info = f"\n📦 प्रोडक्ट: {entities['product']['name']}" if mr else f"\n📦 Product: {entities['product']['name']}"
        if mr:
            return (f"😔 माफ करा {name}! तुमच्या तक्रारीने दुःख वाटले."
                    f"{product_info}\n\n"
                    f"📋 काय समस्या आहे तपशीवात सांगा — आम्ही लगेच सोडवणार.\n"
                    f"📞 किंवा थेट कॉल करा: +91-XXXXXXXXXX")
        return (f"😔 Maaf karo {name}! Aapki complaint sun ke dukh hua."
                f"{product_info}\n\n"
                f"📋 Kya problem hai detail mein batao — hum turant solve karenge.\n"
                f"📞 Ya direct call karo: +91-XXXXXXXXXX")

    def _handle_discount(self, message, name, coupon_context, language="hi"):
        """Handle discount inquiry."""
        mr = (language == "mr")
        if coupon_context:
            coupons = []
            for c in coupon_context[:3]:
                coupons.append(f"🏷️ {c['code']} - {c['discount_value']}{'%' if c['discount_type'] == 'percent' else '₹'} OFF")
            if mr:
                return f"{name}, हे ऑफर्स आहेत:\n" + "\n".join(coupons) + "\n\nऑर्डर करताना अप्लाई करा!"
            return f"{name}, ye offers hain:\n" + "\n".join(coupons) + "\n\nOrder karte waqt apply karo!"
        if mr:
            return f"{name}, आत्ता कोणताही स्पेशल ऑफर नाही. पण नियमित ग्राहकांना नक्की मिळतो! 🎁"
        return f"{name}, abhi koi special offer nahi hai. Lekin regular customers ko zaroor milta hai! 🎁"

    def _handle_payment(self, message, name, payment_context, language="hi"):
        """Handle payment inquiry."""
        mr = (language == "mr")
        if payment_context and payment_context.get("upi_id"):
            if mr:
                return f"{name}, पेमेंट पर्याय:\n💳 UPI: {payment_context['upi_id']}\n💵 कॅश ऑन डिलिव्हरी\n🏦 बँक ट्रान्सफर\n\nकशाने पे करायचे?"
            return f"{name}, payment options:\n💳 UPI: {payment_context['upi_id']}\n💵 Cash on Delivery\n🏦 Bank Transfer\n\nKaise pay karna hai?"
        if mr:
            return f"{name}, पेमेंट पर्याय:\n💳 UPI (GPay/PhonePe/PayTM)\n💵 कॅश\n\nकाय पसंत?"
        return f"{name}, payment options:\n💳 UPI (GPay/PhonePe/PayTM)\n💵 Cash\n\nKya pasand?"

    def _handle_angry(self, message, name, entities, inventory, language="hi"):
        """Handle angry customer with extra care."""
        mr = (language == "mr")
        product_info = ""
        if entities.get("product"):
            product_info = f"\n📦 प्रोडक्ट: {entities['product']['name']}" if mr else f"\n📦 Product: {entities['product']['name']}"
        if mr:
            return (f"😔 {name}, मला माहीत आहे तुम्ही चिंतित आहात. मी तुम्हाला मदत करीन!"
                    f"{product_info}\n\n"
                    f"📋 काय झाले तपशीवात सांगा — आम्ही सोडवणार.\n"
                    f"📞 तक्रार क्रमांक: +91-XXXXXXXXXX\n"
                    f"🙏 आम्ही तुमच्यासोबत आहोत!")
        return (f"😔 {name}, mujhe pata hai aap pareshan hain. Main aapki help karunga!"
                f"{product_info}\n\n"
                f"📋 Kya hua detail mein batao — hum solve karenge.\n"
                f"📞 Complaint number: +91-XXXXXXXXXX\n"
                f"🙏 Hum aapke saath hain!")

    def _handle_urgent(self, message, name, entities, inventory, language="hi"):
        """Handle urgent request with priority."""
        mr = (language == "mr")
        if entities.get("product"):
            p = entities["product"]
            if mr:
                return f"⚡ {name}, {p['name']} तुरंत हवे! 💰 ₹{p['price']}\n📦 स्टॉक आहे — आत्ता ऑर्डर करा!\n🕐 पिकअप: 30 मिनिटांत रेडी"
            return f"⚡ {name}, {p['name']} turant chahiye! 💰 ₹{p['price']}\n📦 Stock hai — abhi order karo!\n🕐 Pickup: 30 min mein ready"
        if mr:
            return f"⚡ {name}, लगेच सांगा काय हवे — मी तुरंत मदत करतो!"
        return f"⚡ {name}, jaldi batao kya chahiye — main turant help karta hoon!"


# ============================================================
# GLOBAL INSTANCE
# ============================================================

_falcon = None

def get_falcon() -> FalconEngine:
    """Get singleton Falcon Engine instance."""
    global _falcon
    if _falcon is None:
        _falcon = FalconEngine()
    return _falcon
