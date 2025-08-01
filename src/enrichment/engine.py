import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

from .config import EnrichmentConfig
from .models import EnrichedCompany, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnrichmentEngine:
    def __init__(self):
        self.config = EnrichmentConfig()
        # Use SQLite
        if "sqlite" in self.config.DATABASE_URL:
            self.engine = create_engine(
                self.config.DATABASE_URL, 
                connect_args={"check_same_thread": False}
            )
        else:
            self.engine = create_engine(self.config.DATABASE_URL)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        
        self.Session = sessionmaker(bind=self.engine)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        
    async def enrich_company(self, company_data: Dict) -> Dict:
        """Main enrichment orchestrator"""
        uei = company_data.get('UEI (Unique Entity Identifier)')
        logger.info(f"Starting enrichment for {uei}")
        
        enriched_data = {
            'uei': uei,
            'organization_name': company_data.get('Organization Name'),
            'primary_naics': str(company_data.get('Primary NAICS code', '')),
            'state': company_data.get('State'),
            'city': company_data.get('City'),
            'website': company_data.get('Website'),
            'phone_number': str(company_data.get('Phone number', '')),
            'enrichment_status': {}
        }
        
        # Calculate basic scores for now
        self.calculate_risk_scores(enriched_data)
        self.calculate_growth_indicators(enriched_data)
        self.calculate_final_scores(enriched_data)
        
        enriched_data['last_enriched'] = datetime.utcnow()
        enriched_data['enrichment_version'] = '1.0'
        
        return enriched_data
    
    def calculate_risk_scores(self, company: Dict):
        """Calculate various risk metrics"""
        # Simplified scoring
        company['succession_risk_score'] = 5.0
        company['financial_risk_score'] = 5.0
        company['operational_risk_score'] = 5.0
        company['overall_risk_rating'] = 'MEDIUM'
    
    def calculate_growth_indicators(self, company: Dict):
        """Calculate growth potential"""
        company['growth_potential_score'] = 5.0
        company['acquisition_readiness'] = 5.0
    
    def calculate_final_scores(self, company: Dict):
        """Calculate PE investment score and business health grade"""
        company['pe_investment_score'] = 50.0
        company['business_health_grade'] = 'B'
        company['peer_percentile'] = 50.0
        company['key_recommendations'] = []

async def process_csv_batch(csv_file: str, batch_size: int = 100):
    """Process a CSV file in batches"""
    logger.info(f"Processing {csv_file}")
    
    df = pd.read_csv(csv_file)
    total_rows = len(df)
    
    async with EnrichmentEngine() as engine:
        db_session = engine.Session()
        
        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            batch = df.iloc[start_idx:end_idx]
            
            logger.info(f"Processing batch {start_idx//batch_size + 1} ({start_idx}-{end_idx} of {total_rows})")
            
            for _, row in batch.iterrows():
                company_data = row.to_dict()
                try:
                    enriched = await engine.enrich_company(company_data)
                    
                    # Save to database
                    db_company = db_session.query(EnrichedCompany).filter_by(
                        uei=enriched['uei']
                    ).first()
                    
                    if not db_company:
                        db_company = EnrichedCompany()
                    
                    # Update fields
                    for key, value in enriched.items():
                        if hasattr(db_company, key):
                            setattr(db_company, key, value)
                    
                    db_session.add(db_company)
                    
                except Exception as e:
                    logger.error(f"Error processing company {company_data.get('UEI (Unique Entity Identifier)')}: {e}")
            
            # Commit the batch
            try:
                db_session.commit()
                logger.info(f"Batch {start_idx//batch_size + 1} committed successfully")
            except Exception as e:
                logger.error(f"Error committing batch: {e}")
                db_session.rollback()
            
            # Rate limiting between batches
            await asyncio.sleep(1)
        
        db_session.close()
