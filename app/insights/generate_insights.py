import os
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import CallTranscript, CallInsight
from transformers import pipeline
from sentence_transformers import SentenceTransformer

sentiment_model = pipeline("sentiment-analysis")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def is_filler(token):
    fillers = {"um", "uh", "like", "you know", "i mean", "so", "actually"}
    return token.lower() in fillers

def calculate_agent_talk_ratio(transcript):
    agent_words = 0
    total_words = 0

    for line in transcript.split("\n"):
        if not line.strip():
            continue
        if line.startswith("Agent:"):
            words = [w for w in line[6:].split() if not is_filler(w)]
            agent_words += len(words)
        elif line.startswith("Customer:"):
            words = [w for w in line[9:].split() if not is_filler(w)]
            total_words += len(words)
        else:
            continue

    total_words += agent_words
    return round(agent_words / total_words, 4) if total_words > 0 else 0.0

def analyze_sentiment(transcript):
    customer_lines = "\n".join([line[9:] for line in transcript.split("\n") if line.startswith("Customer:")])
    result = sentiment_model(customer_lines[:512])[0]  
    label = result["label"]
    score = result["score"]

    if label == "POSITIVE":
        return round(score, 4)
    elif label == "NEGATIVE":
        return round(-score, 4)
    else:
        return 0.0

def compute_and_store_insights():
    db: Session = SessionLocal()
    try:
        transcripts = db.query(CallTranscript).all()

        for call in transcripts:
            if db.query(CallInsight).filter_by(call_id=call.call_id).first():
                continue 

            ratio = calculate_agent_talk_ratio(call.transcript)
            sentiment = analyze_sentiment(call.transcript)
            embedding = embedding_model.encode(call.transcript).tolist()

            insight = CallInsight(
                call_id=call.call_id,
                agent_talk_ratio=ratio,
                customer_sentiment_score=sentiment,
                embedding=str(embedding)  
            )
            db.add(insight)
            db.commit()

    finally:
        db.close()
