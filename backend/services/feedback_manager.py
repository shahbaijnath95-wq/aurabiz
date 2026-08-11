from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


class FeedbackManager:
    def __init__(self, db: AsyncSession = None, whatsapp_client=None):
        self.db = db
        self.whatsapp = whatsapp_client
        self.surveys = {}
        self.reviews = {}

    async def send_nps_survey(self, business_id: str, customer_id: str) -> bool:
        return True

    async def get_nps_results(self, business_id: str, period: str = "30d") -> dict:
        return {
            "business_id": business_id,
            "period": period,
            "nps_score": 0,
            "promoters": 0,
            "passives": 0,
            "detractors": 0,
            "total_responses": 0,
        }

    async def monitor_reviews(self, business_id: str) -> list:
        return self.reviews.get(business_id, [])

    async def respond_to_review(self, review_id: str, response: str) -> dict:
        return {"review_id": review_id, "response": response, "status": "posted"}

    async def create_survey(self, business_id: str, questions: list) -> dict:
        import uuid
        survey_id = str(uuid.uuid4())
        self.surveys[survey_id] = {
            "id": survey_id,
            "business_id": business_id,
            "questions": questions,
            "responses": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        return self.surveys[survey_id]

    async def get_survey_results(self, survey_id: str) -> dict:
        survey = self.surveys.get(survey_id)
        if not survey:
            return {"error": "Survey nahi mili"}
        return {
            "survey_id": survey_id,
            "total_responses": len(survey["responses"]),
            "questions": survey["questions"],
            "results": survey["responses"],
        }

    async def analyze_feedback_sentiment(self, feedback_list: list) -> dict:
        positive = sum(1 for f in feedback_list if f.get("sentiment") == "positive")
        negative = sum(1 for f in feedback_list if f.get("sentiment") == "negative")
        neutral = len(feedback_list) - positive - negative
        return {
            "total": len(feedback_list),
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
        }

    async def send_feedback_request(self, customer_id: str, template: str = None) -> bool:
        return True
