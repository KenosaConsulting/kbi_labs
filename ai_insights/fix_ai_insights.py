#!/usr/bin/env python3
import re

# Read the current file
with open('ai_insights_api.py', 'r') as f:
    content = f.read()

# Find the prepare_context method and properly replace it
# First, let's find where it starts
start_pattern = r'(\s*)def _prepare_context\(self[^:]*\):'
match = re.search(start_pattern, content)

if match:
    indent = match.group(1)  # Capture the indentation
    
    # Create properly indented new method
    new_method = f'''{indent}def _prepare_context(self, params):
{indent}    """Prepare enhanced context for GPT-4 with industry-specific analysis"""
{indent}    # Extract company metrics
{indent}    score = float(params.get('score', 0))
{indent}    grade = params.get('grade', 'N/A')
{indent}    contracts = int(params.get('contracts', 0))
{indent}    value = float(params.get('value', 0))
{indent}    patents = int(params.get('patents', 0))
{indent}    nsf = float(params.get('nsf', 0))
{indent}    
{indent}    # Calculate derived metrics
{indent}    avg_contract = value / contracts if contracts > 0 else 0
{indent}    innovation_index = (patents * 10) + (nsf / 100000) if patents or nsf else 0
{indent}    
{indent}    # Get industry context
{indent}    naics = params.get('naics', 'N/A')
{indent}    industry_desc = self._get_industry_description(naics)
{indent}    market_density = self._calculate_market_density(params.get('state', 'N/A'), naics)
{indent}    
{indent}    context = f"""
{indent}    Analyze this company as a Private Equity investment opportunity:
{indent}    
{indent}    Company: {{params.get('name', 'Unknown')}}
{indent}    Location: {{params.get('city', 'N/A')}}, {{params.get('state', 'N/A')}}
{indent}    
{indent}    Key Metrics:
{indent}    - PE Investment Score: {{score}}/100
{indent}    - Business Health Grade: {{grade}}
{indent}    - Federal Contracts: {{contracts}} (Total Value: ${{value:,.2f}})
{indent}    - Average Contract Size: ${{avg_contract:,.2f}}
{indent}    - Patents: {{patents}}
{indent}    - NSF Funding: ${{nsf:,.2f}}
{indent}    - Industry: {{industry_desc}} (NAICS: {{naics}})
{indent}    - Innovation Index: {{innovation_index:.1f}}
{indent}    - Market Density: {{market_density}}
{indent}    
{indent}    Provide a comprehensive investment analysis including:
{indent}    
{indent}    1. Investment recommendation: Must be one of [Strong Buy, Buy, Hold, Sell] with specific justification
{indent}    2. Key strengths: 3-5 specific competitive advantages based on the metrics
{indent}    3. Growth opportunities: 3-5 concrete, actionable growth strategies specific to their industry
{indent}    4. Risk factors: 3-5 specific risks based on their metrics and industry
{indent}    5. Market position: Assess their position relative to industry standards
{indent}    6. Competitive advantages: What makes them unique in their market
{indent}    7. Action items: 4-6 specific due diligence items for investors
{indent}    8. Financial health: Assessment based on their grade and score
{indent}    9. Innovation score: 0-100 based on patents and R&D funding
{indent}    10. ESG considerations: Environmental, social, governance factors relevant to their industry
{indent}    
{indent}    For {{industry_desc}}, consider industry-specific factors:
{indent}    - Regulatory environment and compliance requirements
{indent}    - Technology adoption and innovation needs  
{indent}    - Market consolidation opportunities
{indent}    - Geographic expansion potential
{indent}    - Seasonal or cyclical factors
{indent}    
{indent}    Be specific and avoid generic statements. Reference their actual metrics in your analysis.
{indent}    
{indent}    Format your response as a JSON object with these exact keys:
{indent}    {{{{
{indent}        "recommendation": "Buy",
{indent}        "investment_score": 85,
{indent}        "key_strengths": ["strength1", "strength2", ...],
{indent}        "growth_opportunities": ["opportunity1", "opportunity2", ...],
{indent}        "risk_factors": ["risk1", "risk2", ...],
{indent}        "market_position": "Detailed position assessment",
{indent}        "competitive_advantages": ["advantage1", "advantage2", ...],
{indent}        "action_items": ["action1", "action2", ...],
{indent}        "financial_health": "Detailed health assessment",
{indent}        "innovation_score": 75,
{indent}        "esg_considerations": ["consideration1", "consideration2", ...]
{indent}    }}}}
{indent}    """
{indent}    
{indent}    return context

{indent}def _get_industry_description(self, naics):
{indent}    """Get human-readable industry description from NAICS code"""
{indent}    naics_map = {{
{indent}        '23': 'Construction',
{indent}        '31': 'Manufacturing',
{indent}        '32': 'Manufacturing',
{indent}        '33': 'Manufacturing',
{indent}        '42': 'Wholesale Trade',
{indent}        '44': 'Retail Trade',
{indent}        '48': 'Transportation',
{indent}        '51': 'Information Technology',
{indent}        '52': 'Finance and Insurance',
{indent}        '53': 'Real Estate',
{indent}        '54': 'Professional Services',
{indent}        '56': 'Administrative Services',
{indent}        '61': 'Educational Services',
{indent}        '62': 'Healthcare',
{indent}        '71': 'Arts and Entertainment',
{indent}        '72': 'Accommodation and Food Services',
{indent}        '81': 'Other Services',
{indent}        '92': 'Public Administration'
{indent}    }}
{indent}    
{indent}    if naics and len(naics) >= 2:
{indent}        prefix = naics[:2]
{indent}        return naics_map.get(prefix, 'General Business')
{indent}    return 'General Business'

{indent}def _calculate_market_density(self, state, naics):
{indent}    """Calculate market density for the state/industry combination"""
{indent}    # Simplified calculation - in production would use real data
{indent}    high_density_states = ['CA', 'NY', 'TX', 'FL', 'IL']
{indent}    high_density_industries = ['51', '52', '54']
{indent}    
{indent}    if state in high_density_states and naics[:2] in high_density_industries:
{indent}        return 'High Competition'
{indent}    elif state in high_density_states or naics[:2] in high_density_industries:
{indent}        return 'Moderate Competition'
{indent}    else:
{indent}        return 'Low Competition'
'''
    
    # Find the end of the current _prepare_context method
    # Look for the next method definition at the same indentation level
    current_method_pattern = rf'{indent}def _prepare_context\(self[^:]*\):.*?(?={indent}def\s|\Z)'
    
    # Replace the old method with the new one
    new_content = re.sub(current_method_pattern, new_method, content, flags=re.DOTALL)
    
    # Write the updated content
    with open('ai_insights_api.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Successfully fixed AI insights API!")
else:
    print("❌ Could not find _prepare_context method")
