from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class EnrichedCompany(Base):
    __tablename__ = 'enriched_companies'
    
    # Core identifiers
    uei = Column(String(50), primary_key=True)
    organization_name = Column(String(255))
    primary_naics = Column(String(10), index=True)
    state = Column(String(2), index=True)
    city = Column(String(100))
    zipcode = Column(String(10))
    website = Column(String(255))
    phone_number = Column(String(20))
    
    # Enrichment tracking
    last_enriched = Column(DateTime)
    enrichment_version = Column(String(10))
    enrichment_status = Column(JSON)
    
    # Government data
    sam_registration_status = Column(String(50))
    cage_code = Column(String(20))
    federal_contracts_count = Column(Integer, default=0)
    federal_contracts_value = Column(Float, default=0)
    latest_contract_date = Column(DateTime)
    set_aside_types = Column(JSON)
    
    # Economic indicators
    economic_indicators = Column(JSON)
    market_fragmentation_score = Column(Float)
    industry_concentration = Column(Float)
    
    # Innovation metrics
    patent_count = Column(Integer, default=0)
    patent_citations = Column(Integer, default=0)
    r_and_d_intensity = Column(Float)
    innovation_score = Column(Float)
    nsf_grants = Column(JSON)
    
    # Digital presence
    has_website = Column(Boolean, default=False)
    website_quality_score = Column(Float)
    social_media_presence = Column(JSON)
    online_reviews_count = Column(Integer, default=0)
    average_rating = Column(Float)
    
    # Risk scores
    succession_risk_score = Column(Float)
    financial_risk_score = Column(Float)
    operational_risk_score = Column(Float)
    overall_risk_rating = Column(String(20))
    
    # Growth indicators
    growth_potential_score = Column(Float)
    acquisition_readiness = Column(Float)
    market_expansion_opportunities = Column(JSON)
    
    # Calculated insights
    pe_investment_score = Column(Float)
    business_health_grade = Column(String(2))
    peer_percentile = Column(Float)
    key_recommendations = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
