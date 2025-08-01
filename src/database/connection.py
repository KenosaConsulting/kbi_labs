from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use PostgreSQL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://kbi_user:your_postgres_password_here@kbi_postgres:5432/kbi_labs"
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
