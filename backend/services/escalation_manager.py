from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


class EscalationManager:
    def __init__(self, db: AsyncSession = None, whatsapp_client=None):
        self.db = db
        self.whatsapp_client = whatsapp_client
        self.escalations = {}

    async def check_escalation(self, customer_id: str, business_id: str, message: str, context: dict = None) -> dict:
        triggers = []
        message_lower = message.lower()

        human_triggers = ["insaan se baat", "human agent", "manager", "real person"]
        if any(t in message_lower for t in human_triggers):
            triggers.append("human_request")

        negative_triggers = ["gussa", "angry", "worst", "useless", "bakwas", "pathetic"]
        if any(t in message_lower for t in negative_triggers):
            triggers.append("negative_sentiment")

        frustrated = ["samajh nahi aaya", "dobara bolo", "samjho", "clear nahi"]
        if any(t in message_lower for t in frustrated):
            triggers.append("confusion")

        refund_triggers = ["refund", "paisa wapas", "money back", "cancel"]
        if any(t in message_lower for t in refund_triggers):
            triggers.append("refund_request")

        needs_escalation = len(triggers) > 0
        severity = "high" if len(triggers) >= 2 else "medium" if needs_escalation else "low"

        return {
            "needs_escalation": needs_escalation,
            "triggers": triggers,
            "severity": severity,
            "reason": ", ".join(triggers) if triggers else None,
        }

    async def escalate_to_agent(self, customer_id: str, business_id: str, reason: str) -> dict:
        escalation_id = f"ESC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.escalations[escalation_id] = {
            "id": escalation_id,
            "customer_id": customer_id,
            "business_id": business_id,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        }
        await self.notify_agent(business_id, customer_id, reason)
        return self.escalations[escalation_id]

    async def notify_agent(self, business_id: str, customer_id: str, message: str) -> None:
        pass

    async def get_pending_escalations(self, business_id: str) -> list:
        return [e for e in self.escalations.values() if e["business_id"] == business_id and e["status"] == "pending"]

    async def resolve_escalation(self, escalation_id: str, resolution: str) -> dict:
        if escalation_id in self.escalations:
            self.escalations[escalation_id]["status"] = "resolved"
            self.escalations[escalation_id]["resolution"] = resolution
            self.escalations[escalation_id]["resolved_at"] = datetime.utcnow().isoformat()
            return self.escalations[escalation_id]
        return {"error": "Escalation nahi mili"}

    async def get_escalation_stats(self, business_id: str) -> dict:
        business_esc = [e for e in self.escalations.values() if e["business_id"] == business_id]
        return {
            "total": len(business_esc),
            "pending": sum(1 for e in business_esc if e["status"] == "pending"),
            "resolved": sum(1 for e in business_esc if e["status"] == "resolved"),
        }

    async def auto_escalate_rules(self, business_id: str) -> list:
        return [
            {"rule": "human_request", "description": "Customer ne insaan se baat maangi", "severity": "high"},
            {"rule": "negative_sentiment", "description": "Customer ka sentiment negative hai", "severity": "medium"},
            {"rule": "confusion", "description": "Customer ko samajh nahi aa raha", "severity": "medium"},
            {"rule": "refund_request", "description": "Customer refund maang raha hai", "severity": "high"},
        ]

    async def update_escalation_rules(self, business_id: str, rules: list) -> dict:
        return {"business_id": business_id, "rules_updated": len(rules)}
