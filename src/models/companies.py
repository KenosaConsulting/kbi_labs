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
