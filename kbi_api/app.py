#!/usr/bin/env python3
from flask import Flask, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Sample company data
companies = [
    {
        "uei": "RKGUUXN56911",
        "organization_name": "CARDINAL REGENT CONSULTING LLC",
        "city": "WEST RIVER",
        "state": "Maryland",
        "primary_naics": "541990.0",
        "pe_investment_score": 100.0,
        "business_health_grade": "A",
        "federal_contracts_count": 0,
        "federal_contracts_value": 0,
        "patent_count": 0,
        "nsf_total_funding": 0,
        "sam_registration_status": "Active",
        "cage_code": "N/A",
        "phone_number": "8039603139.0",
        "email": "N/A",
        "website": "www.cardinalregent.com",
        "state_gdp_billions": 400,
        "state_population": 6000000
    },
    {
        "uei": "PWKZEN548648",
        "organization_name": "SOUTH JERSEY HEAT AND COOL LLC",
        "city": "VINELAND",
        "state": "New Jersey",
        "primary_naics": "238220",
        "pe_investment_score": 100.0,
        "business_health_grade": "A",
        "federal_contracts_count": 2,
        "federal_contracts_value": 250000,
        "patent_count": 1,
        "nsf_total_funding": 50000,
        "sam_registration_status": "Active",
        "cage_code": "ABC123",
        "phone_number": "856-555-0100",
        "email": "info@sjheatcool.com",
        "website": "www.sjheatcool.com",
        "state_gdp_billions": 650,
        "state_population": 9200000
    },
    {
        "uei": "CTIENVINC123",
        "organization_name": "CTI ENVIRONMENTAL INC",
        "city": "SAN FRANCISCO",
        "state": "California",
        "primary_naics": "541620",
        "pe_investment_score": 100.0,
        "business_health_grade": "A",
        "federal_contracts_count": 5,
        "federal_contracts_value": 1500000,
        "patent_count": 3,
        "nsf_total_funding": 200000,
        "sam_registration_status": "Active",
        "cage_code": "CTI456",
        "phone_number": "415-555-0200",
        "email": "contact@ctienvironmental.com",
        "website": "www.ctienvironmental.com",
        "state_gdp_billions": 3500,
        "state_population": 39500000
    },
    {
        "uei": "MUNROENT789",
        "organization_name": "MUNRO ENTERPRISES LLC",
        "city": "DETROIT",
        "state": "Michigan",
        "primary_naics": "336111",
        "pe_investment_score": 100.0,
        "business_health_grade": "A",
        "federal_contracts_count": 8,
        "federal_contracts_value": 3200000,
        "patent_count": 12,
        "nsf_total_funding": 500000,
        "sam_registration_status": "Active",
        "cage_code": "MUN789",
        "phone_number": "313-555-0300",
        "email": "info@munroenterprises.com",
        "website": "www.munroenterprises.com",
        "state_gdp_billions": 540,
        "state_population": 10000000
    }
]

@app.route('/api/companies', methods=['GET'])
def get_companies():
    """Get all companies"""
    return jsonify(companies)

@app.route('/api/companies/<uei>', methods=['GET'])
def get_company(uei):
    """Get a specific company by UEI"""
    company = next((c for c in companies if c['uei'] == uei), None)
    if company:
        return jsonify(company)
    return jsonify({'error': 'Company not found'}), 404

@app.route('/api/states', methods=['GET'])
def get_states():
    """Get unique states"""
    states = list(set(c['state'] for c in companies))
    return jsonify(sorted(states))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
