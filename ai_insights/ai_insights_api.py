#!/usr/bin/env python3
"""
AI Insights API for KBI Labs
Generates real-time insights using GPT-4
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from openai import OpenAI
import asyncio
import aiohttp
from dataclasses import dataclass, asdict
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')
class CompanyInsight:
    """Structure for company insights"""
    investment_score: float
    recommendation: str
    key_strengths: List[str]
    growth_opportunities: List[str]
    risk_factors: List[str]
    market_position: str
    competitive_advantages: List[str]
    action_items: List[str]
    financial_health: str
    innovation_score: float
    esg_considerations: List[str]
    generated_at: str

class AIInsightsEngine:
    """GPT-4 powered insights engine for company analysis"""
    
    def __init__(self):
        self.model = "gpt-4-turbo-preview"
        self.max_retries = 3
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour
        
    async def generate_insights(self, company_data: Dict[str, Any]) -> CompanyInsight:
        """Generate comprehensive insights for a company using GPT-4"""
        
        # Check cache first
        cache_key = f"{company_data.get('uei', 'unknown')}_{company_data.get('organization_name', '')}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"Returning cached insights for {cache_key}")
                return cached_data
        
        # Prepare context for GPT-4
        context = self._prepare_context(company_data)
        
        # Generate insights with GPT-4
        insights = await self._call_gpt4(context, company_data)
        
        # Cache the results
        self.cache[cache_key] = (insights, time.time())
        
        return insights
    
    def _prepare_context(self, company_data: Dict[str, Any]) -> str:
        """Prepare context for GPT-4 analysis"""
        
        return f"""
        Analyze the following company data and provide investment insights:
        
        Company: {company_data.get('organization_name', 'Unknown')}
        Location: {company_data.get('city', 'N/A')}, {company_data.get('state', 'N/A')}
        
        Key Metrics:
        - PE Investment Score: {company_data.get('pe_investment_score', 'N/A')}
        - Business Health Grade: {company_data.get('business_health_grade', 'N/A')}
        - Federal Contracts: {company_data.get('federal_contracts_count', 0)}
        - Contract Value: ${company_data.get('federal_contracts_value', 0):,.2f}
        - Patent Count: {company_data.get('patent_count', 0)}
        - NSF Funding: ${company_data.get('nsf_total_funding', 0):,.2f}
        - Certifications: {company_data.get('certifications', [])}
        
        Industry: NAICS {company_data.get('primary_naics', 'N/A')}
        Website: {company_data.get('website', 'N/A')}
        
        Economic Context:
        - State GDP: ${company_data.get('state_gdp_billions', 0):.1f}B
        - State Population: {company_data.get('state_population', 0):,}
        
        Provide a comprehensive analysis including:
        1. Investment recommendation (Strong Buy/Buy/Hold/Sell)
        2. Key strengths (3-5 points)
        3. Growth opportunities (3-5 points)
        4. Risk factors (3-5 points)
        5. Market position assessment
        6. Competitive advantages
        7. Actionable recommendations for investors
        8. Financial health assessment
        9. Innovation score (0-100)
        10. ESG considerations
        
        Format your response as a JSON object.
        """
    
    async def _call_gpt4(self, context: str, company_data: Dict[str, Any]) -> CompanyInsight:
        """Call GPT-4 API and parse response"""
        
        for attempt in range(self.max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a senior investment analyst specializing in 
                            private equity and SMB investments. Provide data-driven insights 
                            based on the company metrics provided. Be specific and actionable.
                            Always respond with valid JSON."""
                        },
                        {
                            "role": "user",
                            "content": context
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                # Parse GPT-4 response
                insights_data = json.loads(response.choices[0].message.content)
                
                # Create CompanyInsight object
                return CompanyInsight(
                    investment_score=insights_data.get('investment_score', 
                        company_data.get('pe_investment_score', 0)),
                    recommendation=insights_data.get('recommendation', 'Hold'),
                    key_strengths=insights_data.get('key_strengths', []),
                    growth_opportunities=insights_data.get('growth_opportunities', []),
                    risk_factors=insights_data.get('risk_factors', []),
                    market_position=insights_data.get('market_position', 'Emerging'),
                    competitive_advantages=insights_data.get('competitive_advantages', []),
                    action_items=insights_data.get('action_items', []),
                    financial_health=insights_data.get('financial_health', 'Stable'),
                    innovation_score=insights_data.get('innovation_score', 50),
                    esg_considerations=insights_data.get('esg_considerations', []),
                    generated_at=datetime.now().isoformat()
                )
                
            except Exception as e:
                logger.error(f"GPT-4 API error (attempt {attempt + 1}): {str(e)}")
                if attempt == self.max_retries - 1:
                    # Return fallback insights
                    return self._generate_fallback_insights(company_data)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _generate_fallback_insights(self, company_data: Dict[str, Any]) -> CompanyInsight:
        """Generate fallback insights when GPT-4 is unavailable"""
        
        score = company_data.get('pe_investment_score', 50)
        grade = company_data.get('business_health_grade', 'C')
        
        # Simple rule-based recommendations
        if score >= 80 and grade in ['A', 'B']:
            recommendation = "Buy"
        elif score >= 60:
            recommendation = "Hold"
        else:
            recommendation = "Sell"
        
        return CompanyInsight(
            investment_score=score,
            recommendation=recommendation,
            key_strengths=["Established business", "Federal contractor"],
            growth_opportunities=["Market expansion", "Digital transformation"],
            risk_factors=["Market competition", "Economic uncertainty"],
            market_position="Established",
            competitive_advantages=["Domain expertise", "Government relationships"],
            action_items=["Monitor quarterly performance", "Assess expansion opportunities"],
            financial_health="Stable",
            innovation_score=60,
            esg_considerations=["Environmental compliance needed"],
            generated_at=datetime.now().isoformat()
        )

# Initialize insights engine
insights_engine = AIInsightsEngine()

@app.route('/api/insights/<uei>', methods=['GET'])
async def get_company_insights(uei: str):
    """Get AI-generated insights for a specific company"""
    
    try:
        # In production, fetch company data from database
        # For now, using sample data
        company_data = {
            'uei': uei,
            'organization_name': request.args.get('name', 'Sample Company'),
            'pe_investment_score': float(request.args.get('score', 75)),
            'business_health_grade': request.args.get('grade', 'B'),
            'federal_contracts_count': int(request.args.get('contracts', 5)),
            'federal_contracts_value': float(request.args.get('value', 1000000)),
            'city': request.args.get('city', 'New York'),
            'state': request.args.get('state', 'NY'),
            'primary_naics': request.args.get('naics', '541990'),
            'patent_count': int(request.args.get('patents', 2)),
            'nsf_total_funding': float(request.args.get('nsf', 50000))
        }
        
        # Generate insights
        insights = await insights_engine.generate_insights(company_data)
        
        return jsonify({
            'success': True,
            'data': asdict(insights)
        })
        
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/insights/batch', methods=['POST'])
async def get_batch_insights():
    """Get insights for multiple companies"""
    
    try:
        companies = request.json.get('companies', [])
        
        # Generate insights concurrently
        tasks = []
        for company in companies:
            task = insights_engine.generate_insights(company)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        return jsonify({
            'success': True,
            'data': [asdict(insight) for insight in results]
        })
        
    except Exception as e:
        logger.error(f"Error in batch insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/insights/compare', methods=['POST'])
async def compare_companies():
    """Generate comparative insights for multiple companies"""
    
    try:
        companies = request.json.get('companies', [])
        
        if len(companies) < 2:
            return jsonify({
                'success': False,
                'error': 'At least 2 companies required for comparison'
            }), 400
        
        # Prepare comparison context
        comparison_context = f"""
        Compare the following {len(companies)} companies for investment potential:
        
        """
        
        for i, company in enumerate(companies, 1):
            comparison_context += f"""
            Company {i}: {company.get('organization_name')}
            - Score: {company.get('pe_investment_score')}
            - Grade: {company.get('business_health_grade')}
            - Contracts: {company.get('federal_contracts_count')}
            - Industry: {company.get('primary_naics')}
            
            """
        
        comparison_context += """
        Provide a detailed comparison including:
        1. Ranking by investment potential
        2. Key differentiators
        3. Relative strengths and weaknesses
        4. Portfolio diversification benefits
        5. Recommended allocation percentages
        
        Format as JSON.
        """
        
        # Get GPT-4 comparison
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert portfolio manager. Provide detailed comparative analysis."
                },
                {
                    "role": "user",
                    "content": comparison_context
                }
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        comparison_data = json.loads(response.choices[0].message.content)
        
        return jsonify({
            'success': True,
            'data': comparison_data
        })
        
    except Exception as e:
        logger.error(f"Error in company comparison: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/insights/trends', methods=['GET'])
async def get_market_trends():
    """Get AI-powered market trends and predictions"""
    
    try:
        industry = request.args.get('industry', 'all')
        timeframe = request.args.get('timeframe', 'quarterly')
        
        # Generate market analysis
        context = f"""
        Provide market analysis for:
        - Industry: {industry}
        - Timeframe: {timeframe}
        
        Include:
        1. Current market trends
        2. Growth projections
        3. Key drivers
        4. Risk factors
        5. Investment opportunities
        6. Recommended sectors
        
        Format as JSON.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a market analyst specializing in SMB and private equity trends."
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        trends_data = json.loads(response.choices[0].message.content)
        
        return jsonify({
            'success': True,
            'data': trends_data
        })
        
    except Exception as e:
        logger.error(f"Error generating market trends: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Run with asyncio support
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)
