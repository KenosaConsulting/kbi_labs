#!/usr/bin/env python3
"""
Data Enrichment Setup Script
Week 1 Implementation Setup for KBI Labs Platform

This script sets up the data enrichment pipeline integration:
1. Runs database migrations
2. Initializes the enrichment service
3. Tests the API endpoints
4. Provides usage examples
"""

import asyncio
import asyncpg
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from database.connection import create_database_pool, execute_migration, check_database_health
from services.data_enrichment_service import get_enrichment_service, EnrichmentJobConfig, Priority

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataEnrichmentSetup:
    """Setup manager for data enrichment integration"""
    
    def __init__(self):
        self.db_pool = None
        self.enrichment_service = None
    
    async def run_complete_setup(self):
        """Run the complete setup process"""
        
        logger.info("🚀 Starting KBI Labs Data Enrichment Setup")
        logger.info("=" * 60)
        
        try:
            # Step 1: Database Setup
            await self._setup_database()
            
            # Step 2: Service Initialization
            await self._initialize_services()
            
            # Step 3: API Testing
            await self._test_api_functionality()
            
            # Step 4: Usage Examples
            await self._demonstrate_usage()
            
            logger.info("✅ Data enrichment setup completed successfully!")
            logger.info("📋 Next steps:")
            logger.info("   1. Update your FastAPI app to include the new routes")
            logger.info("   2. Set up environment variables for database connection")
            logger.info("   3. Configure background job processing")
            logger.info("   4. Update frontend to use new enrichment endpoints")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {str(e)}")
            raise
        
        finally:
            await self._cleanup()
    
    async def _setup_database(self):
        """Set up database schema and migrations"""
        
        logger.info("📊 Setting up database schema...")
        
        try:
            # Create connection pool
            self.db_pool = await create_database_pool()
            
            # Check database health
            health_status = await check_database_health()
            if health_status['status'] != 'healthy':
                raise Exception(f"Database unhealthy: {health_status}")
            
            logger.info(f"✅ Database connection established")
            logger.info(f"   Database version: {health_status.get('database_version', 'Unknown')}")
            
            # Run migration
            migration_file = Path(__file__).parent / "database/migrations/001_add_data_enrichment_tables.sql"
            
            if migration_file.exists():
                logger.info("🔄 Running database migration...")
                await execute_migration(str(migration_file))
                logger.info("✅ Database migration completed")
            else:
                logger.warning("⚠️  Migration file not found - please run manually")
            
            # Verify tables were created
            await self._verify_database_schema()
            
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise
    
    async def _verify_database_schema(self):
        """Verify that all required tables were created"""
        
        logger.info("🔍 Verifying database schema...")
        
        required_tables = [
            'data_enrichment_jobs',
            'enriched_data_cache', 
            'data_source_health',
            'enrichment_schedules',
            'data_quality_reports'
        ]
        
        async with self.db_pool.acquire() as conn:
            for table in required_tables:
                exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = $1
                    )
                """, table)
                
                if exists:
                    logger.info(f"   ✅ Table '{table}' exists")
                else:
                    logger.error(f"   ❌ Table '{table}' missing")
                    raise Exception(f"Required table '{table}' was not created")
        
        logger.info("✅ Database schema verification completed")
    
    async def _initialize_services(self):
        """Initialize the data enrichment service"""
        
        logger.info("⚙️  Initializing data enrichment services...")
        
        try:
            # Get enrichment service instance
            self.enrichment_service = await get_enrichment_service(self.db_pool)
            
            logger.info("✅ Data enrichment service initialized")
            logger.info("   📊 Government data pipeline ready")
            logger.info("   👥 Personnel collector ready")
            logger.info("   💰 Budget extractor ready")
            logger.info("   🏢 Organizational scraper ready")
            logger.info("   ✔️  Data validator ready")
            
        except Exception as e:
            logger.error(f"Service initialization failed: {str(e)}")
            raise
    
    async def _test_api_functionality(self):
        """Test core API functionality"""
        
        logger.info("🧪 Testing API functionality...")
        
        try:
            # Test 1: Check supported agencies
            logger.info("   Testing agency support...")
            
            # Test 2: Request enrichment (this will queue a job)
            logger.info("   Testing enrichment request...")
            
            config = EnrichmentJobConfig(
                agency_code="9700",
                agency_name="Department of Defense",
                data_types=["budget", "personnel"],
                enrichment_depth="basic",
                priority=Priority.HIGH,
                requested_by_user_id="test-user"
            )
            
            result = await self.enrichment_service.request_agency_enrichment(config)
            logger.info(f"   ✅ Enrichment request: {result.get('status')}")
            
            if result.get('job_id'):
                job_id = result['job_id']
                
                # Test 3: Check job status
                logger.info("   Testing job status...")
                status = await self.enrichment_service.get_job_status(job_id)
                logger.info(f"   ✅ Job status: {status.get('status', 'unknown')}")
            
            # Test 4: Check agency summary
            logger.info("   Testing agency summary...")
            summary = await self.enrichment_service.get_enrichment_summary("9700")
            logger.info(f"   ✅ Agency summary retrieved")
            
            logger.info("✅ API functionality tests completed")
            
        except Exception as e:
            logger.error(f"API testing failed: {str(e)}")
            raise
    
    async def _demonstrate_usage(self):
        """Demonstrate how to use the enrichment system"""
        
        logger.info("📚 Usage Examples:")
        logger.info("")
        
        logger.info("1. Basic enrichment request:")
        logger.info("""
        POST /api/data-enrichment/enrich
        {
            "agency_code": "9700",
            "agency_name": "Department of Defense",
            "data_types": ["budget", "personnel", "contracts"],
            "enrichment_depth": "standard", 
            "priority": "normal"
        }
        """)
        
        logger.info("2. Check job status:")
        logger.info("""
        GET /api/data-enrichment/job/{job_id}/status
        """)
        
        logger.info("3. Get enriched data:")
        logger.info("""
        GET /api/data-enrichment/agency/9700/data?data_types=budget,personnel
        """)
        
        logger.info("4. Get agency summary:")
        logger.info("""
        GET /api/data-enrichment/agency/9700/summary
        """)
        
        logger.info("5. WebSocket real-time updates:")
        logger.info("""
        WS /api/data-enrichment/ws/job/{job_id}
        """)
        
        logger.info("")
        logger.info("🔧 Integration with existing platform:")
        logger.info("")
        logger.info("Update your FastAPI app.py:")
        logger.info("""
        from backend.api.data_enrichment_routes import router as enrichment_router
        
        app.include_router(enrichment_router)
        """)
        
        logger.info("")
        logger.info("Update your frontend components:")
        logger.info("""
        // Trigger enrichment
        const response = await fetch('/api/data-enrichment/enrich', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                agency_code: '9700',
                data_types: ['budget', 'personnel'],
                enrichment_depth: 'standard'
            })
        });
        
        // Get enriched data
        const data = await fetch('/api/data-enrichment/agency/9700/data');
        """)
    
    async def _cleanup(self):
        """Clean up resources"""
        
        if self.enrichment_service:
            await self.enrichment_service.cleanup()
        
        if self.db_pool:
            await self.db_pool.close()

# Additional utility functions for integration

async def quick_test_enrichment():
    """Quick test of the enrichment system"""
    
    logger.info("🚀 Quick enrichment test")
    
    try:
        # Create database pool
        db_pool = await create_database_pool()
        
        # Get service
        service = await get_enrichment_service(db_pool)
        
        # Test enrichment request
        config = EnrichmentJobConfig(
            agency_code="7000",  # DHS
            data_types=["budget"],
            enrichment_depth="basic",
            priority=Priority.NORMAL
        )
        
        result = await service.request_agency_enrichment(config)
        logger.info(f"Test result: {result}")
        
        # Cleanup
        await service.cleanup()
        await db_pool.close()
        
        logger.info("✅ Quick test completed")
        
    except Exception as e:
        logger.error(f"Quick test failed: {str(e)}")

def setup_environment_variables():
    """Set up example environment variables"""
    
    logger.info("🔧 Environment Variable Setup:")
    logger.info("")
    logger.info("Add these to your .env file or environment:")
    logger.info("""
    # Database Configuration
    DATABASE_HOST=localhost
    DATABASE_PORT=5432
    DATABASE_NAME=kbi_labs
    DATABASE_USER=postgres
    DATABASE_PASSWORD=your_password
    
    # Database Pool Configuration
    DATABASE_POOL_MIN_SIZE=5
    DATABASE_POOL_MAX_SIZE=20
    DATABASE_COMMAND_TIMEOUT=60
    
    # Data Enrichment Configuration
    ENRICHMENT_MAX_CONCURRENT_JOBS=3
    ENRICHMENT_JOB_TIMEOUT_MINUTES=30
    ENRICHMENT_CACHE_DEFAULT_HOURS=168  # 1 week
    
    # External API Configuration (optional)
    USASPENDING_API_KEY=your_key_if_needed
    SAM_GOV_API_KEY=your_sam_gov_key
    """)

async def run_database_migration_only():
    """Run only the database migration"""
    
    logger.info("🔄 Running database migration only...")
    
    try:
        db_pool = await create_database_pool()
        
        migration_file = Path(__file__).parent / "database/migrations/001_add_data_enrichment_tables.sql"
        await execute_migration(str(migration_file))
        
        logger.info("✅ Migration completed")
        
        await db_pool.close()
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")

# Command line interface
async def main():
    """Main setup function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="KBI Labs Data Enrichment Setup")
    parser.add_argument('--mode', choices=['full', 'migration', 'test', 'env'], 
                       default='full', help='Setup mode')
    
    args = parser.parse_args()
    
    if args.mode == 'full':
        setup = DataEnrichmentSetup()
        await setup.run_complete_setup()
    
    elif args.mode == 'migration':
        await run_database_migration_only()
    
    elif args.mode == 'test':
        await quick_test_enrichment()
    
    elif args.mode == 'env':
        setup_environment_variables()

if __name__ == "__main__":
    # Set environment variables for development if not set
    if not os.getenv('DATABASE_NAME'):
        os.environ['DATABASE_NAME'] = 'kbi_labs'
        os.environ['DATABASE_USER'] = 'postgres'  
        os.environ['DATABASE_PASSWORD'] = 'password'
        os.environ['DATABASE_HOST'] = 'localhost'
        os.environ['DATABASE_PORT'] = '5432'
    
    asyncio.run(main())