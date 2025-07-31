#!/usr/bin/env python3
"""Start KBI Labs API with enrichment capabilities"""
import os
import sys
import subprocess

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def find_main_file():
    """Find the main API file"""
    candidates = [
        "src/main.py",
        "src/main_update.py",
        "src/main_with_static.py",
        "main.py",
        "app.py"
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            # Check if it has FastAPI app
            with open(candidate, 'r') as f:
                content = f.read()
                if 'FastAPI' in content and ('app =' in content or 'app=' in content):
                    return candidate
    
    return None

def main():
    """Start the API server"""
    print("🚀 Starting KBI Labs API Server")
    print("=" * 50)
    
    # Check environment
    sam_key = os.getenv("SAM_GOV_API_KEY", "")
    if sam_key:
        print(f"✅ SAM.gov API Key loaded: {sam_key[:10]}...")
    else:
        print("⚠️  SAM.gov API Key not found in environment")
    
    # Find main file
    main_file = find_main_file()
    
    if not main_file:
        print("❌ No main API file found!")
        print("Please create a FastAPI application in src/main.py or main.py")
        return
    
    print(f"✅ Found API file: {main_file}")
    
    # Determine module name
    if main_file.startswith("src/"):
        module = main_file.replace("/", ".").replace(".py", "")
    else:
        module = main_file.replace(".py", "")
    
    # Start uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn",
        f"{module}:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    print(f"\n🔧 Running: {' '.join(cmd)}")
    print("\n📡 API will be available at:")
    print("   Local: http://localhost:8000")
    print("   Network: http://0.0.0.0:8000")
    print("   Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")

if __name__ == "__main__":
    main()
