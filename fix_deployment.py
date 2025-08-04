#!/usr/bin/env python3
"""
KBI Labs Deployment Fix Script
Fixes the deployment inconsistency by ensuring the correct version is deployed
"""

import subprocess
import requests
import time
import json
import sys
from datetime import datetime

def log(message):
    """Log with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def run_command(command, description):
    """Run a shell command and return result"""
    log(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            log(f"✅ {description} - Success")
            return result.stdout.strip()
        else:
            log(f"❌ {description} - Failed: {result.stderr}")
            return None
    except Exception as e:
        log(f"❌ {description} - Exception: {e}")
        return None

def check_production_status():
    """Check current production status"""
    log("Checking current production status...")
    
    try:
        response = requests.get("http://3.143.232.123:8000/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log(f"Current version: {data.get('version', 'unknown')}")
            log(f"Current title: {data.get('message', 'unknown')}")
            return data
        else:
            log(f"❌ Production server returned status {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Unable to reach production server: {e}")
        return None

def check_ai_endpoints():
    """Check if AI endpoints are available"""
    log("Checking AI endpoints...")
    
    endpoints_to_check = [
        "/api/government-intelligence/health",
        "/api/government-intelligence/procurement-opportunities",
        "/health",
        "/api/docs"
    ]
    
    results = {}
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(f"http://3.143.232.123:8000{endpoint}", timeout=10)
            results[endpoint] = {
                "status_code": response.status_code,
                "available": response.status_code == 200
            }
            log(f"Endpoint {endpoint}: {'✅' if response.status_code == 200 else '❌'} ({response.status_code})")
        except Exception as e:
            results[endpoint] = {
                "status_code": None,
                "available": False,
                "error": str(e)
            }
            log(f"Endpoint {endpoint}: ❌ Error - {e}")
    
    return results

def build_and_test_locally():
    """Build and test the unified application locally"""
    log("Building unified application locally...")
    
    # Test the unified main file
    log("Testing unified main file...")
    result = run_command("cd /Users/oogwayuzumaki/kbi_labs && python -c \"from src.main_unified import app; print('✅ Unified app loads successfully')\"", "Test unified app import")
    
    if result is None:
        log("❌ Unified app failed to load locally")
        return False
    
    # Build Docker image
    log("Building Docker image...")
    result = run_command("cd /Users/oogwayuzumaki/kbi_labs && docker build -t kbi_labs:fixed .", "Build Docker image")
    
    if result is None:
        log("❌ Docker build failed")
        return False
    
    log("✅ Local build successful")
    return True

def create_deployment_commands():
    """Create commands for deployment"""
    log("Creating deployment commands...")
    
    commands = [
        "# Stop current container if running",
        "docker stop kbi_labs_container || true",
        "docker rm kbi_labs_container || true",
        "",
        "# Build new image with unified main",
        "docker build -t kbi_labs:latest .",
        "",
        "# Run new container",
        "docker run -d --name kbi_labs_container -p 8000:8000 kbi_labs:latest",
        "",
        "# Check logs",
        "docker logs kbi_labs_container",
        "",
        "# Test endpoints",
        "sleep 10",
        "curl http://localhost:8000/",
        "curl http://localhost:8000/health",
        "curl http://localhost:8000/api/government-intelligence/health"
    ]
    
    with open("/Users/oogwayuzumaki/kbi_labs/deploy_commands.sh", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# KBI Labs Deployment Fix Commands\n")
        f.write("# Run these commands on the production server\n\n")
        for command in commands:
            f.write(command + "\n")
    
    log("✅ Deployment commands saved to deploy_commands.sh")

def main():
    """Main deployment fix process"""
    log("🚀 Starting KBI Labs Deployment Fix")
    log("=" * 50)
    
    # Step 1: Check current production status
    current_status = check_production_status()
    
    # Step 2: Check AI endpoints availability
    endpoint_results = check_ai_endpoints()
    
    # Step 3: Count missing endpoints
    missing_endpoints = sum(1 for result in endpoint_results.values() if not result["available"])
    log(f"Missing endpoints: {missing_endpoints}/{len(endpoint_results)}")
    
    # Step 4: Build and test locally
    local_success = build_and_test_locally()
    
    if not local_success:
        log("❌ Local build failed. Cannot proceed with deployment.")
        sys.exit(1)
    
    # Step 5: Create deployment commands
    create_deployment_commands()
    
    # Step 6: Summary and next steps
    log("\n" + "=" * 50)
    log("🎯 DEPLOYMENT FIX SUMMARY")
    log("=" * 50)
    
    if current_status:
        log(f"Current Production Version: {current_status.get('version', 'unknown')}")
    
    log(f"Target Version: 2.2.0 (Unified Platform)")
    log(f"Missing AI Endpoints: {missing_endpoints}")
    log(f"Local Build Status: {'✅ Success' if local_success else '❌ Failed'}")
    
    log("\n📋 NEXT STEPS:")
    log("1. The unified application has been built and tested locally")
    log("2. Deployment commands have been saved to deploy_commands.sh")
    log("3. Copy the updated code to the production server")
    log("4. Run the deployment commands on the production server")
    log("5. Verify all endpoints are working")
    
    log("\n🔧 MANUAL DEPLOYMENT:")
    log("scp -r kbi_labs/ user@3.143.232.123:/path/to/deployment/")
    log("ssh user@3.143.232.123")
    log("cd /path/to/deployment/kbi_labs")
    log("bash deploy_commands.sh")
    
    log("\n✅ Deployment fix preparation complete!")

if __name__ == "__main__":
    main()