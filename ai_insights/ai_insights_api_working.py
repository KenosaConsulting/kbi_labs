#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import json
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

class AIInsightsGenerator:
    def __init__(self):
        self.openai_available = False
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            if os.getenv('OPENAI_API_KEY'):
                self.openai_available = True
        except:
            print("OpenAI not available, using enhanced simulation")
    
    def generate_insights(self, company_data):
        """Generate AI insights for a company"""
        if self.openai_available:
            return self._generate_openai_insights(company_data)
        else:
            return self._generate_enhanced_simulated_insights(company_data)
    
    def _generate_enhanced_simulated_insights(self, params):
        """Generate enhanced simulated insights based on company metrics"""
        score = float(params.get('score', 0))
        grade = params.get('grade', 'N/A')
        contracts = int(params.get('contracts', 0))
        value = float(params.get('value', 0))
        patents = int(params.get('patents', 0))
        nsf = float(params.get('nsf', 0))
        naics = params.get('naics', 'N/A')
        state = params.get('state', 'N/A')
        name = params.get('name', 'Unknown Company')
        
        # Calculate derived metrics
        avg_contract = value / contracts if contracts > 0 else 0
        innovation_index = min(100, (patents * 10) + (nsf / 100000))
        
        # Determine recommendation based on score
        if score >= 80:
            recommendation = "Strong Buy"
            investment_score = 85 + random.randint(0, 10)
        elif score >= 70:
            recommendation = "Buy"
            investment_score = 70 + random.randint(0, 14)
        elif score >= 50:
            recommendation = "Hold"
            investment_score = 50 + random.randint(0, 19)
        else:
            recommendation = "Sell"
            investment_score = 30 + random.randint(0, 19)
        
        # Industry-specific insights
        industry_desc = self._get_industry_description(naics)
        market_density = self._calculate_market_density(state, naics)
        
        # Generate specific insights based on metrics
        key_strengths = []
        if contracts > 10:
            key_strengths.append(f"Established federal contractor with {contracts} active contracts")
        if avg_contract > 1000000:
            key_strengths.append(f"High-value contracts averaging ${avg_contract/1000000:.1f}M")
        if patents > 0:
            key_strengths.append(f"Innovation leader with {patents} patents demonstrating R&D capability")
        if grade in ['A', 'B']:
            key_strengths.append(f"Strong business health grade ({grade}) indicating financial stability")
        if score >= 70:
            key_strengths.append("High PE investment score showing strong acquisition potential")
        
        # Growth opportunities based on industry
        growth_opportunities = []
        if contracts < 5:
            growth_opportunities.append("Expand federal contracting through SAM.gov certifications")
        if naics[:2] in ['54', '51']:
            growth_opportunities.append("Leverage technology expertise for digital transformation services")
        if market_density != "High Competition":
            growth_opportunities.append(f"Geographic expansion opportunity in {market_density.lower()} market")
        growth_opportunities.append(f"Industry consolidation play in {industry_desc} sector")
        if patents == 0:
            growth_opportunities.append("Develop IP portfolio to increase company valuation")
        
        # Risk factors
        risk_factors = []
        if contracts == 0:
            risk_factors.append("No federal contract revenue diversification")
        if grade in ['C', 'D', 'F']:
            risk_factors.append(f"Business health grade of {grade} requires immediate attention")
        if market_density == "High Competition":
            risk_factors.append("Highly competitive market may limit growth potential")
        if avg_contract > 5000000:
            risk_factors.append("High contract concentration risk")
        risk_factors.append(f"Industry-specific risks in {industry_desc}")
        
        # Action items
        action_items = [
            "Conduct management team interviews and capability assessment",
            "Review last 3 years of financial statements and tax returns",
            f"Analyze competitive landscape in {industry_desc} sector",
            "Evaluate customer concentration and contract pipeline",
            "Assess technology stack and digital infrastructure",
            "Review employee retention rates and key personnel dependencies"
        ]
        
        return {
            "recommendation": recommendation,
            "investment_score": investment_score,
            "key_strengths": key_strengths[:5],
            "growth_opportunities": growth_opportunities[:5],
            "risk_factors": risk_factors[:5],
            "market_position": f"{'Strong' if score >= 70 else 'Moderate'} position in {industry_desc} with {market_density.lower()}",
            "competitive_advantages": [
                f"Federal contracting expertise in {industry_desc}",
                f"Strategic location in {state}",
                "Established business with proven track record"
            ],
            "action_items": action_items[:6],
            "financial_health": f"Grade {grade} with PE score of {score}/100 indicates {'strong' if grade in ['A', 'B'] else 'moderate'} financial health. {'Positive' if score >= 70 else 'Careful'} outlook for acquisition.",
            "innovation_score": int(innovation_index),
            "esg_considerations": [
                f"Environmental compliance in {industry_desc} sector",
                "Local workforce development opportunities",
                "Governance structure suitable for PE ownership"
            ],
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_industry_description(self, naics):
        """Get human-readable industry description from NAICS code"""
        naics_map = {
            '23': 'Construction',
            '31': 'Manufacturing', '32': 'Manufacturing', '33': 'Manufacturing',
            '42': 'Wholesale Trade',
            '44': 'Retail Trade', '45': 'Retail Trade',
            '48': 'Transportation', '49': 'Transportation',
            '51': 'Information Technology',
            '52': 'Finance and Insurance',
            '53': 'Real Estate',
            '54': 'Professional Services',
            '56': 'Administrative Services',
            '61': 'Educational Services',
            '62': 'Healthcare',
            '71': 'Arts and Entertainment',
            '72': 'Accommodation and Food Services',
            '81': 'Other Services',
            '92': 'Public Administration'
        }
        
        if naics and len(naics) >= 2:
            prefix = naics[:2]
            return naics_map.get(prefix, 'General Business')
        return 'General Business'
    
    def _calculate_market_density(self, state, naics):
        """Calculate market density for the state/industry combination"""
        high_density_states = ['CA', 'NY', 'TX', 'FL', 'IL']
        high_density_industries = ['51', '52', '54']
        
        if state in high_density_states and naics[:2] in high_density_industries:
            return "High Competition"
        elif state in high_density_states or naics[:2] in high_density_industries:
            return "Moderate Competition"
        else:
            return "Low Competition"

# Initialize the generator
generator = AIInsightsGenerator()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'AI Insights API',
        'openai_available': generator.openai_available
    })

@app.route('/api/insights/<uei>', methods=['GET'])
def get_insights(uei):
    """Generate AI insights for a company"""
    try:
        # Get parameters from query string
        params = {
            'uei': uei,
            'name': request.args.get('name', 'Unknown'),
            'score': request.args.get('score', 0),
            'grade': request.args.get('grade', 'N/A'),
            'contracts': request.args.get('contracts', 0),
            'value': request.args.get('value', 0),
            'city': request.args.get('city', 'N/A'),
            'state': request.args.get('state', 'N/A'),
            'naics': request.args.get('naics', 'N/A'),
            'patents': request.args.get('patents', 0),
            'nsf': request.args.get('nsf', 0)
        }
        
        # Generate insights
        insights = generator.generate_insights(params)
        
        return jsonify({
            'success': True,
            'data': insights
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Enhanced AI Insights API on port 5001...")
    print(f"OpenAI Available: {generator.openai_available}")
    app.run(host='0.0.0.0', port=5001, debug=False)

    def _generate_openai_insights(self, params):
        """Generate insights using OpenAI GPT-4"""
        try:
            # Prepare the context
            context = self._prepare_context(params)
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a private equity investment analyst providing detailed company analysis."},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            result['generated_at'] = datetime.now().isoformat()
            return result
            
        except Exception as e:
            print(f"OpenAI error: {e}")
            # Fall back to enhanced simulation
            return self._generate_enhanced_simulated_insights(params)
    
    def _prepare_context(self, params):
        """Prepare context for GPT-4"""
        score = float(params.get('score', 0))
        grade = params.get('grade', 'N/A')
        contracts = int(params.get('contracts', 0))
        value = float(params.get('value', 0))
        patents = int(params.get('patents', 0))
        nsf = float(params.get('nsf', 0))
        naics = params.get('naics', 'N/A')
        state = params.get('state', 'N/A')
        name = params.get('name', 'Unknown Company')
        
        # Calculate derived metrics
        avg_contract = value / contracts if contracts > 0 else 0
        innovation_index = (patents * 10) + (nsf / 100000) if patents or nsf else 0
        
        # Get industry context
        industry_desc = self._get_industry_description(naics)
        market_density = self._calculate_market_density(state, naics)
        
        return f"""
        Analyze this company as a Private Equity investment opportunity:
        
        Company: {name}
        Location: {params.get('city', 'N/A')}, {state}
        
        Key Metrics:
        - PE Investment Score: {score}/100
        - Business Health Grade: {grade}
        - Federal Contracts: {contracts} (Total Value: ${value:,.2f})
        - Average Contract Size: ${avg_contract:,.2f}
        - Patents: {patents}
        - NSF Funding: ${nsf:,.2f}
        - Industry: {industry_desc} (NAICS: {naics})
        - Innovation Index: {innovation_index:.1f}
        - Market Density: {market_density}
        
        Provide a comprehensive investment analysis. Return ONLY a JSON object with these exact keys:
        {{
            "recommendation": "Buy",  // Must be one of: Strong Buy, Buy, Hold, Sell
            "investment_score": 85,   // 0-100
            "key_strengths": ["strength1", "strength2"],  // 3-5 items
            "growth_opportunities": ["opportunity1", "opportunity2"],  // 3-5 items
            "risk_factors": ["risk1", "risk2"],  // 3-5 items
            "market_position": "Detailed position assessment",
            "competitive_advantages": ["advantage1", "advantage2"],  // 2-4 items
            "action_items": ["action1", "action2"],  // 4-6 items
            "financial_health": "Detailed health assessment",
            "innovation_score": 75,  // 0-100
            "esg_considerations": ["consideration1", "consideration2"]  // 2-3 items
        }}
        """
