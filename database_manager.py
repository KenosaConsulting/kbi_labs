#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Database Manager for KBI Labs
Handles PostgreSQL operations, migrations, and connection pooling
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager, contextmanager
import json

import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2.pool import ThreadedConnectionPool
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration"""
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 5432))
        self.database = os.getenv('DB_NAME', 'kbi_labs')
        self.user = os.getenv('DB_USER', 'kbi_user')
        self.password = os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', 'change-this-password'))
        
    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def psycopg2_params(self) -> Dict[str, Any]:
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }


class DatabaseManager:
    """Main database manager class"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.sync_engine = None
        self.async_engine = None
        self.connection_pool = None
        self.async_pool = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize database connections and pools"""
        if self._initialized:
            return
        
        try:
            # Create sync engine
            self.sync_engine = create_engine(
                self.config.sync_url,
                pool_size=20,
                max_overflow=40,
                pool_pre_ping=True,
                echo=False
            )
            
            # Create async engine
            self.async_engine = create_async_engine(
                self.config.async_url,
                pool_size=20,
                max_overflow=40,
                echo=False
            )
            
            # Create psycopg2 connection pool
            self.connection_pool = ThreadedConnectionPool(
                minconn=5,
                maxconn=50,
                **self.config.psycopg2_params
            )
            
            # Create asyncpg pool
            self.async_pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=10,
                max_size=50,
                command_timeout=60
            )
            
            # Create session factories
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.sync_engine
            )
            
            self.AsyncSessionLocal = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_db(self) -> Session:
        """Get SQLAlchemy session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @asynccontextmanager
    async def get_async_db(self) -> AsyncSession:
        """Get async SQLAlchemy session"""
        async with self.AsyncSessionLocal() as session:
            yield session
    
    @contextmanager
    def get_psycopg2_connection(self):
        """Get psycopg2 connection from pool"""
        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)
    
    @asynccontextmanager
    async def get_asyncpg_connection(self):
        """Get asyncpg connection from pool"""
        async with self.async_pool.acquire() as conn:
            yield conn
    
    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute a query and return results"""
        async with self.get_asyncpg_connection() as conn:
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute many queries with parameters"""
        async with self.get_asyncpg_connection() as conn:
            result = await conn.executemany(query, params_list)
            return len(params_list)
    
    def bulk_insert_dataframe(self, df: pd.DataFrame, table_name: str, 
                            schema: Optional[str] = None) -> int:
        """Bulk insert pandas DataFrame to PostgreSQL"""
        try:
            with self.get_psycopg2_connection() as conn:
                # Use COPY for best performance
                from io import StringIO
                
                # Create a string buffer
                output = StringIO()
                df.to_csv(output, sep='\t', header=False, index=False)
                output.seek(0)
                
                # Copy data
                with conn.cursor() as cursor:
                    columns = ','.join(df.columns)
                    if schema:
                        table_ref = f'"{schema}"."{table_name}"'
                    else:
                        table_ref = f'"{table_name}"'
                    
                    cursor.copy_expert(
                        f"COPY {table_ref} ({columns}) FROM STDIN WITH CSV DELIMITER E'\\t'",
                        output
                    )
                    conn.commit()
                    
            logger.info(f"Bulk inserted {len(df)} rows to {table_name}")
            return len(df)
            
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def upsert_company(self, company_data: Dict[str, Any]) -> bool:
        """Upsert company data"""
        query = """
        INSERT INTO companies (
            uei, organization_name, dba_name, city, state, zipcode,
            annual_revenue, federal_contracts_value, grants_received,
            pe_investment_score, business_health_grade, innovation_score,
            growth_potential_score, last_enriched_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        ON CONFLICT (uei) DO UPDATE SET
            organization_name = EXCLUDED.organization_name,
            dba_name = EXCLUDED.dba_name,
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            zipcode = EXCLUDED.zipcode,
            annual_revenue = EXCLUDED.annual_revenue,
            federal_contracts_value = EXCLUDED.federal_contracts_value,
            grants_received = EXCLUDED.grants_received,
            pe_investment_score = EXCLUDED.pe_investment_score,
            business_health_grade = EXCLUDED.business_health_grade,
            innovation_score = EXCLUDED.innovation_score,
            growth_potential_score = EXCLUDED.growth_potential_score,
            last_enriched_at = EXCLUDED.last_enriched_at,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id
        """
        
        try:
            async with self.get_asyncpg_connection() as conn:
                result = await conn.fetchrow(
                    query,
                    company_data.get('uei'),
                    company_data.get('organization_name'),
                    company_data.get('dba_name'),
                    company_data.get('city'),
                    company_data.get('state'),
                    company_data.get('zipcode'),
                    company_data.get('annual_revenue'),
                    company_data.get('federal_contracts_value'),
                    company_data.get('grants_received'),
                    company_data.get('pe_investment_score'),
                    company_data.get('business_health_grade'),
                    company_data.get('innovation_score'),
                    company_data.get('growth_potential_score'),
                    datetime.utcnow()
                )
                return result is not None
        except Exception as e:
            logger.error(f"Failed to upsert company: {e}")
            return False
    
    async def get_companies_for_enrichment(self, 
                                         limit: int = 100,
                                         hours_since_enriched: int = 24) -> List[Dict]:
        """Get companies that need enrichment"""
        query = """
        SELECT uei, organization_name, state, last_enriched_at
        FROM companies
        WHERE last_enriched_at IS NULL 
           OR last_enriched_at < CURRENT_TIMESTAMP - INTERVAL '%s hours'
        ORDER BY 
            CASE WHEN last_enriched_at IS NULL THEN 0 ELSE 1 END,
            last_enriched_at ASC
        LIMIT %s
        """
        
        return await self.execute_query(query, (hours_since_enriched, limit))
    
    async def save_enrichment_result(self, 
                                   uei: str,
                                   source: str,
                                   status: str,
                                   data: Optional[Dict] = None,
                                   error: Optional[str] = None) -> bool:
        """Save enrichment result"""
        query = """
        INSERT INTO enrichment_history (uei, source, status, data, error_message)
        VALUES ($1, $2, $3, $4, $5)
        """
        
        try:
            async with self.get_asyncpg_connection() as conn:
                await conn.execute(
                    query,
                    uei,
                    source,
                    status,
                    json.dumps(data) if data else None,
                    error
                )
                return True
        except Exception as e:
            logger.error(f"Failed to save enrichment result: {e}")
            return False
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        queries = {
            'total_companies': "SELECT COUNT(*) as count FROM companies",
            'enriched_companies': """
                SELECT COUNT(*) as count FROM companies 
                WHERE last_enriched_at IS NOT NULL
            """,
            'top_states': """
                SELECT state, COUNT(*) as count 
                FROM companies 
                GROUP BY state 
                ORDER BY count DESC 
                LIMIT 10
            """,
            'grade_distribution': """
                SELECT business_health_grade, COUNT(*) as count 
                FROM companies 
                WHERE business_health_grade IS NOT NULL
                GROUP BY business_health_grade
            """,
            'avg_scores': """
                SELECT 
                    AVG(pe_investment_score) as avg_pe_score,
                    AVG(innovation_score) as avg_innovation_score,
                    AVG(growth_potential_score) as avg_growth_score
                FROM companies
            """
        }
        
        summary = {}
        
        for key, query in queries.items():
            result = await self.execute_query(query)
            if key in ['total_companies', 'enriched_companies']:
                summary[key] = result[0]['count'] if result else 0
            else:
                summary[key] = result
        
        return summary
    
    async def create_indexes(self):
        """Create optimized indexes for performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_companies_state ON companies(state)",
            "CREATE INDEX IF NOT EXISTS idx_companies_pe_score ON companies(pe_investment_score)",
            "CREATE INDEX IF NOT EXISTS idx_companies_health_grade ON companies(business_health_grade)",
            "CREATE INDEX IF NOT EXISTS idx_companies_enriched_at ON companies(last_enriched_at)",
            "CREATE INDEX IF NOT EXISTS idx_enrichment_uei_source ON enrichment_history(uei, source)",
            "CREATE INDEX IF NOT EXISTS idx_enrichment_created ON enrichment_history(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_companies_state_score ON companies(state, pe_investment_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_companies_search ON companies USING gin(to_tsvector('english', organization_name))"
        ]
        
        async with self.get_asyncpg_connection() as conn:
            for index in indexes:
                try:
                    await conn.execute(index)
                    logger.info(f"Created index: {index.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
    
    async def optimize_database(self):
        """Run database optimization tasks"""
        optimization_queries = [
            "VACUUM ANALYZE companies",
            "VACUUM ANALYZE enrichment_history",
            "REINDEX TABLE companies",
            "REINDEX TABLE enrichment_history"
        ]
        
        async with self.get_asyncpg_connection() as conn:
            for query in optimization_queries:
                try:
                    await conn.execute(query)
                    logger.info(f"Executed: {query}")
                except Exception as e:
                    logger.warning(f"Optimization warning: {e}")
    
    def migrate_from_sqlite(self, sqlite_path: str = 'kbi_production.db') -> int:
        """Migrate data from SQLite to PostgreSQL"""
        import sqlite3
        
        try:
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            # Read companies table
            df = pd.read_sql_query("SELECT * FROM companies", sqlite_conn)
            sqlite_conn.close()
            
            logger.info(f"Found {len(df)} companies to migrate")
            
            # Map columns
            column_mapping = {
                'uei': 'uei',
                'organization_name': 'organization_name',
                'city': 'city',
                'state': 'state',
                'zipcode': 'zipcode',
                'pe_investment_score': 'pe_investment_score',
                'business_health_grade': 'business_health_grade',
                'federal_contracts_value': 'federal_contracts_value',
                'patent_count': 'patent_count',
                'innovation_score': 'innovation_score',
                'growth_potential_score': 'growth_potential_score'
            }
            
            # Select and rename columns
            df_mapped = df[list(column_mapping.keys())].rename(columns=column_mapping)
            
            # Bulk insert
            rows_inserted = self.bulk_insert_dataframe(df_mapped, 'companies')
            
            logger.info(f"✅ Successfully migrated {rows_inserted} companies")
            return rows_inserted
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        health = {
            'status': 'unknown',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {}
        }
        
        try:
            # Check connection
            async with self.get_asyncpg_connection() as conn:
                version = await conn.fetchval('SELECT version()')
                health['details']['version'] = version.split(' ')[1]
                
                # Check table counts
                tables = ['companies', 'enrichment_history']
                for table in tables:
                    count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                    health['details'][f'{table}_count'] = count
                
                # Check database size
                size = await conn.fetchval("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
                health['details']['database_size'] = size
                
                # Check active connections
                active = await conn.fetchval("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                health['details']['active_connections'] = active
            
            health['status'] = 'healthy'
            
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health
    
    async def close(self):
        """Close all database connections"""
        if self.sync_engine:
            self.sync_engine.dispose()
        
        if self.async_engine:
            await self.async_engine.dispose()
        
        if self.connection_pool:
            self.connection_pool.closeall()
        
        if self.async_pool:
            await self.async_pool.close()
        
        logger.info("Database connections closed")


# Singleton instance
db_manager = DatabaseManager()


if __name__ == "__main__":
    async def test_database():
        """Test database functionality"""
        # Initialize
        await db_manager.initialize()
        
        # Run health check
        health = await db_manager.health_check()
        print("Health Check:", json.dumps(health, indent=2))
        
        # Create indexes
        await db_manager.create_indexes()
        
        # Get analytics summary
        summary = await db_manager.get_analytics_summary()
        print("Analytics Summary:", json.dumps(summary, indent=2))
        
        # Test upsert
        test_company = {
            'uei': 'TEST123456789',
            'organization_name': 'Test Corp Alpha',
            'city': 'San Francisco',
            'state': 'CA',
            'pe_investment_score': 85.5
        }
        
        success = await db_manager.upsert_company(test_company)
        print(f"Upsert test: {'✅ Success' if success else '❌ Failed'}")
        
        # Close connections
        await db_manager.close()
    
    # Run test
    asyncio.run(test_database())
