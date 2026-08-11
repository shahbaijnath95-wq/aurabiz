"""
Falcon Trainer — Self-Learning Module
=======================================
Jab API use hota hai (Cloudflare/Groq/Gemini), uska reply save hota hai.
Falcon time ke saath seekhta hai — API ki zaroorat kam hoti jaati hai.

Flow:
1. Customer → API se reply aaya
2. Reply + query + intent + entities save karo
3. Next time similar query aaye → Falcon saved reply use kare
4. Agar customer ne feedback diya (accha/bura) → weight update karo

Storage: falcon_training.json (local file, no DB needed)
"""

import json
import os
import hashlib
import tempfile
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
import threading

TRAINING_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "falcon_training.json")
MAX_TRAINING_ENTRIES = 5000  # Max saved responses

# File lock to prevent concurrent writes corrupting the JSON
_file_lock = threading.Lock()


class FalconTrainer:
    """Self-learning module — trains Falcon from API responses."""

    def __init__(self):
        self._data: Dict[str, Any] = {
            "responses": [],  # List of training entries
            "patterns": {},   # intent → [response_templates]
            "product_responses": {},  # product_name → [responses]
            "feedback": {},   # query_hash → {"positive": 0, "negative": 0}
            "stats": {
                "total_learned": 0,
                "total_used": 0,
                "accuracy": 0.0,
            }
        }
        self._load()

    def _load(self):
        """Load training data from file."""
        try:
            if os.path.exists(TRAINING_FILE):
                with open(TRAINING_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._data.update(loaded)
        except Exception:
            pass  # Start fresh if file corrupted

    def _save(self):
        """Save training data to file — atomic write with locking."""
        with _file_lock:
            try:
                os.makedirs(os.path.dirname(TRAINING_FILE), exist_ok=True)
                # Atomic write: write to temp file then rename
                dir_path = os.path.dirname(TRAINING_FILE) or "."
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=dir_path,
                    delete=False, suffix=".tmp"
                ) as tmp:
                    json.dump(self._data, tmp, ensure_ascii=False, indent=2)
                    tmp_path = tmp.name
                os.replace(tmp_path, TRAINING_FILE)
            except Exception:
                pass

    def _hash_query(self, query: str, intent: str = "", language: str = "hi") -> str:
        """Create hash for query deduplication."""
        normalized = query.lower().strip()
        return hashlib.md5(f"{normalized}:{intent}:{language}".encode()).hexdigest()[:12]

    def learn(
        self,
        query: str,
        response: str,
        intent: str = "unknown",
        entities: Dict = None,
        product_name: str = None,
        customer_name: str = "Customer",
        business_name: str = "Business",
        confidence: float = 0.0,
        language: str = "hi",
    ):
        """
        Learn from an API response.
        Called every time API generates a reply.
        """
        if not response or len(response) < 10:
            return  # Skip very short responses

        query_hash = self._hash_query(query, intent, language)

        # Check if already learned this exact query
        for entry in self._data["responses"]:
            if entry.get("query_hash") == query_hash:
                # Update response if new one is better (longer, more detailed)
                if len(response) > len(entry.get("response", "")):
                    entry["response"] = response
                    entry["updated_at"] = datetime.now().isoformat()
                    entry["use_count"] = entry.get("use_count", 0)
                self._save()
                return

        # Create training entry
        entry = {
            "query": query.lower().strip(),
            "query_hash": query_hash,
            "response": response,
            "intent": intent,
            "entities": entities or {},
            "product_name": product_name,
            "customer_name": customer_name,
            "business_name": business_name,
            "confidence": confidence,
            "learned_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "use_count": 0,
            "success_count": 0,
            "fail_count": 0,
            "weight": 1.0,
            "language": language,
        }

        self._data["responses"].append(entry)

        # Update patterns index
        if intent not in self._data["patterns"]:
            self._data["patterns"][intent] = []
        self._data["patterns"][intent].append(query_hash)

        # Update product index
        if product_name:
            if product_name not in self._data["product_responses"]:
                self._data["product_responses"][product_name] = []
            self._data["product_responses"][product_name].append(query_hash)

        self._data["stats"]["total_learned"] += 1

        # Trim if too many entries
        if len(self._data["responses"]) > MAX_TRAINING_ENTRIES:
            # Keep newest and highest-weight entries
            self._data["responses"].sort(
                key=lambda x: (x.get("weight", 1.0), x.get("use_count", 0)),
                reverse=True
            )
            self._data["responses"] = self._data["responses"][:MAX_TRAINING_ENTRIES]

        self._save()

    def find_response(
        self,
        query: str,
        intent: str = None,
        product_name: str = None,
        threshold: float = 0.70,
        language: str = "hi",
    ) -> Optional[str]:
        """
        Find a learned response for a similar query.
        Returns None if no good match found.
        """
        query_lower = query.lower().strip()
        best_match = None
        best_score = 0.0

        for entry in self._data["responses"]:
            score = 0.0

            # Exact hash match
            if entry.get("query_hash") == self._hash_query(query_lower, intent or "", language):
                score = 1.0
            else:
                # Fuzzy match on query text
                stored_query = entry.get("query", "")
                text_ratio = SequenceMatcher(None, query_lower, stored_query).ratio()

                # Intent match bonus
                if intent and entry.get("intent") == intent:
                    text_ratio += 0.15

                # Product match bonus
                if product_name and entry.get("product_name") == product_name:
                    text_ratio += 0.1

                # Language match required
                if entry.get("language") != language:
                    text_ratio = 0.0

                score = text_ratio

            # Apply weight (from feedback)
            score *= entry.get("weight", 1.0)

            if score > best_score and score >= threshold:
                best_score = score
                best_match = entry

        if best_match:
            # Update usage stats
            best_match["use_count"] = best_match.get("use_count", 0) + 1
            self._data["stats"]["total_used"] += 1
            self._save()

            # Personalize response
            response = best_match["response"]
            response = response.replace("{name}", best_match.get("customer_name", "Customer"))
            return response

        return None

    def feedback(self, query: str, intent: str = "", positive: bool = True):
        """
        Record feedback for a learned response.
        positive=True → response was good
        positive=False → response was bad
        """
        query_hash = self._hash_query(query, intent)

        # Update feedback counters
        if query_hash not in self._data["feedback"]:
            self._data["feedback"][query_hash] = {"positive": 0, "negative": 0}

        if positive:
            self._data["feedback"][query_hash]["positive"] += 1
        else:
            self._data["feedback"][query_hash]["negative"] += 1

        # Update weight on the response entry
        for entry in self._data["responses"]:
            if entry.get("query_hash") == query_hash:
                fb = self._data["feedback"][query_hash]
                total = fb["positive"] + fb["negative"]
                if total > 0:
                    # Weight: 0.3 to 2.0 based on positive ratio
                    positive_ratio = fb["positive"] / total
                    entry["weight"] = 0.3 + (positive_ratio * 1.7)
                    if positive:
                        entry["success_count"] = entry.get("success_count", 0) + 1
                    else:
                        entry["fail_count"] = entry.get("fail_count", 0) + 1
                break

        # Update accuracy stat
        total_fb = sum(
            fb["positive"] + fb["negative"]
            for fb in self._data["feedback"].values()
        )
        total_positive = sum(
            fb["positive"]
            for fb in self._data["feedback"].values()
        )
        if total_fb > 0:
            self._data["stats"]["accuracy"] = round(total_positive / total_fb * 100, 1)

        self._save()

    def get_stats(self) -> Dict:
        """Get training statistics."""
        return {
            "total_learned": self._data["stats"].get("total_learned", 0),
            "total_used": self._data["stats"].get("total_used", 0),
            "accuracy": self._data["stats"].get("accuracy", 0.0),
            "total_entries": len(self._data["responses"]),
            "intents_covered": list(self._data["patterns"].keys()),
            "products_covered": list(self._data["product_responses"].keys()),
        }

    def get_product_responses(self, product_name: str) -> List[str]:
        """Get all learned responses for a specific product."""
        hashes = self._data["product_responses"].get(product_name, [])
        responses = []
        for entry in self._data["responses"]:
            if entry.get("query_hash") in hashes:
                responses.append(entry["response"])
        return responses

    def clear_old_entries(self, days: int = 30):
        """Clear entries older than X days with low usage."""
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        self._data["responses"] = [
            e for e in self._data["responses"]
            if e.get("learned_at", "") > cutoff or e.get("use_count", 0) > 5
        ]
        self._save()


# ============================================================
# GLOBAL INSTANCE
# ============================================================

_trainer = None

def get_trainer() -> FalconTrainer:
    """Get singleton Falcon Trainer instance."""
    global _trainer
    if _trainer is None:
        _trainer = FalconTrainer()
    return _trainer
