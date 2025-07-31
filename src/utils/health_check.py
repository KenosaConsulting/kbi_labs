#!/usr/bin/env python3
"""
KBI Labs Platform Health Check
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8090"
AI_URL = "http://localhost:8095"

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
    
    # Check AI service
    try:
        response = requests.get(f"{AI_URL}/api/health", timeout=5)
        print("✅ AI Insights: Online")
    except:
        print("⚠️  AI Insights: Not responding (may be on different port)")
    
    print()
    print("📊 DATA STATUS:")
    
    # Check database
    try:
        import sqlite3
        conn = sqlite3.connect('kbi_complete_enriched.db')
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM enriched_companies_full").fetchone()[0]
        print(f"✅ Enriched Database: {count:,} companies")
        conn.close()
    except Exception as e:
        print(f"❌ Database Error: {e}")
    
    print()
    print("💡 QUICK FIXES:")
    print("1. Start services: python3 combined_server_v2.py")
    print("2. Load companies: python3 load_companies_fixed.py")
    print("3. Check logs: tail -f *.log")

if __name__ == "__main__":
    main()
