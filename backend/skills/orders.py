from skills.base import Skill


class OrdersSkill(Skill):
    name = "orders"
    description = "Order status, delivery tracking, ETA"
    capabilities = ["check_status", "track_delivery", "get_eta", "report_issue"]

    async def execute(self, context: dict) -> dict:
        order_id = context.get("order_id", "")
        if order_id:
            response = f"Order {order_id} ka status: Processing mein hai. 📦 2-3 din mein deliver ho jayega!"
        else:
            response = "Kya aapka order track karna hai? 📦 Order number bataiye, main status bata deta hun."

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
