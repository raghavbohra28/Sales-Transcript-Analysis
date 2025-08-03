from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import CallTranscript, CallInsight
from app.schemas import AgentAnalytics

router = APIRouter()

@router.get("/api/v1/analytics/agents", response_model=List[AgentAnalytics])
def get_agent_analytics(db: Session = Depends(get_db)):
    result = (
        db.query(
            CallTranscript.agent_id,
            func.avg(CallInsight.customer_sentiment_score).label("avg_sentiment"),
            func.avg(CallInsight.agent_talk_ratio).label("avg_talk_ratio"),
            func.count(CallTranscript.call_id).label("total_calls"),
        )
        .join(CallInsight, CallTranscript.call_id == CallInsight.call_id)
        .group_by(CallTranscript.agent_id)
        .all()
    )

    return [
        AgentAnalytics(
            agent_id=row.agent_id,
            avg_sentiment=row.avg_sentiment,
            avg_talk_ratio=row.avg_talk_ratio,
            total_calls=row.total_calls,
        )
        for row in result
    ]
