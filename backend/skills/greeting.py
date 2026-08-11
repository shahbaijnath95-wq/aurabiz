from skills.base import Skill


class GreetingSkill(Skill):
    name = "greeting"
    description = "Customer ka swagat karta hai - returning customer ko pehchanta hai"
    capabilities = ["welcome", "returning_customer", "time_based_greeting"]

    async def execute(self, context: dict) -> dict:
        business_name = context.get("business_name", "Humara Business")
        customer_name = context.get("customer_name", "Customer")
        is_returning = context.get("is_returning_customer", False)

        if is_returning:
            response = f"Wapas aane ka shukriya {customer_name} ji! 🙏 Kya help kar sakta hun aaj?"
        else:
            response = f"Namaste {customer_name} ji! 🙏 {business_name} mein aapka swagat hai! Hum kaise help kar sakte hain?"

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
