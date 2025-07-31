#!/bin/bash
# Complete API Setup for DSBS Compass Platform
echo "🚀 Setting up Compass Platform API..."

# Step 1: Create database connection module
echo "📡 Creating database connection..."
mkdir -p src/database
cat > src/database/connection.py << 'INNER_EOF'
"""
Database connection for KBI Labs
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = "postgresql://kbi_user:your_postgres_password_here@kbi_postgres:5432/kbi_labs"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
INNER_EOF

# Step 2: Create company model
echo "🏢 Creating company model..."
mkdir -p src/models
cat > src/models/companies.py << 'INNER_EOF'
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from ..database.connection import Base

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_name = Column(String(255), nullable=False, index=True)
    capabilities_narrative = Column(Text)
    capabilities_statement_link = Column(String(500))
    active_sba_certifications = Column(String(500))
    contact_first_name = Column(String(100))
    contact_last_name = Column(String(100))
    job_title = Column(String(200))
    email = Column(String(255))
    address_line_1 = Column(String(255))
    address_line_2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50), index=True)
    zipcode = Column(String(20))
    website = Column(String(500))
    uei = Column(String(50), unique=True, index=True)
    phone_number = Column(String(50))
    primary_naics_code = Column(String(20), index=True)
    legal_structure = Column(String(100))
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
INNER_EOF

# Step 3: Update main API router
echo "🔗 Updating main API router..."
cat > src/api/v1/api.py << 'INNER_EOF'
from fastapi import APIRouter
from .endpoints import companies

api_router = APIRouter()
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
INNER_EOF

# Step 4: Create __init__.py files
touch src/__init__.py src/api/__init__.py src/api/v1/__init__.py src/api/v1/endpoints/__init__.py src/database/__init__.py src/models/__init__.py

# Step 5: Install dependencies
docker exec -it kbi_api pip install sqlalchemy

echo "✅ API setup complete!"
