#!/usr/bin/env python3
import re

# Read the current file
with open('ai_insights_api.py', 'r') as f:
    content = f.read()

# Create the new enhanced context method
new_context = '''    def _prepare_context(self, params):
        """Prepare enhanced context for GPT-4 with industry-specific analysis"""
        # Extract company metrics
        score = float(params.get('score', 0))
        grade = params.get('grade', 'N/A')
        contracts = int(params.get('contracts', 0))
        value = float(params.get('value', 0))
        patents = int(params.get('patents', 0))
        nsf = float(params.get('nsf', 0))
        
        # Calculate derived metrics
        avg_contract = value / contracts if contracts > 0 else 0
        innovation_index = (patents * 10) + (nsf / 100000) if patents or nsf else 0
        
        # Get industry context
        naics = params.get('naics', 'N/A')
        industry_desc = self._get_industry_description(naics)
        market_density = self._calculate_market_density(params.get('state', 'N/A'), naics)
        
        context = f"""
        Analyze this company as a Private Equity investment opportunity:
        
        Company: {params.get('name', 'Unknown')}
        Location: {params.get('city', 'N/A')}, {params.get('state', 'N/A')}
        
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
        
        Provide a comprehensive investment analysis including:
        
        1. Investment recommendation: Must be one of [Strong Buy, Buy, Hold, Sell] with specific justification
        2. Key strengths: 3-5 specific competitive advantages based on the metrics
        3. Growth opportunities: 3-5 concrete, actionable growth strategies specific to their industry
        4. Risk factors: 3-5 specific risks based on their metrics and industry
        5. Market position: Assess their position relative to industry standards
        6. Competitive advantages: What makes them unique in their market
        7. Action items: 4-6 specific due diligence items for investors
        8. Financial health: Assessment based on their grade and score
        9. Innovation score: 0-100 based on patents and R&D funding
        10. ESG considerations: Environmental, social, governance factors relevant to their industry
        
        For {industry_desc}, consider industry-specific factors:
        - Regulatory environment and compliance requirements
        - Technology adoption and innovation needs  
        - Market consolidation opportunities
        - Geographic expansion potential
        - Seasonal or cyclical factors
        
        Be specific and avoid generic statements. Reference their actual metrics in your analysis.
        
        Format your response as a JSON object with these exact keys:
        {{
            "recommendation": "Buy",
            "investment_score": 85,
            "key_strengths": ["strength1", "strength2", ...],
            "growth_opportunities": ["opportunity1", "opportunity2", ...],
            "risk_factors": ["risk1", "risk2", ...],
            "market_position": "Detailed position assessment",
            "competitive_advantages": ["advantage1", "advantage2", ...],
            "action_items": ["action1", "action2", ...],
            "financial_health": "Detailed health assessment",
            "innovation_score": 75,
            "esg_considerations": ["consideration1", "consideration2", ...]
        }}
        """
        
        return context
    
    def _get_industry_description(self, naics):
        """Get human-readable industry description from NAICS code"""
        naics_map = {
            '23': 'Construction',
            '31': 'Manufacturing',
            '32': 'Manufacturing',
            '33': 'Manufacturing',
            '42': 'Wholesale Trade',
            '44': 'Retail Trade',
            '48': 'Transportation',
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
        # Simplified calculation - in production would use real data
        high_density_states = ['CA', 'NY', 'TX', 'FL', 'IL']
        high_density_industries = ['51', '52', '54']
        
        if state in high_density_states and naics[:2] in high_density_industries:
            return 'High Competition'
        elif state in high_density_states or naics[:2] in high_density_industries:
            return 'Moderate Competition'
        else:
            return 'Low Competition'
'''

# Find and replace the _prepare_context method
pattern = r'def _prepare_context\(self.*?\n(?=\s{0,4}def\s|\s{0,4}async\s+def\s|\Z)'
new_content = re.sub(pattern, new_context + '\n', content, flags=re.DOTALL)

# Write the updated content
with open('ai_insights_api.py', 'w') as f:
    f.write(new_content)

print("✅ AI Insights context successfully updated!")
print("✅ Added industry-specific analysis")
print("✅ Added market density calculation")
print("✅ Enhanced investment metrics")
