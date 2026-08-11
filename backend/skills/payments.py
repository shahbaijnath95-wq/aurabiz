from skills.base import Skill


class PaymentsSkill(Skill):
    name = "payments"
    description = "Collect, confirm, remind payments - UPI link bhejta hai"
    capabilities = ["collect_payment", "confirm_payment", "send_reminder", "upi_link"]

    async def execute(self, context: dict) -> dict:
        amount = context.get("amount", 0)
        customer_name = context.get("customer_name", "Customer")
        if amount:
            response = f"{customer_name} ji, ₹{amount} ka payment pending hai. 💳 UPI se pay karein: upi://pay?amount={amount}"
        else:
            response = f"{customer_name} ji, payment ka amount bataiye. Main UPI link bhej deta hun! 💰"

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
