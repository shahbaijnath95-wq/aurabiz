from typing import Optional
from datetime import datetime, timedelta


class SentimentAnalyzer:
    def __init__(self, llm=None):
        self.llm = llm

    async def analyze(self, text: str) -> dict:
        if self.llm:
            try:
                return await self._analyze_with_llm(text)
            except Exception:
                pass
        return self._rule_based_analyze(text)

    async def analyze_batch(self, texts: list[str]) -> list[dict]:
        return [await self.analyze(text) for text in texts]

    async def get_sentiment_trend(self, customer_id: str, days: int = 30) -> dict:
        return {
            "customer_id": customer_id,
            "period_days": days,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "trend": "stable",
        }

    async def detect_escalation(self, text: str, conversation_history: list = None) -> bool:
        escalation_words = [
            "gussa", "angry", "frustrated", "insaan se baat", "human agent",
            "manager", "complaint", "worst", "useless", "bakwas", "pathetic",
            "disappointed", "disgusted", "furious", "irritated"
        ]
        text_lower = text.lower()
        if any(word in text_lower for word in escalation_words):
            return True
        if conversation_history:
            recent_negative = sum(
                1 for h in conversation_history[-3:]
                if h.get("sentiment") == "negative"
            )
            if recent_negative >= 2:
                return True
        return False

    def _rule_based_analyze(self, text: str) -> dict:
        text_lower = text.lower()

        positive_words = [
            "accha", "badhiya", "shukriya", "dhanyavaad", "great", "good", "nice",
            "happy", "excellent", "perfect", "wonderful", "amazing", "love",
            "best", "awesome", "fantastic", "thank", "thanks", "superb"
        ]
        negative_words = [
            "kharab", "bura", "pareshan", "angry", "bad", "problem", "gussa",
            "worst", "hate", "terrible", "horrible", "awful", "poor",
            "disappointed", "frustrated", "annoying", "useless"
        ]
        neutral_words = [
            "theek", "okay", "ok", "fine", "normal", "usual", "average"
        ]

        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        neu_count = sum(1 for w in neutral_words if w in text_lower)

        if pos_count > neg_count and pos_count > neu_count:
            sentiment = "positive"
            confidence = min(0.6 + (pos_count * 0.1), 0.95)
            emotions = ["happy"]
        elif neg_count > pos_count:
            sentiment = "negative"
            confidence = min(0.6 + (neg_count * 0.1), 0.95)
            emotions = ["frustrated"]
        else:
            sentiment = "neutral"
            confidence = 0.5
            emotions = []

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "emotions": emotions,
            "language_detected": "hi-en",
            "tone_suggestion": "empathetic" if sentiment == "negative" else "friendly",
        }

    async def _analyze_with_llm(self, text: str) -> dict:
        return self._rule_based_analyze(text)
