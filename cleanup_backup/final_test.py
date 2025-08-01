#!/usr/bin/env python3
import subprocess
import time
import requests

print("🔍 Final Infrastructure Verification\n")

# Check Docker services
print("1. Docker Services:")
result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                       capture_output=True, text=True)
print(result.stdout)

# Check ports
print("\n2. Port Status:")
ports = {
    5432: "PostgreSQL",
    6379: "Redis", 
    8000: "API Gateway",
    9092: "Kafka"
}

for port, service in ports.items():
    try:
        result = subprocess.run(['lsof', '-i', f':{port}'], 
                               capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {service} on port {port}")
        else:
            print(f"❌ {service} not found on port {port}")
    except:
        pass

# Check API
print("\n3. API Status:")
try:
    resp = requests.get("http://localhost:8000/health", timeout=2)
    print(f"✅ API responding: {resp.json()['status']}")
except:
    print("❌ API not responding")

print("\n✅ Verification complete!")
