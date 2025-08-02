from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, func
from sqlalchemy.dialects.postgresql import TSVECTOR

Base = declarative_base()

class CallTranscript(Base):
    __tablename__ = "call_transcripts"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, unique=True, index=True)
    agent_id = Column(String, index=True)
    customer_id = Column(String)
    language = Column(String)
    start_time = Column(DateTime, index=True)
    duration_seconds = Column(Integer)
    transcript = Column(Text)

    transcript_tsv = Column(TSVECTOR)
    __table_args__ = (
        # Index on tsvector column using GIN
        Index('ix_transcripts_transcript_tsv', 'transcript_tsv', postgresql_using='gin'),
    )
