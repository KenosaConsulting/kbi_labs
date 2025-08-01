# Read the current server file
with open('combined_server_v2.py', 'r') as f:
    content = f.read()

# Check if portfolio summary endpoint exists
if '/api/portfolio/summary' not in content:
    # Add it before the last if __name__ line
    endpoint_code = '''
@app.route('/api/portfolio/summary')
def portfolio_summary():
    """Get portfolio summary statistics"""
    companies = load_companies()
    
    if not companies:
        return jsonify({"total_companies": 0, "total_contract_value": 0, "average_pe_score": 0})
    
    total_value = sum(c.get('federal_contracts_value', 0) for c in companies)
    avg_score = sum(c.get('pe_investment_score', 0) for c in companies) / len(companies) if companies else 0
    
    # Industry breakdown
    industries = {}
    for c in companies:
        naics = str(c.get('primary_naics', 'Unknown'))[:2]
        industries[naics] = industries.get(naics, 0) + 1
    
    return jsonify({
        "total_companies": len(companies),
        "total_contract_value": total_value,
        "average_pe_score": round(avg_score, 1),
        "industry_breakdown": industries,
        "portfolio_health": "Strong" if avg_score >= 80 else "Good" if avg_score >= 70 else "Fair"
    })
'''
    
    # Insert before main
    content = content.replace("if __name__ == '__main__':", endpoint_code + "\nif __name__ == '__main__':")
    
    with open('combined_server_v2_with_portfolio.py', 'w') as f:
        f.write(content)
    
    print("✅ Added portfolio summary endpoint")
    print("Restart server with: pkill -f combined_server && python3 combined_server_v2_with_portfolio.py &")
