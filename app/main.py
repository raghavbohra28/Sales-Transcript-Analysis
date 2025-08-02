from app.database import engine
from app.models import Base, CallTranscript
from sqlalchemy.sql import text
from fastapi import FastAPI
import asyncio
from app.ingest.llm_transcript_ingestion import main  # Import the main async function

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Sales Analytics API"}

@app.post("/ingest-transcripts")
async def ingest_transcripts():
    await main()  # Call the ingestion process
    return {"status": "success", "message": "Transcript ingestion completed."}

def create_tables():
    # Create all tables (safe: won't overwrite existing ones)
    Base.metadata.create_all(bind=engine)

def setup_tsvector_trigger():
    # Setup full-text search trigger for transcript_tsv column
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
