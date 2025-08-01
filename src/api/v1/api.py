from fastapi import APIRouter
from .endpoints import innovation, companies, economic_intelligence, market_fragmentation, digital_gap

api_router = APIRouter()
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(economic_intelligence.router, prefix="/economic", tags=["economic"])
api_router.include_router(digital_gap.router, prefix="/digital-gap", tags=["digital-gap"])
api_router.include_router(market_fragmentation.router, prefix="/fragmentation", tags=["fragmentation"])
api_router.include_router(innovation.router, prefix="/innovation", tags=["innovation"])
