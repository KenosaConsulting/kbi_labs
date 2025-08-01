
#!/usr/bin/env python3
"""
KBI Labs Platform Health Check - Updated
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8090"
AI_URL = "http://localhost:5001"  # Correct port!

def main():
    print("🔍 KBI Labs Platform Health Check")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check main service
    print("📡 SERVICE STATUS:")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Main Dashboard: Online")
        else:
            print(f"⚠️  Main Dashboard: Status {response.status_code}")
    except:
        print("❌ Main Dashboard: Not responding")
    
    # Check API
    try:
        response = requests.get(f"{BASE_URL}/api/companies", timeout=5)
        if response.status_code == 200:
            companies = response.json()
            print(f"✅ API: Online ({len(companies)} companies loaded)")
        else:
            print(f"⚠️  API: Status {response.status_code}")
    except:
        print("❌ API: Not responding")
    
    # Check AI service on correct port
    try:
        response = requests.get(f"{AI_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ AI Insights: Online (port 5001)")
        else:
            print(f"⚠️  AI Insights: Status {response.status_code}")
    except:
        print("⚠️  AI Insights: Not responding on port 5001")
    
    print()
    print("📊 DATA STATUS:")
    
    # Check database
    try:
        import sqlite3
        conn = sqlite3.connect('kbi_complete_enriched.db')
        cursor = conn.cursor()
        
        # Total companies
        count = cursor.execute("SELECT COUNT(*) FROM enriched_companies_full").fetchone()[0]
        print(f"✅ Total companies in database: {count:,}")
        
        # Companies with good scores
        good_count = cursor.execute("SELECT COUNT(*) FROM enriched_companies_full WHERE pe_investment_score >= 80").fetchone()[0]
        print(f"✅ High-scoring companies (80+): {good_count:,}")
        
        # Companies with patents
        patent_count = cursor.execute("SELECT COUNT(*) FROM enriched_companies_full WHERE patent_count > 0").fetchone()[0]
        print(f"✅ Companies with patents: {patent_count:,}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Database Error: {e}")
    
    print()
    print("🚀 QUICK ACTIONS:")
    print("1. Load more companies: python3 load_companies_final.py")
    print("2. View dashboard: http://3.143.232.123:8090")
    print("3. Check AI insights: Click any company → AI Insights tab")
    print()
    print("💡 Platform is ready for use!")

if __name__ == "__main__":
    main()
