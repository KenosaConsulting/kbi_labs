"""Company schemas for API validation"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class CompanyBase(BaseModel):
    uei: str
    organization_name: str
    primary_naics: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    website: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

class Company(CompanyBase):
    """Basic company model for listings"""
    active_sba_certifications: Optional[str] = None
    pe_investment_score: Optional[float] = None
    business_health_grade: Optional[str] = None
    patent_count: Optional[int] = None
    nsf_awards_count: Optional[int] = None

class CompanyDetail(CompanyBase):
    """Detailed company model with all fields"""
    legal_structure: Optional[str] = None
    active_sba_certifications: Optional[str] = None
    capabilities_narrative: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    
    # Census data
    census_state_population: Optional[str] = None
    census_median_income: Optional[str] = None
    census_bachelors_degree: Optional[str] = None
    census_masters_degree: Optional[str] = None
    census_professional_degree: Optional[str] = None
    census_doctorate_degree: Optional[str] = None
    
    # Economic indicators
    fred_unemployment_rate: Optional[float] = None
    fred_unemployment_date: Optional[str] = None
    
    # Innovation metrics
    patent_count: Optional[int] = None
    nsf_awards_count: Optional[int] = None
    nsf_total_funding: Optional[float] = None
    nsf_recent_awards: Optional[str] = None
    
    # Scoring
    pe_investment_score: Optional[float] = None
    business_health_grade: Optional[str] = None
    scoring_factors: Optional[Dict[str, Any]] = None
    enrichment_timestamp: Optional[str] = None
    
    # Analytics
    analytics: Optional[Dict[str, Any]] = None

class CompanyList(BaseModel):
    """Response model for company list"""
    companies: List[Company]
    total: int
    skip: int
    limit: int
    filters: Optional[Dict[str, Any]] = {}

class StateAnalytics(BaseModel):
    """State-level analytics"""
    state: str
    company_count: int
    avg_pe_score: Optional[float]
    grade_a_count: int
    grade_b_count: int
    grade_c_count: int
    avg_patents: Optional[float]
    avg_nsf_funding: Optional[float]
