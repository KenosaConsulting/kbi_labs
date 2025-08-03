from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use SQLite for local testing, PostgreSQL for production
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./kbi_labs.db"  # Local SQLite fallback
)

# Create engine with PostgreSQL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
