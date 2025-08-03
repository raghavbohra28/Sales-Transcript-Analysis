
# 📞 Sales Call Analytics Microservice

A FastAPI-based microservice that simulates, ingests, analyzes, and serves insights from customer-agent sales calls. It uses Azure OpenAI to generate call transcripts, computes AI-driven insights (sentiment and talk ratio), and provides structured APIs for analytics and coaching.

---

## 🚀 Features

- Generate synthetic sales-call transcripts using Azure OpenAI
- Extract and store structured call metadata
- Compute agent-customer sentiment and talk ratio
- Generate coaching recommendations
- Serve analytics and call data via REST API

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL
- **AI**: Azure OpenAI GPT, Hugging Face Transformers, Sentence Transformers
- **Deployment**: Docker, Uvicorn
- **Search**: PostgreSQL Full-Text Search with GIN Index

---

## ⚙️ Setup Instructions

1. **Clone the repository**:
```bash
git clone https://github.com/your-username/sales-call-analytics.git
cd sales-call-analytics
```

2. **Create and activate virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run migrations**:
```bash
alembic upgrade head
```

5. **Start the FastAPI server**:
```bash
uvicorn main:app --reload
```

---

## 📌 API Usage Guide

### 🧪 Testing the Workflow

1. **Ingest Synthetic Call Transcripts**
```bash
curl -X POST http://localhost:8000/ingest-transcripts
```
Generates synthetic sales-call transcripts using Azure OpenAI and stores them in the database.

2. **Compute AI-Driven Insights**
```bash
curl -X POST http://localhost:8000/compute-insights
```
Analyzes stored transcripts to compute:
- Agent talk ratio
- Customer sentiment score  
Stores results in the `call_insights` table.

---

### 📞 Call Management APIs (`/api/v1/calls`)

- **List All Calls**
```bash
curl http://localhost:8000/api/v1/calls
```
Returns a list of all call transcripts (optionally supports pagination and filtering).

- **Get Call by ID**
```bash
curl http://localhost:8000/api/v1/calls/{call_id}
```
Fetches the full transcript and metadata for a specific call.

- **Get Coaching Recommendations**
```bash
curl http://localhost:8000/api/v1/calls/{call_id}/recommendations
```
Returns tailored coaching tips based on detected sentiment and agent speaking behavior.

---

### 📊 Analytics APIs (`/api/v1/analytics`)

- **Agent-wise Analytics**
```bash
curl http://localhost:8000/api/v1/analytics/agents
```
Returns aggregated analytics per agent including:
- Average sentiment score
- Average agent talk ratio  
Supports optional filters (e.g., by agent name or date).

---

## 📂 Project Structure

```
app/
├── api/
│   ├── routes_calls.py
│   └── routes_analytics.py
├── ingest/
│   └── llm_transcript_ingestion.py
├── insights/
│   └── generate_insights.py
├── models.py
├── schemas.py
├── db.py
├── main.py
```

---

## 📌 Notes

- Use `tsvector`-based GIN indexing for fast search on transcript content.
- Pre-computed insights ensure the `/recommendations` and `/analytics/agents` endpoints are fast.
- The `embedding` column is stored as stringified list — adapt as needed if using pgvector.


