from fastapi import FastAPI
from models import Base
from database import engine

app = FastAPI(title="Sales Call Analytics API")

@app.get("/")
def read_root():
    return {"message": "Sales Analytics API is running"}

if __name__ == "__main__":
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
