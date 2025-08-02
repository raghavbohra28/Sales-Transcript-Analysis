from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker



# DATABASE_URL = "sqlite:///./sales_calls.db" 
DATABASE_URL = "postgresql://rootuser:rootpass@localhost/sales_calls" 

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)
print("Database connected:", inspector.get_table_names())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
