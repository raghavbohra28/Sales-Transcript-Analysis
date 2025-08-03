from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class CallInsightSchema(BaseModel):
    agent_talk_ratio: float
    customer_sentiment_score: float

    model_config = ConfigDict(from_attributes=True)


class CallTranscriptSchema(BaseModel):
    call_id: str
    agent_id: str
    customer_id: str
    language: str
    start_time: datetime
    duration_seconds: int
    transcript: str

    model_config = ConfigDict(from_attributes=True)


class FullCallDetails(BaseModel):
    transcript: CallTranscriptSchema
    insights: Optional[CallInsightSchema]

    model_config = ConfigDict(from_attributes=True)


class CoachingRecommendation(BaseModel):
    call_id: str
    recommendations: List[str]
    similar_calls: List[str]


class AgentAnalytics(BaseModel):
    agent_id: str
    avg_sentiment: float
    avg_talk_ratio: float
    total_calls: int
