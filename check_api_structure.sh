#!/bin/bash
# Check API structure and help start the server

echo "🔍 Checking KBI Labs API Structure"
echo "=================================="

# Check for main API files
echo -e "\n📁 Looking for main API files..."

# Check src/main.py
if [ -f "src/main.py" ]; then
    echo "✅ Found src/main.py"
    grep -n "FastAPI\|app = " src/main.py | head -5
elif [ -f "src/main_update.py" ]; then
    echo "✅ Found src/main_update.py"
    grep -n "FastAPI\|app = " src/main_update.py | head -5
fi

# Check for existing routers
echo -e "\n📁 Checking for existing routers..."
if [ -d "src/api/routers" ]; then
    ls -la src/api/routers/
fi

if [ -d "src/routers" ]; then
    ls -la src/routers/
fi

# Check database
echo -e "\n🗄️ Checking database..."
if [ -f "kbi_production.db" ]; then
    echo "✅ Found kbi_production.db"
    echo "   Size: $(du -h kbi_production.db | cut -f1)"
    
    # Check if enrichment table exists
    if sqlite3 kbi_production.db "SELECT name FROM sqlite_master WHERE type='table' AND name='company_enrichment';" | grep -q "company_enrichment"; then
        echo "✅ company_enrichment table exists"
        
        # Count enriched companies
        count=$(sqlite3 kbi_production.db "SELECT COUNT(*) FROM company_enrichment;" 2>/dev/null || echo "0")
        echo "   Enriched companies: $count"
    else
        echo "❌ company_enrichment table not found - running migration..."
        sqlite3 kbi_production.db < migrations/add_enrichment_table.sql
    fi
else
    echo "❌ kbi_production.db not found"
    
    # Check for other database files
    echo "   Looking for other database files..."
    ls -la *.db 2>/dev/null || echo "   No .db files found"
fi

# Create a startup script
echo -e "\n📝 Creating startup script..."
cat > start_kbi_api.py << 'EOF'
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
EOF

chmod +x start_kbi_api.py

echo -e "\n✅ Setup complete!"
echo -e "\n🚀 To start your API, run:"
echo "   python3 start_kbi_api.py"
echo -e "\nOr directly:"
echo "   python3 -m uvicorn src.main_update:app --reload"
