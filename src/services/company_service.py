"""Company Service with Real Database"""
from typing import List, Optional, Dict, Any
from src.models.database_manager import db_manager
from src.services.enrichment_pipeline import EnrichmentPipeline
from src.utils.cache import cache_service
import logging
import json

logger = logging.getLogger(__name__)

class CompanyService:
    def __init__(self):
        self.enrichment_pipeline = EnrichmentPipeline()
    
    async def list_companies(
        self,
        skip: int = 0,
        limit: int = 100,
        state: Optional[str] = None,
        search: Optional[str] = None,
        naics: Optional[str] = None,
        grade: Optional[str] = None,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """List companies from real database"""
        cache_key = f"companies:{skip}:{limit}:{state}:{search}:{naics}:{grade}"
        
        # Try cache first
        cached = await cache_service.get(cache_key)
        if cached:
            return cached
        
        # Build query with filters
        conditions = []
        params = []
        
        if state:
            conditions.append("state = ?")
            params.append(state)
        
        if search:
            conditions.append("(organization_name LIKE ? OR uei LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        if naics:
            conditions.append("primary_naics LIKE ?")
            params.append(f"{naics}%")
        
        if grade:
            conditions.append("business_health_grade = ?")
            params.append(grade)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Count query
        count_query = f"SELECT COUNT(*) as total FROM companies WHERE {where_clause}"
        count_result = await db_manager.execute_one(count_query, params)
        total_count = count_result['total'] if count_result else 0
        
        # Main query
        query = f"""
        SELECT uei, organization_name, primary_naics, state, city, 
               website, active_sba_certifications, pe_investment_score, 
               business_health_grade, patent_count, nsf_awards_count
        FROM companies 
        WHERE {where_clause}
        ORDER BY pe_investment_score DESC NULLS LAST, organization_name
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, skip])
        companies = await db_manager.execute_all(query, params)
        
        result = {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "companies": companies or []
        }
        
        # Cache for 5 minutes
        await cache_service.set(cache_key, result, expire=300)
        
        return result
    
    async def get_company_by_uei(self, uei: str) -> Optional[Dict[str, Any]]:
        """Get detailed company information"""
        cache_key = f"company:{uei}"
        
        # Try cache first
        cached = await cache_service.get(cache_key)
        if cached:
            return cached
        
        query = "SELECT * FROM companies WHERE uei = ?"
        company = await db_manager.execute_one(query, [uei])
        
        if company:
            # Parse JSON fields if they're stored as strings
            if company.get('scoring_factors') and isinstance(company['scoring_factors'], str):
                try:
                    company['scoring_factors'] = json.loads(company['scoring_factors'])
                except:
                    pass
            
            if company.get('nsf_recent_awards') and isinstance(company['nsf_recent_awards'], str):
                try:
                    company['nsf_recent_awards'] = json.loads(company['nsf_recent_awards'])
                except:
                    pass
            
            # Add analytics
            company['analytics'] = await self._get_company_analytics(uei)
            
            # Cache for 10 minutes
            await cache_service.set(cache_key, company, expire=600)
        
        return company
    
    async def get_top_companies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get top companies by PE investment score"""
        cache_key = f"top_companies:{limit}"
        
        # Try cache first
        cached = await cache_service.get(cache_key)
        if cached:
            return cached
        
        # Check if we have a pre-computed top_companies table
        try:
            query = "SELECT * FROM top_companies ORDER BY pe_investment_score DESC LIMIT ?"
            companies = await db_manager.execute_all(query, [limit])
        except:
            # Fallback to main table
            query = """
            SELECT uei, organization_name, primary_naics, state, city, 
                   website, active_sba_certifications, pe_investment_score, 
                   business_health_grade, patent_count, nsf_awards_count
            FROM companies 
            WHERE pe_investment_score IS NOT NULL
            ORDER BY pe_investment_score DESC
            LIMIT ?
            """
            companies = await db_manager.execute_all(query, [limit])
        
        # Cache for 30 minutes
        await cache_service.set(cache_key, companies or [], expire=1800)
        
        return companies or []
    
    async def get_state_analytics(self) -> List[Dict[str, Any]]:
        """Get analytics by state"""
        cache_key = "state_analytics"
        
        # Try cache first
        cached = await cache_service.get(cache_key)
        if cached:
            return cached
        
        # Check if we have pre-computed analytics
        try:
            query = "SELECT * FROM state_analytics ORDER BY company_count DESC"
            analytics = await db_manager.execute_all(query)
        except:
            # Compute on the fly
            query = """
            SELECT 
                state,
                COUNT(*) as company_count,
                AVG(pe_investment_score) as avg_pe_score,
                AVG(patent_count) as avg_patent_count,
                AVG(nsf_total_funding) as avg_nsf_funding,
                COUNT(CASE WHEN business_health_grade = 'A' THEN 1 END) as grade_a_count,
                COUNT(CASE WHEN business_health_grade = 'B' THEN 1 END) as grade_b_count,
                COUNT(CASE WHEN business_health_grade = 'C' THEN 1 END) as grade_c_count,
                COUNT(CASE WHEN business_health_grade = 'D' THEN 1 END) as grade_d_count,
                COUNT(CASE WHEN business_health_grade = 'F' THEN 1 END) as grade_f_count
            FROM companies 
            WHERE state IS NOT NULL
            GROUP BY state
            ORDER BY company_count DESC
            """
            results = await db_manager.execute_all(query)
            
            # Format results
            analytics = []
            for row in results or []:
                analytics.append({
                    'state': row['state'],
                    'company_count': row['company_count'],
                    'avg_pe_score': round(row['avg_pe_score'], 2) if row['avg_pe_score'] else None,
                    'avg_patent_count': round(row['avg_patent_count'], 2) if row['avg_patent_count'] else None,
                    'avg_nsf_funding': round(row['avg_nsf_funding'], 2) if row['avg_nsf_funding'] else None,
                    'grade_distribution': {
                        'A': row.get('grade_a_count', 0),
                        'B': row.get('grade_b_count', 0),
                        'C': row.get('grade_c_count', 0),
                        'D': row.get('grade_d_count', 0),
                        'F': row.get('grade_f_count', 0)
                    }
                })
        
        # Cache for 1 hour
        await cache_service.set(cache_key, analytics or [], expire=3600)
        
        return analytics or []
    
    async def enrich_company(self, uei: str) -> Dict[str, Any]:
        """Trigger enrichment for a specific company"""
        # Get current company data
        company = await self.get_company_by_uei(uei)
        if not company:
            raise ValueError(f"Company with UEI {uei} not found")
        
        # Run enrichment pipeline
        enriched_data = await self.enrichment_pipeline.enrich_company(company)
        
        # Update database with enriched data
        # This would be implemented based on your enrichment pipeline
        
        return {
            "uei": uei,
            "status": "enriched",
            "enriched_fields": list(enriched_data.keys())
        }
    
    async def _get_company_analytics(self, uei: str) -> Dict[str, Any]:
        """Get analytics for a specific company"""
        # This could include comparisons, rankings, etc.
        return {
            "industry_rank": None,  # Would calculate based on NAICS
            "state_rank": None,     # Would calculate based on state
            "growth_metrics": {},   # Would calculate if we had historical data
        }

# Create singleton instance
company_service = CompanyService()
