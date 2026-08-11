from skills.base import Skill


class FollowupSkill(Skill):
    name = "followup"
    description = "Smart reminders, re-engagement, abandoned cart"
    capabilities = ["send_reminder", "re_engage", "cart_recovery", "check_in"]

    async def execute(self, context: dict) -> dict:
        customer_name = context.get("customer_name", "Customer")
        days = context.get("days_since_order", 0)
        if days > 7:
            response = f"{customer_name} ji! 🎁 Bahut din ho gaye! Special discount mil raha hai - 15% off. Abhi order karein!"
        elif days > 3:
            response = f"{customer_name} ji, aapka order kaisa laga? 🙏 Koi feedback ho to batayein!"
        else:
            response = f"{customer_name} ji! Sirf aapke liye special offer hai. Check karein! 🎉"

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
