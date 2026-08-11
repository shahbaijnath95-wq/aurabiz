from skills.base import Skill


class BillingSkill(Skill):
    name = "billing"
    description = "Generate bill, send bill, track payment"
    capabilities = ["generate_bill", "send_bill", "track_payment", "invoice"]

    async def execute(self, context: dict) -> dict:
        customer_name = context.get("customer_name", "Customer")
        amount = context.get("amount", 0)
        if amount:
            response = f"{customer_name} ji, aapka bill ₹{amount} hai. ✅ Payment link bhejun kya? UPI se aasani se pay kar sakte hain!"
        else:
            response = f"{customer_name} ji, bill generate karne ke liye items aur amount bataiye. 📄"

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
