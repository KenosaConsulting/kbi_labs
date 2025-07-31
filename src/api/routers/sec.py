#!/usr/bin/env python3
"""
SEC EDGAR API Router for KBI Labs
Provides comprehensive financial intelligence and compliance monitoring endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from src.integrations.government.sec_edgar import SECEdgarAPI, SECCompanyInfo, SECFiling, find_company_cik

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3/sec", tags=["SEC EDGAR"])

@router.get("/health")
async def sec_health_check():
    """Health check for SEC EDGAR API integration"""
    return {
        "service": "SEC EDGAR API",
        "status": "operational",
        "base_url": "https://data.sec.gov",
        "rate_limit": "10 requests/second",
        "authentication": "none_required",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/company/{cik}")
async def get_company_info(
    cik: str = Path(..., description="Company CIK (Central Index Key)")
) -> Dict[str, Any]:
    """
    Get basic company information by CIK
    
    Args:
        cik: Company Central Index Key (CIK)
        
    Returns:
        Company registration details including name, ticker, exchange, and business address
    """
    async with SECEdgarAPI() as sec_api:
        company_info = await sec_api.get_company_info(cik)
        
        if not company_info:
            raise HTTPException(
                status_code=404, 
                detail=f"Company with CIK {cik} not found or SEC API unavailable"
            )
        
        return {
            "cik": company_info.cik,
            "name": company_info.name,
            "ticker": company_info.ticker,
            "exchange": company_info.exchange,
            "sic": company_info.sic,
            "business_address": company_info.business_address,
            "data_source": "SEC EDGAR",
            "retrieved_at": datetime.now().isoformat()
        }

@router.get("/filings/{cik}")
async def get_company_filings(
    cik: str = Path(..., description="Company CIK (Central Index Key)"),
    form_type: Optional[str] = Query(None, description="Filter by form type (e.g., 10-K, 10-Q, 8-K)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of filings to return")
) -> Dict[str, Any]:
    """
    Get company SEC filings with optional form type filter
    
    Args:
        cik: Company Central Index Key
        form_type: Optional filter by form type (10-K, 10-Q, 8-K, etc.)
        limit: Maximum number of filings to return (1-500)
        
    Returns:
        List of SEC filings with metadata
    """
    async with SECEdgarAPI() as sec_api:
        filings = await sec_api.get_company_filings(cik, form_type, limit)
        
        if not filings:
            raise HTTPException(
                status_code=404,
                detail=f"No filings found for CIK {cik}" + (f" with form type {form_type}" if form_type else "")
            )
        
        filing_data = []
        for filing in filings:
            filing_data.append({
                "accession_number": filing.accession_number,
                "filing_date": filing.filing_date,
                "report_date": filing.report_date,
                "form": filing.form,
                "file_number": filing.file_number,
                "items": filing.items,
                "size": filing.size,
                "is_xbrl": filing.is_xbrl,
                "is_inline_xbrl": filing.is_inline_xbrl
            })
        
        return {
            "cik": cik,
            "form_type_filter": form_type,
            "total_filings": len(filing_data),
            "filings": filing_data,
            "data_source": "SEC EDGAR",
            "retrieved_at": datetime.now().isoformat()
        }

@router.get("/facts/{cik}")
async def get_company_facts(
    cik: str = Path(..., description="Company CIK (Central Index Key)")
) -> Dict[str, Any]:
    """
    Get company financial facts from XBRL filings
    
    Args:
        cik: Company Central Index Key
        
    Returns:
        Comprehensive financial facts and metrics from XBRL data
    """
    async with SECEdgarAPI() as sec_api:
        facts = await sec_api.get_company_facts(cik)
        
        if not facts:
            raise HTTPException(
                status_code=404,
                detail=f"No financial facts found for CIK {cik}"
            )
        
        return {
            "cik": cik,
            "facts": facts,
            "data_source": "SEC EDGAR XBRL",
            "retrieved_at": datetime.now().isoformat()
        }

@router.get("/financials/{cik}")
async def get_financial_metrics(
    cik: str = Path(..., description="Company CIK (Central Index Key)")
) -> Dict[str, Any]:
    """
    Get key financial metrics extracted from company facts
    
    Args:
        cik: Company Central Index Key
        
    Returns:
        Key financial metrics including revenue, assets, liabilities, equity, and cash
    """
    async with SECEdgarAPI() as sec_api:
        metrics = await sec_api.get_financial_metrics(cik)
        
        if not metrics:
            raise HTTPException(
                status_code=404,
                detail=f"No financial metrics available for CIK {cik}"
            )
        
        return {
            "cik": cik,
            "financial_metrics": metrics,
            "data_source": "SEC EDGAR XBRL",
            "retrieved_at": datetime.now().isoformat()
        }

@router.get("/search/ticker/{ticker}")
async def search_by_ticker(
    ticker: str = Path(..., description="Stock ticker symbol")
) -> Dict[str, Any]:
    """
    Search for company information by stock ticker
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
        
    Returns:
        Company information if found
    """
    async with SECEdgarAPI() as sec_api:
        company_info = await sec_api.search_by_ticker(ticker)
        
        if not company_info:
            raise HTTPException(
                status_code=404,
                detail=f"No company found with ticker {ticker}"
            )
        
        return {
            "ticker": ticker.upper(),
            "cik": company_info.cik,
            "name": company_info.name,
            "exchange": company_info.exchange,
            "sic": company_info.sic,
            "business_address": company_info.business_address,
            "data_source": "SEC EDGAR",
            "retrieved_at": datetime.now().isoformat()
        }

@router.get("/search/name/{company_name}")
async def search_by_name(
    company_name: str = Path(..., description="Company name for fuzzy search")
) -> Dict[str, Any]:
    """
    Search for company CIK by company name (fuzzy matching)
    
    Args:
        company_name: Company name to search for
        
    Returns:
        Best matching company CIK and basic info
    """
    cik = await find_company_cik(company_name)
    
    if not cik:
        raise HTTPException(
            status_code=404,
            detail=f"No company found matching '{company_name}'"
        )
    
    # Get full company info with the found CIK
    async with SECEdgarAPI() as sec_api:
        company_info = await sec_api.get_company_info(cik)
        
        if not company_info:
            raise HTTPException(
                status_code=404,
                detail=f"Company data not available for found CIK {cik}"
            )
        
        return {
            "search_term": company_name,
            "cik": company_info.cik,
            "name": company_info.name,
            "ticker": company_info.ticker,
            "exchange": company_info.exchange,
            "sic": company_info.sic,
            "business_address": company_info.business_address,
            "data_source": "SEC EDGAR",
            "retrieved_at": datetime.now().isoformat()
        }

@router.get("/risk-factors/{cik}")
async def get_risk_factors(
    cik: str = Path(..., description="Company CIK (Central Index Key)")
) -> Dict[str, Any]:
    """
    Extract risk factors from most recent 10-K filing
    
    Args:
        cik: Company Central Index Key
        
    Returns:
        Risk factors and related filing information
    """
    async with SECEdgarAPI() as sec_api:
        risk_factors = await sec_api.get_risk_factors(cik)
        
        return {
            "cik": cik,
            "risk_factors": risk_factors,
            "note": "Full risk factor extraction requires HTML parsing implementation",
            "data_source": "SEC EDGAR",
            "retrieved_at": datetime.now().isoformat()
        }

@router.get("/insider-activity/{cik}")
async def get_insider_activity(
    cik: str = Path(..., description="Company CIK (Central Index Key)")
) -> Dict[str, Any]:
    """
    Get insider trading activity from Form 4 filings
    
    Args:
        cik: Company Central Index Key
        
    Returns:
        Recent insider trading activity and Form 4 filings
    """
    async with SECEdgarAPI() as sec_api:
        insider_activity = await sec_api.get_insider_activity(cik)
        
        return {
            "cik": cik,
            "insider_activity": insider_activity,
            "note": "Full transaction details require HTML parsing of Form 4 filings",
            "data_source": "SEC EDGAR",
            "retrieved_at": datetime.now().isoformat()
        }

@router.get("/analysis/{cik}")
async def get_comprehensive_analysis(
    cik: str = Path(..., description="Company CIK (Central Index Key)")
) -> Dict[str, Any]:
    """
    Get comprehensive financial and regulatory analysis for a company
    
    Args:
        cik: Company Central Index Key
        
    Returns:
        Complete analysis including company info, recent filings, financial metrics, and risk assessment
    """
    async with SECEdgarAPI() as sec_api:
        # Get all data in parallel
        company_info = await sec_api.get_company_info(cik)
        recent_filings = await sec_api.get_company_filings(cik, limit=10)
        financial_metrics = await sec_api.get_financial_metrics(cik)
        risk_factors = await sec_api.get_risk_factors(cik)
        insider_activity = await sec_api.get_insider_activity(cik)
        
        if not company_info:
            raise HTTPException(
                status_code=404,
                detail=f"Company with CIK {cik} not found"
            )
        
        # Build comprehensive analysis
        analysis = {
            "cik": cik,
            "company_info": {
                "name": company_info.name,
                "ticker": company_info.ticker,
                "exchange": company_info.exchange,
                "sic": company_info.sic,
                "business_address": company_info.business_address
            },
            "recent_filings": {
                "count": len(recent_filings),
                "filings": [
                    {
                        "form": filing.form,
                        "filing_date": filing.filing_date,
                        "accession_number": filing.accession_number
                    } for filing in recent_filings[:5]  # Top 5 most recent
                ]
            },
            "financial_metrics": financial_metrics,
            "risk_assessment": {
                "risk_factors_available": True if risk_factors else False,
                "recent_insider_activity": len(insider_activity),
                "compliance_status": "Current" if recent_filings else "Unknown"
            },
            "data_completeness": {
                "company_info": bool(company_info),
                "financial_data": bool(financial_metrics),
                "recent_filings": bool(recent_filings),
                "risk_factors": bool(risk_factors)
            },
            "data_source": "SEC EDGAR",
            "analysis_date": datetime.now().isoformat()
        }
        
        return analysis

# Additional utility endpoints
@router.get("/cik-lookup/{identifier}")
async def lookup_cik(
    identifier: str = Path(..., description="Company ticker or name"),
    search_type: str = Query("auto", description="Search type: 'ticker', 'name', or 'auto'")
) -> Dict[str, Any]:
    """
    Universal CIK lookup by ticker or company name
    
    Args:
        identifier: Company ticker symbol or name
        search_type: Type of search to perform
        
    Returns:
        Company CIK and basic information
    """
    async with SECEdgarAPI() as sec_api:
        company_info = None
        
        if search_type == "ticker" or (search_type == "auto" and len(identifier) <= 5 and identifier.isupper()):
            # Try ticker search first
            company_info = await sec_api.search_by_ticker(identifier)
        
        if not company_info and (search_type == "name" or search_type == "auto"):
            # Try name search
            cik = await find_company_cik(identifier)
            if cik:
                company_info = await sec_api.get_company_info(cik)
        
        if not company_info:
            raise HTTPException(
                status_code=404,
                detail=f"No company found for identifier '{identifier}'"
            )
        
        return {
            "search_identifier": identifier,
            "search_type": search_type,
            "cik": company_info.cik,
            "name": company_info.name,
            "ticker": company_info.ticker,
            "data_source": "SEC EDGAR",
            "retrieved_at": datetime.now().isoformat()
        }