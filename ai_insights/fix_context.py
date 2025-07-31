# Read the file
with open('ai_insights_api.py', 'r') as f:
    lines = f.readlines()

# Find the _prepare_context method
in_method = False
method_start = -1
method_end = -1

for i, line in enumerate(lines):
    if 'def _prepare_context(self, company_data: Dict[str, Any]) -> str:' in line:
        method_start = i
        in_method = True
    elif in_method and line.strip() and not line.startswith('        ') and not line.startswith('    def'):
        method_end = i
        break

# If we found the method, replace it
if method_start >= 0:
    # Create the new method with proper indentation
    new_method = '''    def _prepare_context(self, company_data: Dict[str, Any]) -> str:
        """Prepare context for GPT-4 analysis"""
        
        # Get NAICS industry description
        naics_code = company_data.get('primary_naics', 'N/A')
        industry_map = {
            '238220': 'Plumbing, Heating, and Air-Conditioning Contractors',
            '541990': 'Professional, Scientific, and Technical Services',
            '541620': 'Environmental Consulting Services',
            '336111': 'Automobile Manufacturing'
        }
        industry_desc = industry_map.get(str(naics_code).split('.')[0], 'General Business')
        
        # Calculate average contract size
        contracts_count = max(company_data.get('federal_contracts_count', 1), 1)
        contracts_value = company_data.get('federal_contracts_value', 0)
        avg_contract_size = contracts_value / contracts_count
        
        return f"""You are a senior private equity analyst evaluating {company_data.get('organization_name', 'Unknown')}.

COMPANY PROFILE:
- Industry: {industry_desc} (NAICS: {naics_code})
- Location: {company_data.get('city', 'N/A')}, {company_data.get('state', 'N/A')}
- PE Investment Score: {company_data.get('pe_investment_score', 'N/A')}/100
- Business Health Grade: {company_data.get('business_health_grade', 'N/A')}

FINANCIAL METRICS:
- Federal Contract Revenue: ${contracts_value:,.2f}
- Number of Contracts: {company_data.get('federal_contracts_count', 0)}
- Average Contract Size: ${avg_contract_size:,.2f}
- Patents: {company_data.get('patent_count', 0)}
- NSF Funding: ${company_data.get('nsf_total_funding', 0):,.2f}

Provide a detailed investment analysis with:
1. Investment recommendation (Strong Buy/Buy/Hold/Sell)
2. Key strengths (3-5 specific points)
3. Growth opportunities (3-5 actionable strategies)
4. Risk factors (3-5 specific risks)
5. Market position assessment
6. Competitive advantages
7. Action items for investors (4-6 specific items)
8. Financial health assessment
9. Innovation score (0-100)
10. ESG considerations

Be specific to the {industry_desc} industry. Format as JSON."""
    
'''

    # Replace the old method
    if method_end < 0:
        method_end = len(lines)
    
    new_lines = lines[:method_start] + [new_method] + lines[method_end:]
    
    # Write the updated file
    with open('ai_insights_api.py', 'w') as f:
        f.writelines(new_lines)
    
    print("Successfully updated _prepare_context method")
else:
    print("Could not find _prepare_context method")
