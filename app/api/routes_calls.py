from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import CallTranscript, CallInsight
from app.schemas import FullCallDetails, CoachingRecommendation, AgentAnalytics
from sentence_transformers import SentenceTransformer, util
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv
import torch
import os

router = APIRouter()

# Load environment variables and initialize models
load_dotenv()
sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
client = AsyncAzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
)
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")


@router.get("/api/v1/calls", response_model=List[FullCallDetails])
def get_calls(
    limit: int = 10,
    offset: int = 0,
    agent_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    min_sentiment: Optional[float] = None,
    max_sentiment: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(CallTranscript).join(CallInsight, CallTranscript.call_id == CallInsight.call_id)

    if agent_id:
        query = query.filter(CallTranscript.agent_id == agent_id)
    if from_date:
        query = query.filter(CallTranscript.start_time >= from_date)
    if to_date:
        query = query.filter(CallTranscript.start_time <= to_date)
    if min_sentiment:
        query = query.filter(CallInsight.customer_sentiment_score >= min_sentiment)
    if max_sentiment:
        query = query.filter(CallInsight.customer_sentiment_score <= max_sentiment)

    results = query.offset(offset).limit(limit).all()

    output = []
    for row in results:
        insights = db.query(CallInsight).filter_by(call_id=row.call_id).first()
        output.append(FullCallDetails(transcript=row, insights=insights))
    return output


@router.get("/api/v1/calls/{call_id}", response_model=FullCallDetails)
def get_call(call_id: str, db: Session = Depends(get_db)):
    transcript = db.query(CallTranscript).filter_by(call_id=call_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Call not found")

    insights = db.query(CallInsight).filter_by(call_id=call_id).first()
    return FullCallDetails(transcript=transcript, insights=insights)


@router.get("/api/v1/calls/{call_id}/recommendations", response_model=CoachingRecommendation)
async def get_recommendations(call_id: str, db: Session = Depends(get_db)):
    target = db.query(CallInsight).filter_by(call_id=call_id).first()
    if not target or not target.embedding:
        raise HTTPException(status_code=404, detail="Insights not found for this call")

    try:
        target_embedding = torch.tensor(eval(target.embedding))
        all_insights = db.query(CallInsight).filter(CallInsight.call_id != call_id).all()

        sims = []
        for insight in all_insights:
            if insight.embedding:
                emb = torch.tensor(eval(insight.embedding))
                score = util.cos_sim(target_embedding, emb).item()
                sims.append((insight.call_id, score))

        top_5 = sorted(sims, key=lambda x: x[1], reverse=True)[:5]
        similar_calls = [c[0] for c in top_5]

        prompt = (
            f"Based on this sales call insight:\n"
            f"- Agent talk ratio: {target.agent_talk_ratio:.2f}\n"
            f"- Customer sentiment score: {target.customer_sentiment_score:.2f}\n"
            f"Give 3 short and actionable coaching suggestions (each ≤ 40 words) for the sales agent to improve future calls. "
            f"Format each suggestion as a short bullet point.\n"
        )

        response = await client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a sales call coach."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.7,
        )

        raw_text = response.choices[0].message.content.strip()
        recs = [line.strip("•- ").strip() for line in raw_text.split("\n") if line.strip()]
        recommendations = recs[:3]

        return CoachingRecommendation(
            call_id=call_id,
            similar_calls=similar_calls,
            recommendations=recommendations,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/api/v1/analytics/agents", response_model=List[AgentAnalytics])
def get_agent_analytics(db: Session = Depends(get_db)):
    results = (
        db.query(
            CallTranscript.agent_id,
            func.avg(CallInsight.customer_sentiment_score).label("avg_sentiment"),
            func.avg(CallInsight.agent_talk_ratio).label("avg_talk_ratio"),
            func.count(CallTranscript.call_id).label("total_calls")
        )
        .join(CallInsight, CallTranscript.call_id == CallInsight.call_id)
        .group_by(CallTranscript.agent_id)
        .all()
    )

    return [
        AgentAnalytics(
            agent_id=r.agent_id,
            avg_sentiment=r.avg_sentiment,
            avg_talk_ratio=r.avg_talk_ratio,
            total_calls=r.total_calls,
        )
        for r in results
    ]
