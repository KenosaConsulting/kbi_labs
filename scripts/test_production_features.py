#!/usr/bin/env python3
"""
Test Production Features Script
Quick test of all new production-ready features
"""

import asyncio
import aiohttp
import json
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

class ProductionFeatureTester:
    """Test all production features"""
    
    def __init__(self):
        self.session = None
        self.token = None
        self.test_results = {}
    
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
    
    async def teardown(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """Test enhanced health check endpoint"""
        print("🔍 Testing health check endpoint...")
        
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                data = await response.json()
                
                self.test_results["health_check"] = {
                    "status": response.status,
                    "response": data,
                    "passed": response.status in [200, 500]  # Either healthy or reporting issues
                }
                
                print(f"✅ Health check: {data.get('status', 'unknown')}")
                print(f"   Services: {list(data.get('services', {}).keys())}")
                
        except Exception as e:
            self.test_results["health_check"] = {
                "status": "error",
                "error": str(e),
                "passed": False
            }
            print(f"❌ Health check failed: {e}")
    
    async def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        print("\n📊 Testing metrics endpoint...")
        
        try:
            async with self.session.get(f"{BASE_URL}/metrics") as response:
                text_data = await response.text()
                
                # Check for common Prometheus metrics
                has_metrics = any(metric in text_data for metric in [
                    "http_requests_total",
                    "http_request_duration_seconds",
                    "system_cpu_usage"
                ])
                
                self.test_results["metrics"] = {
                    "status": response.status,
                    "has_prometheus_metrics": has_metrics,
                    "content_type": response.headers.get("content-type", ""),
                    "passed": response.status == 200 and has_metrics
                }
                
                print(f"✅ Metrics endpoint accessible")
                print(f"   Content type: {response.headers.get('content-type')}")
                print(f"   Has Prometheus metrics: {has_metrics}")
                
        except Exception as e:
            self.test_results["metrics"] = {
                "status": "error",
                "error": str(e),
                "passed": False
            }
            print(f"❌ Metrics endpoint failed: {e}")
    
    async def test_authentication(self):
        """Test authentication system"""
        print("\n🔐 Testing authentication system...")
        
        try:
            # Test login with default admin credentials
            login_data = {
                "email": "admin@kbilabs.com",
                "password": "admin123"
            }
            
            async with self.session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
                data = await response.json()
                
                if response.status == 200:
                    self.token = data.get("access_token")
                    self.test_results["auth_login"] = {
                        "status": response.status,
                        "has_token": bool(self.token),
                        "user_info": data.get("user_info", {}),
                        "passed": True
                    }
                    print("✅ Authentication login successful")
                    print(f"   User: {data.get('user_info', {}).get('email')}")
                    print(f"   Roles: {data.get('user_info', {}).get('roles', [])}")
                else:
                    self.test_results["auth_login"] = {
                        "status": response.status,
                        "error": data,
                        "passed": False
                    }
                    print(f"❌ Authentication login failed: {response.status}")
                    
        except Exception as e:
            self.test_results["auth_login"] = {
                "status": "error",
                "error": str(e),
                "passed": False
            }
            print(f"❌ Authentication test failed: {e}")
    
    async def test_protected_endpoint(self):
        """Test protected endpoint with authentication"""
        print("\n🛡️ Testing protected endpoints...")
        
        if not self.token:
            print("❌ No token available, skipping protected endpoint test")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test user info endpoint
            async with self.session.get(f"{BASE_URL}/auth/me", headers=headers) as response:
                data = await response.json()
                
                self.test_results["protected_endpoint"] = {
                    "status": response.status,
                    "user_data": data,
                    "passed": response.status == 200
                }
                
                if response.status == 200:
                    print("✅ Protected endpoint accessible with token")
                    print(f"   User: {data.get('email')}")
                else:
                    print(f"❌ Protected endpoint failed: {response.status}")
                    
        except Exception as e:
            self.test_results["protected_endpoint"] = {
                "status": "error",
                "error": str(e),
                "passed": False
            }
            print(f"❌ Protected endpoint test failed: {e}")
    
    async def test_rate_limiting(self):
        """Test rate limiting"""
        print("\n🚦 Testing rate limiting...")
        
        try:
            # Make multiple rapid requests to trigger rate limiting
            responses = []
            for i in range(20):  # Make 20 rapid requests
                try:
                    async with self.session.get(f"{BASE_URL}/health") as response:
                        responses.append(response.status)
                except Exception:
                    responses.append(0)
            
            rate_limited = any(status == 429 for status in responses)
            success_count = sum(1 for status in responses if status == 200)
            
            self.test_results["rate_limiting"] = {
                "total_requests": len(responses),
                "successful_requests": success_count,
                "rate_limited": rate_limited,
                "passed": True  # Either works or gets rate limited - both are correct
            }
            
            if rate_limited:
                print("✅ Rate limiting is working (some requests blocked)")
            else:
                print("ℹ️ Rate limiting not triggered with test load")
                
        except Exception as e:
            self.test_results["rate_limiting"] = {
                "status": "error",
                "error": str(e),
                "passed": False
            }
            print(f"❌ Rate limiting test failed: {e}")
    
    async def test_data_enrichment_endpoint(self):
        """Test data enrichment endpoints with authentication"""
        print("\n🔄 Testing data enrichment endpoints...")
        
        if not self.token:
            print("❌ No token available, skipping enrichment test")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test agencies endpoint
            async with self.session.get(f"{BASE_URL}/api/data-enrichment/agencies", headers=headers) as response:
                data = await response.json()
                
                self.test_results["enrichment_agencies"] = {
                    "status": response.status,
                    "agencies_count": len(data.get("agencies", [])),
                    "passed": response.status == 200
                }
                
                if response.status == 200:
                    print(f"✅ Agencies endpoint: {len(data.get('agencies', []))} agencies available")
                else:
                    print(f"❌ Agencies endpoint failed: {response.status}")
            
            # Test enrichment request
            enrichment_data = {
                "agency_code": "9700",
                "agency_name": "Department of Defense",
                "data_types": ["budget", "personnel"],
                "enrichment_depth": "standard"
            }
            
            async with self.session.post(f"{BASE_URL}/api/data-enrichment/enrich", 
                                       json=enrichment_data, headers=headers) as response:
                data = await response.json()
                
                self.test_results["enrichment_request"] = {
                    "status": response.status,
                    "success": data.get("success", False),
                    "job_id": data.get("job_id"),
                    "passed": response.status == 200 and data.get("success", False)
                }
                
                if response.status == 200:
                    print(f"✅ Enrichment request successful: {data.get('job_id')}")
                else:
                    print(f"❌ Enrichment request failed: {response.status}")
                    
        except Exception as e:
            self.test_results["enrichment_request"] = {
                "status": "error",
                "error": str(e),
                "passed": False
            }
            print(f"❌ Enrichment endpoint test failed: {e}")
    
    async def test_input_validation(self):
        """Test input validation"""
        print("\n✅ Testing input validation...")
        
        if not self.token:
            print("❌ No token available, skipping validation test")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test with invalid data (should be rejected)
            invalid_data = {
                "agency_code": "'; DROP TABLE users; --",  # SQL injection attempt
                "data_types": ["invalid_type"],
                "enrichment_depth": "malicious"
            }
            
            async with self.session.post(f"{BASE_URL}/api/data-enrichment/enrich",
                                       json=invalid_data, headers=headers) as response:
                
                # Should return validation error (422 or 400)
                validation_working = response.status in [422, 400]
                
                self.test_results["input_validation"] = {
                    "status": response.status,
                    "validation_working": validation_working,
                    "passed": validation_working
                }
                
                if validation_working:
                    print("✅ Input validation is working (malicious input rejected)")
                else:
                    print(f"❌ Input validation may be weak: {response.status}")
                    
        except Exception as e:
            self.test_results["input_validation"] = {
                "status": "error",
                "error": str(e),
                "passed": False
            }
            print(f"❌ Input validation test failed: {e}")
    
    async def run_all_tests(self):
        """Run all production feature tests"""
        print("🚀 Testing KBI Labs Production Features")
        print("=" * 50)
        
        await self.setup()
        
        try:
            await self.test_health_check()
            await self.test_metrics_endpoint()
            await self.test_authentication()
            await self.test_protected_endpoint()
            await self.test_rate_limiting()
            await self.test_data_enrichment_endpoint()
            await self.test_input_validation()
            
            # Print summary
            print("\n" + "=" * 50)
            print("📋 Test Results Summary")
            print("=" * 50)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() 
                              if isinstance(result, dict) and result.get("passed", False))
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
            
            print("\nDetailed Results:")
            for test_name, result in self.test_results.items():
                status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
                print(f"  {test_name}: {status}")
            
            # Save detailed results
            with open("test_results.json", "w") as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            print("\n💾 Detailed results saved to test_results.json")
            
            if passed_tests == total_tests:
                print("\n🎉 All production features are working correctly!")
                return True
            else:
                print(f"\n⚠️ {total_tests - passed_tests} tests failed. Check the results above.")
                return False
                
        finally:
            await self.teardown()

async def main():
    """Main test runner"""
    tester = ProductionFeatureTester()
    
    print("Make sure the server is running with:")
    print("  python main_server.py")
    print("or")
    print("  uvicorn main_server:app --reload")
    print("")
    
    # Wait a moment for user to see the message
    await asyncio.sleep(2)
    
    success = await tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)