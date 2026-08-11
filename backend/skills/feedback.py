from skills.base import Skill


class FeedbackSkill(Skill):
    name = "feedback"
    description = "Request feedback, NPS survey, reviews - sentiment-aware"
    capabilities = ["request_feedback", "nps_survey", "collect_review", "analyze"]

    async def execute(self, context: dict) -> dict:
        customer_name = context.get("customer_name", "Customer")
        sentiment = context.get("sentiment", "neutral")
        if sentiment == "negative":
            response = f"{customer_name} ji, humein khushi hui aap batane ka mauka de rahe hain. 🙏 Kya hua? Detail mein bataiye taaki hum improve kar sakein."
        elif sentiment == "positive":
            response = f"{customer_name} ji, bahut accha laga sun ke! ⭐ Kya aap 5 star review de sakte hain? Aapka feedback bahut matter karta hai!"
        else:
            response = f"{customer_name} ji, aapka experience kaisa raha? ⭐ 1-10 mein kitne stars denge? Feedback se hum aur accha kar paayenge."

        return {"response": response, "skill": self.name}

    def format_response(self, result: str) -> str:
        return result
