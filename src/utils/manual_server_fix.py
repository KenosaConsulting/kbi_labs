
#!/usr/bin/env python3
"""
Manually fix the server to load companies from JSON
"""

import os

def create_working_server():
    """Create a simple working server that loads from companies.json"""
    
    server_code = '''#!/usr/bin/env python3
"""
KBI Labs Combined Server v2 - Fixed
"""

from flask import Flask, render_template, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import json
import os
import requests
import io
import csv

app = Flask(__name__, 
    static_folder='kbi_dashboard',
    template_folder='kbi_dashboard')
CORS(app)

# Configuration
COMPANIES_FILE = 'companies.json'
AI_INSIGHTS_URL = 'http://localhost:5001'

def load_companies():
    """Load companies from JSON file"""
    try:
        with open(COMPANIES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading companies: {e}")
        return []

# Routes
@app.route('/')
def index():
    return send_from_directory('kbi_dashboard', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('kbi_dashboard', path)

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "service": "KBI Labs API"})

@app.route('/api/companies', methods=['GET'])
def api_companies():
    """Get all companies"""
    companies = load_companies()
    return jsonify(companies)

@app.route('/api/companies/<uei>')
def get_company(uei):
    """Get specific company by UEI"""
    companies = load_companies()
    company = next((c for c in companies if c.get('uei') == uei), None)
    if company:
        return jsonify(company)
    return jsonify({"error": "Company not found"}), 404

@app.route('/api/companies/<uei>/insights', methods=['POST'])
def get_company_insights(uei):
    """Get AI insights for a company"""
    try:
        # Get company data
        companies = load_companies()
        company = next((c for c in companies if c.get('uei') == uei), None)
        
        if not company:
            return jsonify({"error": "Company not found"}), 404
        
        # Call AI insights service
        response = requests.post(
            f"{AI_INSIGHTS_URL}/api/insights/company",
            json=company,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "AI service error"}), 500
            
    except Exception as e:
        print(f"Error getting insights: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/summary')
def portfolio_summary():
    """Get portfolio summary statistics"""
    companies = load_companies()
    
    if not companies:
        return jsonify({"error": "No companies loaded"}), 404
    
    total_value = sum(c.get('federal_contracts_value', 0) for c in companies)
    avg_score = sum(c.get('pe_investment_score', 0) for c in companies) / len(companies) if companies else 0
    
    # Industry breakdown
    industries = {}
    for c in companies:
        naics = str(c.get('primary_naics', 'Unknown'))[:2]
        industries[naics] = industries.get(naics, 0) + 1
    
    # State breakdown  
    states = {}
    for c in companies:
        state = c.get('state', 'Unknown')
        states[state] = states.get(state, 0) + 1
    
    return jsonify({
        "total_companies": len(companies),
        "total_contract_value": total_value,
        "average_pe_score": round(avg_score, 1),
        "top_performers": len([c for c in companies if c.get('pe_investment_score', 0) >= 80]),
        "industry_breakdown": industries,
        "geographic_breakdown": states,
        "portfolio_health": "Strong" if avg_score >= 80 else "Good" if avg_score >= 70 else "Fair"
    })

if __name__ == '__main__':
    print(f"Starting KBI Labs Server...")
    print(f"Loading companies from: {COMPANIES_FILE}")
    
    # Test load
    companies = load_companies()
    print(f"Loaded {len(companies)} companies")
    if companies:
        print(f"First company: {companies[0].get('company_name', 'Unknown')}")
    
    # Start server
    app.run(host='0.0.0.0', port=8090, debug=False)
'''
    
    # Write the fixed server
    with open('combined_server_v2_fixed.py', 'w') as f:
        f.write(server_code)
    
    print("✅ Created combined_server_v2_fixed.py")
    
    # Make it executable
    os.chmod('combined_server_v2_fixed.py', 0o755)
    
    print("\n🚀 To use the fixed server:")
    print("   1. pkill -f combined_server")
    print("   2. python3 combined_server_v2_fixed.py &")
    print("\n   Or replace the original:")
    print("   mv combined_server_v2.py combined_server_v2_broken.py")
    print("   mv combined_server_v2_fixed.py combined_server_v2.py")
    print("   python3 combined_server_v2.py &")

if __name__ == "__main__":
    create_working_server()
