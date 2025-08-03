#!/usr/bin/env python3
"""
KBI Labs Deployment Verification Script
Ensures the correct AI-powered application is deployed to production
"""

import requests
import time
import json
import sys

def test_production_deployment():
    """Test if the correct AI application is deployed"""
    base_url = "http://3.143.232.123:8000"
    
    print("🔍 Testing KBI Labs Production Deployment...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Check if it's our FastAPI app
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        data = response.json()
        
        expected_title = "KBI Labs - Compass Platform"
        actual_title = data.get("message", data.get("title", ""))
        
        if expected_title in actual_title or "AI-Powered" in str(data):
            print(f"✅ Correct application deployed: {actual_title}")
        else:
            print(f"❌ Wrong application deployed: {actual_title}")
            print(f"   Expected: {expected_title}")
            print(f"   Full response: {data}")
            return False
            
    except Exception as e:
        print(f"❌ App check error: {e}")
        return False
    
    # Test 3: Unique verification endpoint
    try:
        response = requests.get(f"{base_url}/deployment/verify", timeout=10)
        if response.status_code == 200:
            verify_data = response.json()
            verification_code = verify_data.get("verification_code", "")
            
            if verification_code == "FASTAPI_AI_DEPLOYED_SUCCESSFULLY":
                print("✅ KBI Labs FastAPI application verified!")
                print(f"   Application: {verify_data.get('application', 'unknown')}")
                print(f"   Version: {verify_data.get('version', 'unknown')}")
                print(f"   AI Services: {verify_data.get('ai_services', False)}")
                
                # Test AI endpoint as bonus
                try:
                    ai_response = requests.get(f"{base_url}/api/ai/status", timeout=5)
                    if ai_response.status_code == 200:
                        ai_data = ai_response.json()
                        if ai_data.get("deployment_id") == "KBI_LABS_FASTAPI_VERIFIED":
                            print("✅ AI services also verified!")
                            return True
                    print("⚠️ AI endpoint needs attention but FastAPI is running")
                    return True
                except:
                    print("⚠️ AI endpoint test failed but FastAPI is verified")
                    return True
            else:
                print(f"❌ Wrong verification code: {verification_code}")
                return False
        else:
            print(f"❌ Verification endpoint failed: {response.status_code}")
            # Fallback to old AI test
            try:
                response = requests.get(f"{base_url}/api/ai/status", timeout=10)
                if response.status_code == 200:
                    ai_data = response.json()
                    if ai_data.get("deployment_id") == "KBI_LABS_FASTAPI_VERIFIED":
                        print("✅ AI services verified (fallback test)!")
                        return True
                print("❌ Old API Gateway still running")
                return False
            except:
                print("❌ No KBI Labs endpoints found")
                return False
            
    except Exception as e:
        print(f"❌ Verification test error: {e}")
        return False

def wait_for_deployment(max_wait=300):
    """Wait for deployment to complete"""
    print(f"⏳ Waiting for deployment to complete (max {max_wait}s)...")
    
    for i in range(max_wait // 10):
        if test_production_deployment():
            print(f"🎉 Deployment successful after {i*10}s!")
            return True
        
        if i < (max_wait // 10) - 1:
            print(f"   Checking again in 10s... ({i*10}s elapsed)")
            time.sleep(10)
    
    print(f"❌ Deployment verification failed after {max_wait}s")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        success = wait_for_deployment()
    else:
        success = test_production_deployment()
    
    sys.exit(0 if success else 1)