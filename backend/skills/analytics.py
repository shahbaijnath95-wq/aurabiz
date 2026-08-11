from skills.base import Skill


class AnalyticsSkill(Skill):
    name = "analytics"
    description = "Sales insights, trends, customer behavior"
    capabilities = ["sales_insights", "trends", "customer_behavior", "revenue_report"]

    async def execute(self, context: dict) -> dict:
        report_type = context.get("report_type", "summary")
        business_name = context.get("business_name", "Business")

        if report_type == "summary":
            response = f"{business_name} ka aaj ka summary: 📊 Revenue ₹0 hai. Abhi transactions record karein, dashboard mein saara data dikh jayega!"
        else:
            response = f"Analytics report ready hai! 📊 Dashboard mein jaake detailed data dekh sakte hain."

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
