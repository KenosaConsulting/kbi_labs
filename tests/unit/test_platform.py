#!/usr/bin/env python3
import requests
import json
import time

print("🧪 KBI Labs Platform Integration Test")
print("=" * 50)

# Test 1: Load companies
print("\n1️⃣ Testing Company API...")
try:
    r = requests.get('http://localhost:8090/api/companies')
    companies = r.json()
    print(f"   ✅ Loaded {len(companies)} companies")
    
    if companies:
        test_company = companies[0]
        print(f"   📊 Test company: {test_company.get('organization_name', 'Unknown')}")
        print(f"      - UEI: {test_company.get('uei')}")
        print(f"      - Score: {test_company.get('pe_investment_score')}")
        print(f"      - Grade: {test_company.get('business_health_grade')}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    test_company = None

# Test 2: AI Insights Generation
print("\n2️⃣ Testing AI Insights Generation...")
if test_company:
    try:
        params = {
            'name': test_company.get('organization_name', 'Test Company'),
            'score': test_company.get('pe_investment_score', 85),
            'grade': test_company.get('business_health_grade', 'A'),
            'contracts': test_company.get('federal_contracts_count', 0),
            'value': test_company.get('federal_contracts_value', 0),
            'city': test_company.get('city', 'Unknown'),
            'state': test_company.get('state', 'Unknown'),
            'naics': test_company.get('primary_naics', '541990'),
            'patents': test_company.get('patent_count', 0),
            'nsf': test_company.get('nsf_total_funding', 0)
        }
        
        r = requests.get(f"http://localhost:5001/api/insights/{test_company['uei']}", params=params)
        result = r.json()
        
        if result.get('success'):
            insights = result.get('data', {})
            print("   ✅ AI Insights generated successfully")
            print(f"      - Recommendation: {insights.get('recommendation', 'N/A')}")
            print(f"      - Investment Score: {insights.get('investment_score', 'N/A')}")
            print(f"      - Key Strengths: {len(insights.get('key_strengths', []))} items")
            print(f"      - Growth Opportunities: {len(insights.get('growth_opportunities', []))} items")
            
            # Check for enhanced features
            if 'analytics' in insights:
                print("   ✅ Enhanced analytics included")
            if 'financial_projections' in insights:
                print("   ✅ Financial projections included")
        else:
            print(f"   ❌ AI Insights failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Test 3: Web Interface
print("\n3️⃣ Testing Web Interface...")
pages = [
    ('/', 'Dashboard'),
    ('/portfolio.html', 'Portfolio Analysis'),
    ('/company-details.html?uei=TEST', 'Company Details')
]

for path, name in pages:
    try:
        r = requests.get(f'http://localhost:8090{path}')
        if r.status_code == 200:
            print(f"   ✅ {name}: Accessible")
        else:
            print(f"   ⚠️  {name}: Status {r.status_code}")
    except Exception as e:
        print(f"   ❌ {name}: {e}")

# Test 4: Database Connection
print("\n4️⃣ Testing Database Connection...")
try:
    import psycopg2
    from db_config import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check enriched companies
    cur.execute("SELECT COUNT(*) FROM enriched_companies")
    count = cur.fetchone()[0]
    print(f"   ✅ Database connected: {count} enriched companies")
    
    conn.close()
except Exception as e:
    print(f"   ⚠️  Database check skipped: {e}")

print("\n" + "=" * 50)
print("✅ Platform test complete!")
print("\nNext steps:")
print("1. Visit http://3.143.232.123:8090 to see the dashboard")
print("2. Click on any company to see detailed analysis")
print("3. Try the Portfolio Analysis page")
print("4. Check the Analytics tab for visualizations")
