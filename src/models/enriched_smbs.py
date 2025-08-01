from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from ..database.connection import Base

class EnrichedSMB(Base):
    __tablename__ = "enriched_smbs"
    
    uei = Column(String(50), primary_key=True, index=True)
    organization_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255))
    state = Column(String(50), index=True)
    naics_code = Column(String(20), index=True)
    google_reviews_rating = Column(Float)
    google_reviews_count = Column(Integer)
    linkedin_company_url = Column(String(500))
    owner_linkedin_url = Column(String(500))
    estimated_revenue = Column(Float)
    employee_count = Column(Integer)
    years_in_business = Column(Integer)
    succession_risk_score = Column(Float, index=True)
    digital_presence_score = Column(Float)
    last_enriched = Column(DateTime)
    raw_data = Column(JSON)
