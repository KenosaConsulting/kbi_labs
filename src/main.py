'''
KBI Labs FastAPI Application
Main entry point for the API
'''
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.api import api_router
from .api.v1.endpoints.ml.predictions import router as ml_router
from datetime import datetime
from typing import Optional, List, Dict
import json

# Create FastAPI app
app = FastAPI(
    title='KBI Labs - Compass Platform',
    description='AI-Powered SMB Intelligence and Business Discovery Platform',
    version='2.1.0'
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Configure this for production
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Mount static files
app.mount('/static', StaticFiles(directory='static'), name='static')

# Include API routers
app.include_router(api_router, prefix='/api/v1')
app.include_router(ml_router, prefix='/api/v1')

# Import AI services
try:
    from .ai_services.recommendation_engine import generate_recommendations_for_opportunities, get_recommendation_summary
    print('✅ AI Recommendation Engine loaded successfully')
except Exception as e:
    print(f'❌ AI Recommendation Engine loading error: {e}')
    generate_recommendations_for_opportunities = None
    get_recommendation_summary = None

# Import patent search module
from .patent_search_module import patent_engine

# Import auth module
try:
    from .auth_sqlite import auth_router
    app.include_router(auth_router)
    print('✅ SQLite auth system loaded')
except Exception as e:
    print(f'❌ Auth loading error: {e}')

# Health check endpoint
@app.get('/')
async def root():
    return {
        'message': 'KBI Labs Compass Platform API', 
        'status': 'operational',
        'endpoints': {
            'companies': '/api/v1/companies/',
            'insights': '/api/v1/companies/compass/insights',
            'stats': '/api/v1/companies/stats/by-state',
            'patents': {
                'search_by_org': '/api/patents/search/organization',
                'search_by_keyword': '/api/patents/search/keyword',
                'org_stats': '/api/patents/stats/organization',
                'top_holders': '/api/patents/top-holders'
            },
            'auth': {
                'register': '/api/auth/register',
                'login': '/api/auth/login',
                'verify': '/api/auth/verify'
            },
            'demos': {
                'simple': '/static/simple_demo.html',
                'enhanced': '/static/enhanced_demo.html',
                'patents': '/static/patent_search_demo.html',
                'auth': '/static/auth_demo_v2.html'
            }
        }
    }

# Patent search endpoints
@app.get('/api/patents/search/organization')
async def search_patents_by_org(
    org_name: str = Query(..., description='Organization name to search'),
    limit: int = Query(100, description='Maximum results to return')
):
    '''Search patents by organization name'''
    start_time = datetime.now()
    
    try:
        results = patent_engine.search_by_organization(org_name, limit)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            'results': results.to_dict('records'),
            'count': len(results),
            'query_time': elapsed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/patents/stats/organization')
async def get_org_stats(org_name: str = Query(..., description='Organization name')):
    '''Get patent statistics for an organization'''
    try:
        stats = patent_engine.get_org_patent_stats(org_name)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/patents/search/keyword')
async def search_patents_by_keyword(
    keyword: str = Query(..., description='Keyword to search in patent titles'),
    limit: int = Query(100, description='Maximum results to return')
):
    '''Search patents by keyword in title'''
    start_time = datetime.now()
    
    try:
        results = patent_engine.search_patents_by_keyword(keyword, limit)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            'results': results.to_dict('records'),
            'count': len(results),
            'query_time': elapsed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/patents/top-holders')
async def get_top_holders(
    year: Optional[int] = Query(None, description='Filter by year'),
    limit: int = Query(20, description='Number of top holders to return')
):
    '''Get top patent holders'''
    try:
        results = patent_engine.get_top_patent_holders(year, limit)
        return {
            'year': year if year else 'all_time',
            'top_holders': results.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/cache/stats')
async def get_cache_stats():
    '''Get Redis cache statistics'''
    try:
        stats = patent_engine.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/health')
async def health_check():
    return {'status': 'healthy'}

# AI Recommendation endpoints
@app.post('/api/ai/recommendations')
async def generate_recommendations(opportunities: List[Dict]):
    """Generate AI-powered recommendations for a list of opportunities"""
    try:
        if not generate_recommendations_for_opportunities:
            raise HTTPException(status_code=503, detail="AI Recommendation Engine not available")
        
        recommendations = generate_recommendations_for_opportunities(opportunities)
        
        return {
            'status': 'success',
            'recommendations': recommendations,
            'count': len(recommendations),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {str(e)}")

@app.post('/api/ai/recommendations/summary')
async def get_recommendations_summary(opportunities: List[Dict]):
    """Get a summary of AI recommendations for dashboard display"""
    try:
        if not get_recommendation_summary:
            raise HTTPException(status_code=503, detail="AI Recommendation Engine not available")
        
        summary = get_recommendation_summary(opportunities)
        
        return {
            'status': 'success',
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation summary failed: {str(e)}")

@app.get('/api/ai/status')
async def get_ai_status():
    """Get AI services status"""
    return {
        'status': 'success',
        'services': {
            'recommendation_engine': generate_recommendations_for_opportunities is not None,
            'opportunity_scorer': True,
            'ml_features': True
        },
        'version': '2.1.0',
        'deployment_id': 'KBI_LABS_FASTAPI_VERIFIED',
        'capabilities': [
            'Opportunity Scoring',
            'Intelligent Recommendations', 
            'Strategic Insights',
            'Market Analysis',
            'Capability Gap Analysis'
        ],
        'timestamp': datetime.now().isoformat()
    }

@app.get('/deployment/verify')
async def deployment_verification():
    """Unique endpoint to verify correct deployment"""
    return {
        'application': 'KBI Labs FastAPI Application',
        'version': '2.1.0',
        'ai_services': True,
        'deployment_timestamp': datetime.now().isoformat(),
        'verification_code': 'FASTAPI_AI_DEPLOYED_SUCCESSFULLY'
    }
