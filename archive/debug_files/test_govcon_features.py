#!/usr/bin/env python3
"""
Government Contractor Feature Testing Script
Tests the new GovCon dashboard functionality
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8001"  # Adjust based on your API port
FRONTEND_URL = "http://localhost:3000"  # Adjust based on your frontend port

def test_api_endpoints():
    """Test all government contractor API endpoints"""
    print("🧪 Testing Government Contractor API Endpoints")
    print("=" * 50)
    
    endpoints = [
        "/api/v1/government-contractor/",
        "/api/v1/government-contractor/compliance/cmmc",
        "/api/v1/government-contractor/compliance/dfars", 
        "/api/v1/government-contractor/compliance/fedramp",
        "/api/v1/government-contractor/opportunities",
        "/api/v1/government-contractor/performance/cpars",
        "/api/v1/government-contractor/analytics/naics"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            url = f"{API_BASE_URL}{endpoint}"
            print(f"\n📡 Testing: {endpoint}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    "status": "✅ PASS",
                    "response_time": response.elapsed.total_seconds(),
                    "data_keys": list(data.keys()) if isinstance(data, dict) else "Non-dict response"
                }
                print(f"   Status: ✅ PASS ({response.status_code})")
                print(f"   Response Time: {response.elapsed.total_seconds():.3f}s")
            else:
                results[endpoint] = {
                    "status": f"❌ FAIL ({response.status_code})",
                    "error": response.text
                }
                print(f"   Status: ❌ FAIL ({response.status_code})")
                
        except requests.exceptions.RequestException as e:
            results[endpoint] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
            print(f"   Status: ❌ ERROR - {e}")
    
    # Summary
    print("\n📊 API Test Summary")
    print("=" * 30)
    passed = sum(1 for r in results.values() if "PASS" in r["status"])
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All API endpoints working!")
    else:
        print("⚠️  Some endpoints need attention")
    
    return results

def test_frontend_accessibility():
    """Test if the frontend is accessible"""
    print("\n🌐 Testing Frontend Accessibility")
    print("=" * 35)
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            print(f"   URL: {FRONTEND_URL}")
            print(f"   Status: {response.status_code}")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach frontend: {e}")
        return False

def generate_test_report(api_results, frontend_status):
    """Generate a comprehensive test report"""
    print("\n📋 Comprehensive Test Report")
    print("=" * 40)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "api_tests": api_results,
        "frontend_accessible": frontend_status,
        "summary": {
            "total_endpoints": len(api_results),
            "passing_endpoints": sum(1 for r in api_results.values() if "PASS" in r["status"]),
            "frontend_status": "✅ Online" if frontend_status else "❌ Offline"
        }
    }
    
    # Save report to file
    with open("govcon_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to: govcon_test_report.json")
    return report

def print_usage_instructions():
    """Print instructions for testing the features"""
    print("\n🚀 How to Test the Government Contractor Dashboard")
    print("=" * 55)
    print("1. Start the API server:")
    print("   cd /path/to/KBILabs-main 2")
    print("   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload")
    print()
    print("2. Start the frontend development server:")
    print("   cd kbi_dashboard")
    print("   npm start")
    print()
    print("3. Open your browser and navigate to:")
    print("   http://localhost:3000/government-contractor")
    print()
    print("4. Test the following features:")
    print("   ✓ Navigate between Overview, Compliance, Opportunities, Performance tabs")
    print("   ✓ Check CMMC 2.0 compliance dashboard")
    print("   ✓ Verify DFARS compliance status")
    print("   ✓ Review FedRAMP requirements")
    print("   ✓ Analyze NAICS code opportunities")
    print("   ✓ View contract pipeline metrics")
    print()
    print("5. API Documentation available at:")
    print("   http://localhost:8001/api/docs")

def main():
    """Main testing function"""
    print("🏛️  KBI Labs Government Contractor Feature Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test API endpoints
    api_results = test_api_endpoints()
    
    # Test frontend
    frontend_status = test_frontend_accessibility()
    
    # Generate report
    generate_test_report(api_results, frontend_status)
    
    # Print usage instructions
    print_usage_instructions()
    
    # Exit with appropriate code
    total_tests = len(api_results) + (1 if frontend_status else 0)
    passed_tests = sum(1 for r in api_results.values() if "PASS" in r["status"]) + (1 if frontend_status else 0)
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Government Contractor dashboard is ready for use.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()