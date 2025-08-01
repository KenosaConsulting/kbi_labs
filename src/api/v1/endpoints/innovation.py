from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import pandas as pd
import json
import asyncio
from src.data_processors.innovation_processor import InnovationAPIProcessor

router = APIRouter()

# Cache for innovation data
innovation_cache = {}

@router.get("/innovation/search/{organization_name}")
async def search_innovation_data(organization_name: str):
    """Get real-time innovation metrics for a specific organization"""
    
    # Check cache first
    if organization_name in innovation_cache:
        cached_data = innovation_cache[organization_name]
        # Return cached data if less than 24 hours old
        # Implementation detail omitted for brevity
    
    try:
        async with InnovationAPIProcessor() as processor:
            metrics = await processor.process_organization(organization_name)
            
        result = {
            "organization": organization_name,
            "innovation_score": metrics.innovation_score,
            "patents": {
                "total": metrics.patents_count,
                "last_5_years": metrics.patents_last_5_years,
                "classifications": metrics.patent_classifications[:10]
            },
            "nsf_funding": {
                "awards_count": metrics.nsf_awards_count,
                "total_funding": metrics.nsf_total_funding,
                "recent_awards": metrics.nsf_recent_awards
            },
            "analysis": {
                "r_and_d_intensity": metrics.r_and_d_intensity,
                "tech_adoption_stage": metrics.tech_adoption_stage
            },
            "last_updated": metrics.last_updated
        }
        
        # Cache the result
        innovation_cache[organization_name] = result
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/innovation/leaders")
async def get_innovation_leaders(
    state: Optional[str] = None,
    min_score: float = Query(default=50.0, ge=0, le=100),
    limit: int = Query(default=20, le=100)
):
    """Get top innovative companies by score"""
    
    try:
        # Load enriched data
        df = pd.read_csv("dsbs_with_innovation_metrics.csv")
        
        # Filter by state if provided
        if state:
            df = df[df['State'] == state]
        
        # Filter by minimum score
        df = df[df['innovation_score'] >= min_score]
        
        # Sort by innovation score
        df = df.sort_values('innovation_score', ascending=False)
        
        # Get top results
        results = []
        for _, row in df.head(limit).iterrows():
            results.append({
                "organization": row['Organization Name'],
                "state": row['State'],
                "city": row['City'],
                "innovation_score": row['innovation_score'],
                "patents_count": row.get('patents_count', 0),
                "nsf_funding": row.get('nsf_total_funding', 0),
                "r_and_d_intensity": row.get('r_and_d_intensity', 'Unknown'),
                "tech_adoption_stage": row.get('tech_adoption_stage', 'Unknown')
            })
        
        return {
            "count": len(results),
            "leaders": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/innovation/analysis/industry/{naics_code}")
async def analyze_industry_innovation(naics_code: str):
    """Analyze innovation metrics for a specific industry"""
    
    try:
        # Load data
        df = pd.read_csv("dsbs_with_innovation_metrics.csv")
        
        # Filter by NAICS code (assuming 2-digit prefix match)
        naics_prefix = naics_code[:2]
        df['naics_prefix'] = df['Primary NAICS code'].astype(str).str[:2]
        industry_df = df[df['naics_prefix'] == naics_prefix]
        
        if industry_df.empty:
            raise HTTPException(status_code=404, detail="No data for this industry")
        
        # Calculate industry statistics
        total_companies = len(industry_df)
        innovators = industry_df[industry_df['innovation_score'] > 0]
        
        result = {
            "naics_code": naics_code,
            "total_companies": total_companies,
            "companies_with_innovation": len(innovators),
            "innovation_rate": round(len(innovators) / total_companies * 100, 1),
            "average_innovation_score": round(industry_df['innovation_score'].mean(), 1),
            "total_patents": int(industry_df['patents_count'].sum()),
            "total_nsf_funding": float(industry_df['nsf_total_funding'].sum()),
            "r_and_d_distribution": industry_df['r_and_d_intensity'].value_counts().to_dict(),
            "tech_adoption_distribution": industry_df['tech_adoption_stage'].value_counts().to_dict(),
            "top_innovators": []
        }
        
        # Add top innovators
        for _, row in industry_df.nlargest(5, 'innovation_score').iterrows():
            result["top_innovators"].append({
                "organization": row['Organization Name'],
                "state": row['State'],
                "innovation_score": row['innovation_score']
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/innovation/opportunities")
async def find_innovation_opportunities(
    min_patents: int = Query(default=5, ge=0),
    max_funding: float = Query(default=500000, ge=0),
    limit: int = Query(default=20, le=100)
):
    """Find undervalued innovative companies (high patents, low funding)"""
    
    try:
        df = pd.read_csv("dsbs_with_innovation_metrics.csv")
        
        # Find companies with patents but limited NSF funding
        opportunities = df[
            (df['patents_count'] >= min_patents) & 
            (df['nsf_total_funding'] <= max_funding)
        ].copy()
        
        # Calculate opportunity score
        opportunities['opportunity_score'] = (
            opportunities['patents_count'] * 10 / 
            (opportunities['nsf_total_funding'] + 10000)  # Add 10k to avoid division by zero
        )
        
        # Sort by opportunity score
        opportunities = opportunities.sort_values('opportunity_score', ascending=False)
        
        results = []
        for _, row in opportunities.head(limit).iterrows():
            results.append({
                "organization": row['Organization Name'],
                "state": row['State'],
                "patents": int(row['patents_count']),
                "recent_patents": int(row.get('patents_last_5_years', 0)),
                "nsf_funding": float(row['nsf_total_funding']),
                "opportunity_score": round(row['opportunity_score'], 2),
                "tech_classifications": row.get('patent_classifications', '').split(',')[:3]
            })
        
        return {
            "count": len(results),
            "opportunities": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
