from skills.base import Skill


class SupportSkill(Skill):
    name = "support"
    description = "Troubleshoot, escalate, SLA tracking, FAQ"
    capabilities = ["troubleshoot", "escalate", "faq", "sla_tracking"]

    async def execute(self, context: dict) -> dict:
        issue = context.get("issue", "")
        customer_name = context.get("customer_name", "Customer")
        if issue:
            response = f"{customer_name} ji, aapki problem samajh aa rahi hai. 🤝 Main jald se jald solve karta hun. Agar zaroorat ho to team se connect karunga."
        else:
            response = f"{customer_name} ji, kya ho raha hai? 🙌 Apna issue detail mein bataiye, main madad karta hun."

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
