from app.database import engine
from app.models import Base, CallTranscript
from sqlalchemy.sql import text
from fastapi import FastAPI
import asyncio
from app.ingest.llm_transcript_ingestion import main 
from app.api import routes_calls, routes_analytics

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Sales Analytics API"}

@app.post("/ingest-transcripts")
async def ingest_transcripts():
    await main()
    return {"status": "success", "message": "Transcript ingestion completed."}

from app.insights.generate_insights import compute_and_store_insights

@app.post("/compute-insights")
async def compute_insights():
    compute_and_store_insights()
    return {"status": "success", "message": "Call insights generated."}

app.include_router(routes_calls.router)
app.include_router(routes_analytics.router)


def create_tables():
    Base.metadata.create_all(bind=engine)

def setup_tsvector_trigger():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION transcripts_tsvector_trigger() RETURNS trigger AS $$
            begin
              new.transcript_tsv :=
                 to_tsvector('english', coalesce(new.transcript,''));
              return new;
            end
            $$ LANGUAGE plpgsql;
        """))

        conn.execute(text("""
            DROP TRIGGER IF EXISTS tsvectorupdate ON call_transcripts;
        """))

        conn.execute(text("""
            CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
            ON call_transcripts FOR EACH ROW EXECUTE FUNCTION transcripts_tsvector_trigger();
        """))

if __name__ == "__main__":
    create_tables()
    setup_tsvector_trigger()
    print("Database initialized and full-text search trigger set up.")
