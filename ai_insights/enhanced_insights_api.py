#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import json
import random
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

class EnhancedInsightsGenerator:
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
        """Generate enhanced AI insights with deeper analysis"""
        if self.openai_available:
            return self._generate_enhanced_openai_insights(company_data)
        else:
            return self._generate_enhanced_simulated_insights(company_data)
    
    def _generate_enhanced_openai_insights(self, params):
        """Generate enhanced insights using OpenAI GPT-4"""
        try:
            # Prepare enhanced context
            context = self._prepare_enhanced_context(params)
            
            # Call OpenAI with enhanced prompt
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are a senior private equity investment analyst with deep expertise in company valuation, 
                    market analysis, and strategic planning. Provide comprehensive, data-driven insights that would be valuable to PE partners 
                    making investment decisions. Always respond with valid JSON only."""},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            # Add additional analytics
            result['analytics'] = self._generate_analytics(params)
            result['peer_comparison'] = self._generate_peer_comparison(params)
            result['financial_projections'] = self._generate_projections(params)
            result['generated_at'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            print(f"OpenAI error: {e}")
            return self._generate_enhanced_simulated_insights(params)
    
    def _prepare_enhanced_context(self, params):
        """Prepare enhanced context for GPT-4"""
        score = float(params.get('score', 0))
        grade = params.get('grade', 'N/A')
        contracts = int(params.get('contracts', 0))
        value = float(params.get('value', 0))
        patents = int(params.get('patents', 0))
        nsf = float(params.get('nsf', 0))
        naics = params.get('naics', 'N/A')
        state = params.get('state', 'N/A')
        name = params.get('name', 'Unknown Company')
        
        # Calculate advanced metrics
        avg_contract = value / contracts if contracts > 0 else 0
        innovation_index = (patents * 10) + (nsf / 100000) if patents or nsf else 0
        revenue_per_contract = value / contracts if contracts > 0 else 0
        
        # Industry analysis
        industry_desc = self._get_industry_description(naics)
        market_density = self._calculate_market_density(state, naics)
        industry_growth = self._get_industry_growth_rate(naics)
        
        return f"""
        Analyze this company as a Private Equity investment opportunity with comprehensive detail:
        
        Company: {name}
        Location: {params.get('city', 'N/A')}, {state}
        
        Key Metrics:
        - PE Investment Score: {score}/100
        - Business Health Grade: {grade}
        - Federal Contracts: {contracts} (Total Value: ${value:,.2f})
        - Average Contract Size: ${avg_contract:,.2f}
        - Revenue per Contract: ${revenue_per_contract:,.2f}
        - Patents: {patents}
        - NSF Funding: ${nsf:,.2f}
        - Industry: {industry_desc} (NAICS: {naics})
        - Innovation Index: {innovation_index:.1f}
        - Market Density: {market_density}
        - Industry Growth Rate: {industry_growth}%
        
        Provide a comprehensive investment analysis including:
        
        1. Investment recommendation with detailed justification
        2. Valuation estimate and methodology
        3. Exit strategy options with 3-5 year timeline
        4. Synergy opportunities with portfolio companies
        5. Value creation opportunities post-acquisition
        6. Market expansion strategies
        7. Operational improvement areas
        8. Technology modernization opportunities
        
        Return ONLY a valid JSON object with these keys:
        {{
            "recommendation": "Buy",
            "investment_score": 85,
            "valuation_range": {{"low": 5000000, "high": 8000000, "methodology": "Multiple of EBITDA"}},
            "key_strengths": ["strength1", "strength2", "strength3", "strength4"],
            "growth_opportunities": ["opportunity1", "opportunity2", "opportunity3", "opportunity4"],
            "risk_factors": ["risk1", "risk2", "risk3"],
            "market_position": "Detailed position assessment",
            "competitive_advantages": ["advantage1", "advantage2", "advantage3"],
            "action_items": ["action1", "action2", "action3", "action4", "action5"],
            "financial_health": "Detailed health assessment",
            "innovation_score": 75,
            "esg_considerations": ["consideration1", "consideration2", "consideration3"],
            "exit_strategies": [{{"strategy": "Strategic Sale", "timeline": "3-5 years", "multiple": "2.5x"}}, {{"strategy": "PE Rollup", "timeline": "2-3 years", "multiple": "2.0x"}}],
            "value_creation_plan": ["initiative1", "initiative2", "initiative3"],
            "synergies": ["synergy1", "synergy2"],
            "operational_improvements": ["improvement1", "improvement2", "improvement3"]
        }}
        """
    
    def _generate_analytics(self, params):
        """Generate detailed analytics"""
        score = float(params.get('score', 0))
        contracts = int(params.get('contracts', 0))
        value = float(params.get('value', 0))
        
        return {
            "market_share_estimate": random.uniform(5, 25),
            "growth_potential": score * 0.8 + random.uniform(10, 30),
            "efficiency_ratio": min(100, (value / 100000) if value > 0 else 0),
            "contract_stability": min(100, contracts * 10),
            "innovation_capacity": float(params.get('patents', 0)) * 20,
            "market_penetration": random.uniform(15, 45),
            "customer_concentration": 100 - (contracts * 5) if contracts < 20 else 20
        }
    
    def _generate_peer_comparison(self, params):
        """Generate peer comparison data"""
        score = float(params.get('score', 0))
        
        return {
            "percentile_rank": min(95, score + random.uniform(-10, 10)),
            "industry_average_score": 65,
            "top_quartile_threshold": 85,
            "peer_count": random.randint(15, 50),
            "competitive_position": "Above Average" if score > 70 else "Average"
        }
    
    def _generate_projections(self, params):
        """Generate financial projections"""
        value = float(params.get('value', 0))
        base_revenue = value or random.uniform(1000000, 10000000)
        
        return {
            "revenue_projections": [
                {"year": 2025, "revenue": base_revenue * 1.0, "growth": 0},
                {"year": 2026, "revenue": base_revenue * 1.15, "growth": 15},
                {"year": 2027, "revenue": base_revenue * 1.35, "growth": 17},
                {"year": 2028, "revenue": base_revenue * 1.60, "growth": 19},
                {"year": 2029, "revenue": base_revenue * 1.90, "growth": 19}
            ],
            "ebitda_margin_progression": [18, 20, 22, 24, 26],
            "irr_estimate": random.uniform(22, 35)
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
    
    def _get_industry_growth_rate(self, naics):
        """Get industry growth rate"""
        growth_rates = {
            '23': 4.2, '31': 2.8, '32': 2.5, '33': 3.1,
            '42': 3.5, '44': 2.9, '45': 3.2,
            '48': 4.1, '49': 3.8, '51': 6.5,
            '52': 4.8, '53': 3.9, '54': 5.2,
            '56': 4.5, '61': 3.2, '62': 5.8,
            '71': 3.5, '72': 4.2, '81': 3.1, '92': 2.1
        }
        
        if naics and len(naics) >= 2:
            return growth_rates.get(naics[:2], 3.5)
        return 3.5
    
    def _generate_enhanced_simulated_insights(self, params):
        """Generate enhanced simulated insights"""
        # [Previous simulated insights code with additions]
        base_insights = self._generate_base_insights(params)
        
        # Add enhanced features
        base_insights['analytics'] = self._generate_analytics(params)
        base_insights['peer_comparison'] = self._generate_peer_comparison(params)
        base_insights['financial_projections'] = self._generate_projections(params)
        
        # Add valuation
        score = float(params.get('score', 0))
        value = float(params.get('value', 0))
        base_val = value * 5 if value > 0 else random.uniform(2000000, 10000000)
        
        base_insights['valuation_range'] = {
            "low": base_val * 0.8,
            "high": base_val * 1.2,
            "methodology": "5x Revenue Multiple"
        }
        
        # Add exit strategies
        base_insights['exit_strategies'] = [
            {"strategy": "Strategic Sale", "timeline": "3-5 years", "multiple": "2.5x"},
            {"strategy": "PE Rollup", "timeline": "2-3 years", "multiple": "2.0x"},
            {"strategy": "Management Buyout", "timeline": "4-5 years", "multiple": "1.8x"}
        ]
        
        # Add value creation plan
        base_insights['value_creation_plan'] = [
            "Implement enterprise sales process",
            "Expand federal contract portfolio",
            "Digital transformation initiative",
            "Geographic expansion to adjacent states",
            "Operational efficiency improvements"
        ]
        
        return base_insights
    
    def _generate_base_insights(self, params):
        """Generate base insights structure"""
        score = float(params.get('score', 0))
        grade = params.get('grade', 'N/A')
        contracts = int(params.get('contracts', 0))
        value = float(params.get('value', 0))
        patents = int(params.get('patents', 0))
        nsf = float(params.get('nsf', 0))
        naics = params.get('naics', 'N/A')
        state = params.get('state', 'N/A')
        name = params.get('name', 'Unknown Company')
        
        # Determine recommendation
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
        
        # Industry context
        industry_desc = self._get_industry_description(naics)
        market_density = self._calculate_market_density(state, naics)
        
        return {
            "recommendation": recommendation,
            "investment_score": investment_score,
            "key_strengths": self._generate_strengths(params),
            "growth_opportunities": self._generate_opportunities(params),
            "risk_factors": self._generate_risks(params),
            "market_position": f"{'Strong' if score >= 70 else 'Moderate'} position in {industry_desc} with {market_density.lower()}",
            "competitive_advantages": self._generate_advantages(params),
            "action_items": self._generate_action_items(params),
            "financial_health": f"Grade {grade} indicates {'strong' if grade in ['A', 'B'] else 'moderate'} financial health.",
            "innovation_score": min(100, (patents * 10) + (nsf / 100000)),
            "esg_considerations": self._generate_esg(params),
            "synergies": self._generate_synergies(params),
            "operational_improvements": self._generate_improvements(params),
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_strengths(self, params):
        """Generate company strengths"""
        strengths = []
        
        if int(params.get('contracts', 0)) > 0:
            strengths.append(f"Established federal contractor with proven track record")
        if float(params.get('score', 0)) >= 80:
            strengths.append("Exceptional PE investment score indicating strong fundamentals")
        if params.get('grade') in ['A', 'B']:
            strengths.append(f"Strong financial health with {params.get('grade')} grade rating")
        if int(params.get('patents', 0)) > 0:
            strengths.append(f"Innovation capability with {params.get('patents')} patents")
        
        # Ensure minimum strengths
        while len(strengths) < 3:
            strengths.append("Strategic market positioning")
        
        return strengths[:5]
    
    def _generate_opportunities(self, params):
        """Generate growth opportunities"""
        opportunities = [
            "Geographic expansion to adjacent markets",
            "Digital transformation to improve operational efficiency",
            "Strategic acquisitions to gain market share",
            "Expand service offerings to existing customers"
        ]
        
        if int(params.get('contracts', 0)) < 5:
            opportunities.insert(0, "Significant federal contracting growth potential")
        if int(params.get('patents', 0)) == 0:
            opportunities.append("Develop intellectual property portfolio")
            
        return opportunities[:5]
    
    def _generate_risks(self, params):
        """Generate risk factors"""
        risks = []
        
        if params.get('grade') in ['C', 'D', 'F']:
            risks.append(f"Financial health concerns with {params.get('grade')} grade")
        if int(params.get('contracts', 0)) < 3:
            risks.append("Limited revenue diversification")
        
        risks.extend([
            "Market competition from larger players",
            "Economic downturn sensitivity",
            "Key personnel dependency"
        ])
        
        return risks[:5]
    
    def _generate_advantages(self, params):
        """Generate competitive advantages"""
        return [
            f"Specialized expertise in {self._get_industry_description(params.get('naics', ''))}",
            f"Strategic location in {params.get('state', 'region')}",
            "Established customer relationships",
            "Proven operational capabilities"
        ][:3]
    
    def _generate_action_items(self, params):
        """Generate due diligence action items"""
        return [
            "Conduct management team assessment and interviews",
            "Review 3-year financial statements and projections",
            "Analyze customer contracts and concentration",
            "Evaluate technology infrastructure and IP portfolio",
            "Assess market position and competitive landscape",
            "Review legal and regulatory compliance"
        ][:6]
    
    def _generate_esg(self, params):
        """Generate ESG considerations"""
        industry = self._get_industry_description(params.get('naics', ''))
        return [
            f"Environmental compliance in {industry} sector",
            "Workforce diversity and inclusion practices",
            "Corporate governance structure assessment",
            "Community impact and local employment"
        ][:3]
    
    def _generate_synergies(self, params):
        """Generate synergy opportunities"""
        return [
            "Cross-selling opportunities with portfolio companies",
            "Shared services and back-office consolidation",
            "Joint procurement and vendor negotiations",
            "Technology platform sharing"
        ][:2]
    
    def _generate_improvements(self, params):
        """Generate operational improvements"""
        return [
            "Implement lean manufacturing/service delivery",
            "Upgrade technology systems and automation",
            "Optimize supply chain and procurement",
            "Enhance sales and marketing processes",
            "Improve financial reporting and controls"
        ][:3]

# Initialize the generator
generator = EnhancedInsightsGenerator()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Enhanced AI Insights API',
        'openai_available': generator.openai_available,
        'version': '2.0'
    })

@app.route('/api/insights/<uei>', methods=['GET'])
def get_insights(uei):
    """Generate enhanced AI insights for a company"""
    try:
        # Get parameters from query string
        params = {
            'uei': uei,
            'name': request.args.get('name', 'Unknown'),
            'score': request.args.get('score', 0),
            'grade': request.args.get('grade', 'N/A'),
            'contracts': request
	'contracts': request.args.get('contracts', 0),
           'value': request.args.get('value', 0),
           'city': request.args.get('city', 'N/A'),
           'state': request.args.get('state', 'N/A'),
           'naics': request.args.get('naics', 'N/A'),
           'patents': request.args.get('patents', 0),
           'nsf': request.args.get('nsf', 0)
       }
       
       # Generate enhanced insights
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

@app.route('/api/market-analysis/<naics>', methods=['GET'])
def get_market_analysis(naics):
   """Get market analysis for a specific NAICS code"""
   try:
       analysis = {
           'industry': generator._get_industry_description(naics),
           'growth_rate': generator._get_industry_growth_rate(naics),
           'market_size': random.uniform(10, 100) * 1000000000,  # billions
           'key_trends': [
               "Digital transformation driving efficiency",
               "Consolidation among mid-market players",
               "Increasing focus on sustainability"
           ],
           'competitive_landscape': {
               'fragmentation': 'High' if naics[:2] in ['23', '54', '81'] else 'Medium',
               'barriers_to_entry': 'Medium',
               'margin_trends': 'Improving'
           }
       }
       
       return jsonify({
           'success': True,
           'data': analysis
       })
       
   except Exception as e:
       return jsonify({
           'success': False,
           'error': str(e)
       }), 500

@app.route('/api/portfolio-analysis', methods=['POST'])
def analyze_portfolio():
   """Analyze a portfolio of companies"""
   try:
       companies = request.json.get('companies', [])
       
       if not companies:
           return jsonify({'error': 'No companies provided'}), 400
       
       # Calculate portfolio metrics
       total_value = sum(float(c.get('federal_contracts_value', 0)) for c in companies)
       avg_score = sum(float(c.get('pe_investment_score', 0)) for c in companies) / len(companies)
       
       # Industry diversification
       industries = {}
       for company in companies:
           ind = generator._get_industry_description(company.get('primary_naics', ''))
           industries[ind] = industries.get(ind, 0) + 1
       
       # Geographic distribution
       states = {}
       for company in companies:
           state = company.get('state', 'Unknown')
           states[state] = states.get(state, 0) + 1
       
       analysis = {
           'portfolio_metrics': {
               'total_companies': len(companies),
               'total_contract_value': total_value,
               'average_pe_score': avg_score,
               'portfolio_health': 'Strong' if avg_score >= 70 else 'Moderate'
           },
           'diversification': {
               'industry_concentration': max(industries.values()) / len(companies) * 100 if companies else 0,
               'geographic_concentration': max(states.values()) / len(companies) * 100 if companies else 0,
               'industries': industries,
               'states': states
           },
           'recommendations': [
               "Consider geographic expansion to reduce concentration risk",
               "Look for synergies between portfolio companies",
               "Identify cross-selling opportunities"
           ]
       }
       
       return jsonify({
           'success': True,
           'data': analysis
       })
       
   except Exception as e:
       return jsonify({
           'success': False,
           'error': str(e)
       }), 500

if __name__ == '__main__':
   print("Starting Enhanced AI Insights API on port 5001...")
   print(f"OpenAI Available: {generator.openai_available}")
   print("New endpoints:")
   print("  - /api/insights/<uei> - Company insights")
   print("  - /api/market-analysis/<naics> - Market analysis")
   print("  - /api/portfolio-analysis - Portfolio analysis")
   app.run(host='0.0.0.0', port=5001, debug=False)
