from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker



DATABASE_URL = "sqlite:///./sales_calls.db"  # For dev. Use PostgreSQL in prod.

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
inspector = inspect(engine)
print("Database connected:", inspector.get_table_names())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
