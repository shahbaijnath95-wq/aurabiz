from skills.base import Skill


class PricingSkill(Skill):
    name = "pricing"
    description = "Price quotes, bulk discounts, payment terms"
    capabilities = ["get_price", "bulk_discount", "payment_terms", "offers"]

    async def execute(self, context: dict) -> dict:
        product = context.get("product", "")
        if product:
            response = f"{product} ki price ₹999 hai. 💰 Bulk order par discount mil sakta hai! 10+ items par 10% off!"
        else:
            response = "Kis product ki price jaanni hai? 💰 Humare paas best deals hain! Bulk orders par special discount milta hai."

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
