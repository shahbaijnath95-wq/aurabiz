from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from database import get_db, redis_client
from auth import get_current_user, verify_business_access
from models import User, Business
from schemas import DashboardResponse, SuccessResponse
from services.analytics_engine import AnalyticsEngine
from services.revenue_forecaster import RevenueForecaster
from services.conversation_analytics import ConversationAnalytics
from services.language_service import detect_language
import json

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


def get_analytics_engine(db):
    return AnalyticsEngine(db, redis_client)


@router.get("/dashboard/{business_id}")
async def get_dashboard(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        engine = get_analytics_engine(db)
        dashboard = await engine.get_dashboard(business_id)
        return dashboard
    except Exception as e:
        return {
            "stat_cards": {
                "revenue": {"value": 0, "change": 0, "trend": "up"},
                "orders": {"value": 0, "change": 0, "trend": "up"},
                "customers": {"value": 0, "change": 0, "trend": "up"},
                "avg_order": {"value": 0, "change": 0, "trend": "up"},
                "messages": {"value": 0, "change": 0, "trend": "up"},
            },
            "revenue_chart": [],
            "customer_metrics": {"total": 0, "new_this_month": 0, "active": 0, "churned": 0},
            "top_products": [],
            "revenue_forecast": [],
            "customer_segments": {"high_value": 0, "medium_value": 0, "low_value": 0},
            "recent_transactions": [],
            "activity_feed": [],
            "ai_insights": ["Dashboard setup ho gaya hai!", f"Error: {str(e)}"],
        }


@router.get("/revenue/{business_id}")
async def get_revenue(
    business_id: str,
    period: str = Query("daily"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    engine = get_analytics_engine(db)
    return await engine.get_revenue_analytics(business_id, period)


@router.get("/transactions/{business_id}")
async def get_transaction_analytics(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    engine = get_analytics_engine(db)
    return await engine.get_transaction_analytics(business_id)


@router.get("/customers/{business_id}")
async def get_customer_analytics(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    engine = get_analytics_engine(db)
    return await engine.get_customer_analytics(business_id)


@router.get("/revenue/forecast/{business_id}")
async def get_forecast(
    business_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    forecaster = RevenueForecaster(db)
    return await forecaster.forecast_revenue(business_id, days)


@router.get("/revenue/patterns/{business_id}")
async def get_patterns(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    forecaster = RevenueForecaster(db)
    return await forecaster.analyze_patterns(business_id)


@router.get("/revenue/alerts/{business_id}")
async def get_alerts(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    forecaster = RevenueForecaster(db)
    return await forecaster.generate_alerts(business_id)


@router.get("/revenue/what-if/{business_id}")
async def what_if(
    business_id: str,
    price_change: float = Query(0),
    volume_change: float = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    forecaster = RevenueForecaster(db)
    return await forecaster.run_what_if(business_id, [{"price_change": price_change, "volume_change": volume_change}])


@router.get("/insights/{business_id}")
async def get_insights(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    engine = get_analytics_engine(db)
    return {"insights": await engine.generate_insights(business_id)}


@router.get("/activity/{business_id}")
async def get_activity(
    business_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    engine = get_analytics_engine(db)
    return {"activity": await engine.get_activity_feed(business_id, limit)}


@router.post("/refresh/{business_id}")
async def refresh(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    engine = get_analytics_engine(db)
    return await engine.refresh_analytics(business_id)


# ── Conversation Analytics ──


@router.get("/conversations/{business_id}")
async def get_conversation_stats(
    business_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    """Get comprehensive conversation analytics."""
    try:
        analytics = ConversationAnalytics(db)
        stats = await analytics.get_conversation_stats(business_id, days)
        return stats
    except Exception as e:
        logger.error("Conversation stats error: {}", e)
        return {
            "total_messages": 0, "inbound_messages": 0, "outbound_messages": 0,
            "unique_customers": 0, "active_conversations": 0,
            "sentiment_distribution": {}, "intent_distribution": {},
            "hourly_trend": [], "daily_trend": [],
        }


@router.get("/conversations/{business_id}/sentiment")
async def get_sentiment_analysis(
    business_id: str,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    """Get sentiment analysis for conversations."""
    try:
        analytics = ConversationAnalytics(db)
        sentiment = await analytics.get_sentiment_summary(business_id, days)
        return sentiment
    except Exception as e:
        logger.error("Sentiment analysis error: {}", e)
        return {"sentiment_distribution": {}, "total_analyzed": 0}


@router.get("/conversations/{business_id}/engagement")
async def get_engagement_metrics(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    """Get customer engagement metrics."""
    try:
        analytics = ConversationAnalytics(db)
        engagement = await analytics.get_customer_engagement(business_id, days=7)
        return engagement
    except Exception as e:
        logger.error("Engagement metrics error: {}", e)
        return {"top_customers": [], "response_time_avg": 0, "peak_hours": []}


@router.get("/conversations/{business_id}/intents")
async def get_intent_distribution(
    business_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    """Get intent distribution from conversations."""
    try:
        analytics = ConversationAnalytics(db)
        intents = await analytics.get_intent_distribution(business_id, days)
        return intents
    except Exception as e:
        logger.error("Intent distribution error: {}", e)
        return {"intents": {}, "total_analyzed": 0}


@router.post("/language/detect")
async def detect_message_language(
    text: str,
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    """Detect the language of a text message."""
    lang = detect_language(text)
    lang_names = {
        "hi": "Hindi", "en": "English", "mr": "Marathi", "gu": "Gujarati",
        "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
    }
    return {
        "detected_language": lang,
        "language_name": lang_names.get(lang, "Unknown"),
        "confidence": 0.85 if lang != "hi" else 0.9,
    }





