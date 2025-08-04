#!/usr/bin/env python3
"""
KBI Labs Data Enrichment System Setup
Complete setup script to get the enrichment system running for testing
"""

import asyncio
import os
import sys
import subprocess
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnrichmentSystemSetup:
    """Setup manager for the complete enrichment system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_root = self.project_root / "backend"
        self.frontend_root = self.project_root / "frontend"
        
    def run_command(self, command, cwd=None, shell=True):
        """Run a shell command and return the result"""
        try:
            logger.info(f"Running: {command}")
            result = subprocess.run(
                command, 
                shell=shell, 
                cwd=cwd or self.project_root,
                capture_output=True, 
                text=True, 
                check=True
            )
            logger.info(f"✅ Command successful")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Command failed: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            return None
    
    def check_system_requirements(self):
        """Check if system requirements are met"""
        logger.info("🔍 Checking system requirements...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major != 3 or python_version.minor < 8:
            logger.error("❌ Python 3.8+ is required")
            return False
        logger.info(f"✅ Python {python_version.major}.{python_version.minor} found")
        
        # Check if PostgreSQL is available
        pg_result = self.run_command("which psql")
        if not pg_result:
            logger.warning("⚠️  PostgreSQL client not found. You may need to install PostgreSQL")
            logger.info("   For macOS: brew install postgresql")
            logger.info("   For Ubuntu: sudo apt-get install postgresql-client")
            
            # Check if we can use Docker instead
            docker_result = self.run_command("which docker")
            if docker_result:
                logger.info("✅ Docker found - we can use Docker PostgreSQL")
                return True
            else:
                logger.error("❌ Neither PostgreSQL nor Docker found")
                return False
        else:
            logger.info("✅ PostgreSQL client found")
            
        return True
    
    def setup_environment_file(self):
        """Create environment configuration file"""
        logger.info("📝 Setting up environment configuration...")
        
        env_file = self.project_root / ".env"
        env_content = """
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=kbi_labs_enrichment
DATABASE_USER=kbi_user
DATABASE_PASSWORD=kbi_password

# Database Pool Configuration  
DATABASE_POOL_MIN_SIZE=5
DATABASE_POOL_MAX_SIZE=20
DATABASE_COMMAND_TIMEOUT=60

# Data Enrichment Configuration
ENRICHMENT_MAX_CONCURRENT_JOBS=3
ENRICHMENT_JOB_TIMEOUT_MINUTES=30
ENRICHMENT_CACHE_DEFAULT_HOURS=168

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# External API Configuration (optional - can be added later)
# USASPENDING_API_KEY=your_key_if_needed
# SAM_GOV_API_KEY=your_sam_gov_key

# Development flags
ENVIRONMENT=development
DEBUG=true
""".strip()
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        logger.info(f"✅ Environment file created: {env_file}")
        return env_file
    
    def setup_database_with_docker(self):
        """Set up PostgreSQL database using Docker"""
        logger.info("🐳 Setting up PostgreSQL database with Docker...")
        
        # Create docker-compose.yml for database
        docker_compose_content = """
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: kbi_postgres
    environment:
      POSTGRES_DB: kbi_labs_enrichment
      POSTGRES_USER: kbi_user
      POSTGRES_PASSWORD: kbi_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/database/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kbi_user -d kbi_labs_enrichment"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
""".strip()
        
        docker_compose_file = self.project_root / "docker-compose.db.yml"
        with open(docker_compose_file, 'w') as f:
            f.write(docker_compose_content)
        
        logger.info("✅ Docker Compose file created")
        
        # Start PostgreSQL container
        result = self.run_command("docker-compose -f docker-compose.db.yml up -d")
        if not result:
            logger.error("❌ Failed to start PostgreSQL container")
            return False
        
        logger.info("✅ PostgreSQL container started")
        
        # Wait for database to be ready
        logger.info("⏳ Waiting for database to be ready...")
        for i in range(30):
            test_result = self.run_command(
                "docker exec kbi_postgres pg_isready -U kbi_user -d kbi_labs_enrichment"
            )
            if test_result:
                logger.info("✅ Database is ready")
                return True
            logger.info(f"   Waiting... ({i+1}/30)")
            import time
            time.sleep(2)
        
        logger.error("❌ Database failed to become ready")
        return False
    
    def install_python_dependencies(self):
        """Install required Python packages"""
        logger.info("📦 Installing Python dependencies...")
        
        # Check if virtual environment exists
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            logger.info("Creating virtual environment...")
            result = self.run_command(f"python -m venv {venv_path}")
            if not result:
                logger.error("❌ Failed to create virtual environment")
                return False
        
        # Determine activation script based on OS
        if os.name == 'nt':  # Windows
            activate_script = venv_path / "Scripts" / "activate"
            pip_path = venv_path / "Scripts" / "pip"
        else:  # Unix/Linux/macOS
            activate_script = venv_path / "bin" / "activate"
            pip_path = venv_path / "bin" / "pip"
        
        logger.info(f"Using pip at: {pip_path}")
        
        # Create updated requirements.txt with all needed packages
        requirements_content = """
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
aiohttp==3.9.0
asyncpg==0.29.0
pandas==2.0.3
requests==2.31.0
python-dotenv==1.0.0
websockets==12.0
python-multipart==0.0.6
""".strip()
        
        requirements_file = self.project_root / "requirements_enrichment.txt"
        with open(requirements_file, 'w') as f:
            f.write(requirements_content)
        
        # Install dependencies
        result = self.run_command(f"{pip_path} install -r {requirements_file}")
        if not result:
            logger.error("❌ Failed to install Python dependencies")
            return False
        
        logger.info("✅ Python dependencies installed")
        return True
    
    def run_database_migrations(self):
        """Run database migrations"""
        logger.info("🗄️  Running database migrations...")
        
        # Test database connection first
        test_command = """
docker exec kbi_postgres psql -U kbi_user -d kbi_labs_enrichment -c "SELECT version();"
"""
        result = self.run_command(test_command.strip())
        if not result:
            logger.error("❌ Cannot connect to database")
            return False
        
        # Run the migration file
        migration_file = self.backend_root / "database" / "migrations" / "001_add_data_enrichment_tables.sql"
        if not migration_file.exists():
            logger.error(f"❌ Migration file not found: {migration_file}")
            return False
        
        # Copy migration file into container and execute
        copy_result = self.run_command(
            f"docker cp {migration_file} kbi_postgres:/tmp/migration.sql"
        )
        if not copy_result:
            logger.error("❌ Failed to copy migration file to container")
            return False
        
        exec_result = self.run_command(
            "docker exec kbi_postgres psql -U kbi_user -d kbi_labs_enrichment -f /tmp/migration.sql"
        )
        if not exec_result:
            logger.error("❌ Failed to execute migration")
            return False
        
        logger.info("✅ Database migrations completed")
        return True
    
    def create_test_api_server(self):
        """Create a test API server for testing"""
        logger.info("🚀 Creating test API server...")
        
        api_server_content = '''
import asyncio
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

# Add backend to Python path
import sys
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

from api.data_enrichment_routes import router as enrichment_router

app = FastAPI(
    title="KBI Labs Data Enrichment API",
    description="Government data enrichment system for SMB government contractors",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include enrichment routes
app.include_router(enrichment_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "kbi-enrichment-api"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "KBI Labs Data Enrichment API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "enrichment": "/api/data-enrichment/",
            "docs": "/docs"
        }
    }

# Serve frontend static files (if available)
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")

if __name__ == "__main__":
    uvicorn.run(
        "test_api_server:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
        log_level="info"
    )
'''.strip()
        
        api_server_file = self.project_root / "test_api_server.py"
        with open(api_server_file, 'w') as f:
            f.write(api_server_content)
        
        logger.info("✅ Test API server created")
        return api_server_file
    
    def create_test_frontend_page(self):
        """Create a simple test frontend page"""
        logger.info("🎨 Creating test frontend page...")
        
        html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KBI Labs Data Enrichment - Test Page</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold text-center mb-8">KBI Labs Data Enrichment System</h1>
        
        <div class="max-w-2xl mx-auto">
            <!-- System Status -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">System Status</h2>
                <div id="system-status" class="space-y-2">
                    <div class="flex justify-between">
                        <span>API Server:</span>
                        <span id="api-status" class="text-yellow-600">Checking...</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Database:</span>
                        <span id="db-status" class="text-yellow-600">Checking...</span>
                    </div>
                </div>
            </div>
            
            <!-- Quick Test -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">Quick Test</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">Agency Code:</label>
                        <input type="text" id="agency-code" value="9700" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md">
                    </div>
                    <button id="test-enrichment" 
                            class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">
                        Test Agency Enrichment
                    </button>
                </div>
            </div>
            
            <!-- Results -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">Test Results</h2>
                <pre id="test-results" class="bg-gray-100 p-4 rounded text-sm overflow-auto max-h-96">
Ready to test...
                </pre>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000';
        
        // Check system status
        async function checkSystemStatus() {
            try {
                const response = await fetch(`${API_BASE}/health`);
                const data = await response.json();
                document.getElementById('api-status').textContent = 'Online';
                document.getElementById('api-status').className = 'text-green-600';
                
                // Check if enrichment endpoints are available
                const enrichmentResponse = await fetch(`${API_BASE}/api/data-enrichment/agencies`);
                const enrichmentData = await enrichmentResponse.json();
                document.getElementById('db-status').textContent = 'Connected';
                document.getElementById('db-status').className = 'text-green-600';
                
            } catch (error) {
                document.getElementById('api-status').textContent = 'Offline';
                document.getElementById('api-status').className = 'text-red-600';
                document.getElementById('db-status').textContent = 'Disconnected';
                document.getElementById('db-status').className = 'text-red-600';
            }
        }
        
        // Test enrichment
        document.getElementById('test-enrichment').addEventListener('click', async () => {
            const agencyCode = document.getElementById('agency-code').value;
            const resultsElement = document.getElementById('test-results');
            
            resultsElement.textContent = 'Testing enrichment request...\\n';
            
            try {
                const response = await fetch(`${API_BASE}/api/data-enrichment/enrich`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        agency_code: agencyCode,
                        agency_name: `Test Agency ${agencyCode}`,
                        data_types: ['budget', 'personnel'],
                        enrichment_depth: 'basic',
                        priority: 'normal'
                    })
                });
                
                const data = await response.json();
                resultsElement.textContent += `Response (${response.status}): \\n${JSON.stringify(data, null, 2)}`;
                
            } catch (error) {
                resultsElement.textContent += `Error: ${error.message}`;
            }
        });
        
        // Check status on page load
        checkSystemStatus();
        
        // Refresh status every 30 seconds
        setInterval(checkSystemStatus, 30000);
    </script>
</body>
</html>
'''.strip()
        
        test_page = self.project_root / "test_enrichment_system.html"
        with open(test_page, 'w') as f:
            f.write(html_content)
        
        logger.info("✅ Test frontend page created")
        return test_page
    
    def run_complete_setup(self):
        """Run the complete setup process"""
        logger.info("🚀 Starting KBI Labs Data Enrichment System Setup")
        logger.info("=" * 60)
        
        try:
            # Step 1: Check system requirements
            if not self.check_system_requirements():
                logger.error("❌ System requirements not met")
                return False
            
            # Step 2: Setup environment
            self.setup_environment_file()
            
            # Step 3: Install Python dependencies
            if not self.install_python_dependencies():
                logger.error("❌ Failed to install dependencies")
                return False
            
            # Step 4: Setup database
            if not self.setup_database_with_docker():
                logger.error("❌ Failed to setup database")
                return False
            
            # Step 5: Run migrations
            if not self.run_database_migrations():
                logger.error("❌ Failed to run migrations")
                return False
            
            # Step 6: Create test server
            api_server_file = self.create_test_api_server()
            
            # Step 7: Create test frontend
            test_page = self.create_test_frontend_page()
            
            logger.info("✅ Setup completed successfully!")
            logger.info("")
            logger.info("🎉 Next Steps:")
            logger.info("=" * 40)
            logger.info("1. Start the API server:")
            logger.info(f"   cd {self.project_root}")
            logger.info("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
            logger.info("   python test_api_server.py")
            logger.info("")
            logger.info("2. Open the test page:")
            logger.info(f"   open {test_page}")
            logger.info("   or visit: file://" + str(test_page.absolute()))
            logger.info("")
            logger.info("3. API Documentation available at:")
            logger.info("   http://localhost:8000/docs")
            logger.info("")
            logger.info("4. Test the system with the web interface!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {str(e)}")
            return False

def main():
    """Main setup function"""
    setup = EnrichmentSystemSetup()
    success = setup.run_complete_setup()
    
    if success:
        print("\\n🎉 Setup completed successfully!")
        sys.exit(0)
    else:
        print("\\n❌ Setup failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()