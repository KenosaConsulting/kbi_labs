"""Analytics schemas"""
from pydantic import BaseModel
from typing import Optional

class StateAnalytics(BaseModel):
    state: str
    company_count: int
    avg_pe_score: Optional[float] = None
    avg_patent_count: Optional[float] = None
    avg_nsf_funding: Optional[float] = None
    top_naics: Optional[str] = None
    grade_distribution: Optional[dict] = None

class OverviewAnalytics(BaseModel):
    total_companies: int
    states_covered: int
    total_patents: int
    total_nsf_funding: float
    avg_pe_score: float
    grade_distribution: dict
    top_states: list
    top_naics_codes: list
