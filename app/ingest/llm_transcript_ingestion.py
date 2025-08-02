import asyncio
import json
import os
import random
from datetime import datetime
from faker import Faker
import openai
from openai import AzureOpenAI
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv
from app.database import engine, SessionLocal
from sqlalchemy.sql import text

# Load API Key from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

fake = Faker()
NUM_TRANSCRIPTS = 2  # keep low for now to avoid high token usage
OUTPUT_FOLDER = "data/raw"

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("AZURE_OPENAI_MODELNAME")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
subscription_key = os.getenv("AZURE_OPENAI_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

client = AsyncAzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

def build_prompt():
    return (
        "Simulate a realistic sales call transcript between a CUSTOMER and a SALES AGENT.\n\n"
        "Context:\n"
        "- The call is from a business that offers software-as-a-service (SaaS), electronics, or e-commerce solutions.\n"
        "- The customer may have queries about billing issues, password resets, refund requests, feature complaints, product inquiries, or pricing.\n"
        "- The agent may be trying to upsell a new plan, resolve a complaint, or troubleshoot an issue.\n"
        "- Tone should be professional and conversational — not robotic. It can include both positive and negative sentiments.\n"
        "- The agent should remain courteous and helpful throughout.\n"
        "- The customer may sometimes be upset, confused, grateful, or curious.\n"
        "- Mention some realistic product names, services, or terms if needed (e.g., ‘Pro plan’, ‘billing cycle’, ‘login portal’, etc.).\n"
        "- Keep the flow believable. Don’t go too generic — show slight context awareness.\n\n"
        "Instructions:\n"
        "- Alternate between 'Agent:' and 'Customer:' lines.\n"
        "- Limit the conversation to **10–12 exchanges** total.\n"
        "- No need for long paragraphs — 1–2 sentences per line is sufficient.\n"
        "- End the conversation naturally, like a real call would end (e.g., with thanks, a solution offered, or a follow-up promised).\n\n"
        "Transcript:\n"
    )

async def generate_transcript():
    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful sales agent simulator."},
                {"role": "user", "content": build_prompt()}
            ],
            temperature=1.0,
            max_tokens=4096,
            top_p=1.0,
            model=deployment
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Error generating transcript:", e)
        return None

def generate_call_metadata(call_num):
    start_time = fake.date_time_between(start_date="-30d", end_date="now")
    duration = random.randint(60, 600)

    return {
        "call_id": f"CALL_{call_num:04}",
        "agent_id": f"AGENT_{random.randint(100, 999)}",
        "customer_id": f"CUST_{random.randint(1000, 9999)}",
        "language": "en",
        "start_time": start_time.isoformat(),
        "duration_seconds": duration,
    }

async def save_transcript(call_data):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    path = os.path.join(OUTPUT_FOLDER, f"{call_data['call_id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(call_data, f, indent=2)

async def main():
    tasks = []
    for i in range(NUM_TRANSCRIPTS):
        transcript = await generate_transcript()
        if transcript:
            call = generate_call_metadata(i)
            call["transcript"] = transcript
            await save_transcript(call)
            await save_to_postgres(call)
            print(f"Saved {call['call_id']}")
        await asyncio.sleep(1.5)  # Respect rate limits


async def save_to_postgres(call_data):
    session = SessionLocal()
    try:
        insert_stmt = text("""
            INSERT INTO call_transcripts (
                call_id, agent_id, customer_id, language, start_time, duration_seconds, transcript
            ) VALUES (
                :call_id, :agent_id, :customer_id, :language, :start_time, :duration_seconds, :transcript
            )
        """)
        session.execute(insert_stmt, {
            "call_id": call_data["call_id"],
            "agent_id": call_data["agent_id"],
            "customer_id": call_data["customer_id"],
            "language": call_data["language"],
            "start_time": call_data["start_time"],
            "duration_seconds": call_data["duration_seconds"],
            "transcript": call_data["transcript"]
        })
        session.commit()
    except Exception as e:
        print("Error saving to postgres:", e)
        session.rollback()
    finally:
        session.close()

# if __name__ == "__main__":
#     asyncio.run(main())
