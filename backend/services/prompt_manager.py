from typing import Optional
from datetime import datetime
import json
import random


class PromptManager:
    def __init__(self):
        self.prompts = self._load_prompts()
        self.custom_prompts = {}

    def _load_prompts(self) -> dict:
        return {
            "system": """Tu ek helpful AI assistant hai jo Indian small businesses ki madad karta hai.
Teri bhasha Hinglish hai - Hindi words English script mein.
Tera tone friendly, professional aur helpful hai.
Hamesha customer ki madad ko priority de.
Agar kuch samajh nahi aaya to politely pooch.""",

            "greeting": """Tu {business_name} ka AI assistant hai.
Customer ka swagat kar - agar returning customer hai to pehchan ke bolo.
Hinglish mein baat kar. Short aur sweet rakh greeting.""",

            "catalog": """Customer ko product ya service ke baare mein madad kar.
Available products bata, alternatives suggest kar, stock bata.
Hinglish mein jawab de. Price aur availability clearly mention kar.""",

            "pricing": """Customer ko pricing information de.
Bulk discounts, payment terms, offers explain kar.
Hinglish mein jawab de. Price clearly ₹ mein bata.""",

            "billing": """Customer ko bill generate kar ya payment info de.
Invoice bhejne ka option de.
Hinglish mein jawab de.""",

            "orders": """Customer ke order ka status bata.
Delivery tracking, ETA, issues resolve kar.
Hinglish mein jawab de.""",

            "payments": """Payment collection, confirmation ya reminder bhej.
UPI link bhejne ka option de.
Hinglish mein jawab de.""",

            "feedback": """Customer se feedback maang.
NPS survey bhej, review maang.
Sentiment ke hisaab se tone adjust kar.
Hinglish mein jawab de.""",

            "support": """Customer ki problem solve kar.
Troubleshoot kar, FAQ bata, zaroorat ho to escalate kar.
Hinglish mein jawab de.""",

            "followup": """Smart reminders bhej, re-engagement karo.
Abandoned cart follow-up, special offers de.
Hinglish mein jawab de.""",

            "appointments": """Appointment book, confirm, remind, reschedule kar.
Calendar check kar.
Hinglish mein jawab de.""",

            "analytics": """Business analytics aur insights share kar.
Sales trends, customer behavior, revenue data bata.
Hinglish mein jawab de.""",

            "sentiment_analysis": """Is message ka sentiment analyze kar.
Return JSON: {"sentiment": "positive/negative/neutral", "confidence": 0.0-1.0, "emotions": ["happy","angry",...], "language_detected": "hi/en/hi-en"}""",

            "intent_detection": """Is message ka intent detect kar.
Possible intents: greeting, catalog_query, pricing_query, order_status, payment, feedback, complaint, appointment, support, follow_up, unknown
Return JSON: {"intent": "...", "confidence": 0.0-1.0, "parameters": {}}""",

            "fallback": """Agar tu kisi question ka jawab nahi de sakta, to politely bolo:
"Mujhe iske baare mein confirmed jawab nahi pata. Kya main aapko [business owner] se connect kar sakta hun?"
Hinglish mein baat kar.""",
        }

    def get_skill_prompt(self, skill_name: str, context: dict = None) -> str:
        if skill_name in self.custom_prompts:
            prompt = self.custom_prompts[skill_name]
        else:
            prompt = self.prompts.get(skill_name, self.prompts["fallback"])

        if context:
            for key, value in context.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))
        return prompt

    def get_fallback_prompt(self, context: dict = None) -> str:
        return self.get_skill_prompt("fallback", context)

    def get_sentiment_prompt(self, text: str) -> str:
        return f"{self.prompts['sentiment_analysis']}\n\nMessage: {text}"

    def get_intent_prompt(self, text: str) -> str:
        return f"{self.prompts['intent_detection']}\n\nMessage: {text}"

    def get_pricing_prompt(self, context: dict) -> str:
        return self.get_skill_prompt("pricing", context)

    def get_payment_reminder_prompt(self, context: dict) -> str:
        return self.get_skill_prompt("payments", context)

    def get_feedback_request_prompt(self, context: dict) -> str:
        return self.get_skill_prompt("feedback", context)

    def format_response_prompt(self, response: str) -> str:
        return f"Is response ko Hinglish mein format kar, professional banao:\n\n{response}"

    def update_prompt(self, skill: str, new_prompt: str) -> None:
        self.custom_prompts[skill] = new_prompt

    def get_all_skills(self) -> list[str]:
        return [k for k in self.prompts.keys() if k not in ("system", "sentiment_analysis", "intent_detection", "fallback")]
