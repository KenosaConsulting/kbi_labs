#!/usr/bin/env python3
"""
Enhanced SMB Enrichment Pipeline with Real APIs
Integrates multiple data sources for comprehensive business intelligence
"""

import os
import asyncio
import aiohttp
import pandas as pd
from typing import Dict, Optional, List
from dataclasses import dataclass
import json
from datetime import datetime
import sqlite3
from dotenv import load_dotenv
import re
import time

# Load environment variables
load_dotenv()

@dataclass
class EnhancedSMB:
    """Enhanced SMB data with real API enrichments"""
    # Basic fields
    organization_name: str
    uei: str
    email: str
    state: str
    city: str
    address: str
    phone: str
    website: str
    naics_code: str
    
    # Google Places API
    google_place_id: Optional[str] = None
    google_rating: Optional[float] = None
    google_reviews_count: Optional[int] = None
    google_price_level: Optional[int] = None
    business_hours: Optional[Dict] = None
    google_categories: Optional[List[str]] = None
    
    # Clearbit Logo API
    company_logo_url: Optional[str] = None
    
    # Hunter.io Email Verification
    email_verified: Optional[bool] = None
    email_score: Optional[int] = None
    domain_extracted: Optional[str] = None
    
    # USPS Address Validation
    address_validated: Optional[bool] = None
    address_type: Optional[str] = None
    
    # Social Media Presence
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    
    # Calculated scores
    digital_presence_score: Optional[float] = None
    succession_risk_score: Optional[float] = None
    data_quality_score: Optional[float] = None
    estimated_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    
    # Metadata
    last_enriched: Optional[datetime] = None
    enrichment_sources: Optional[List[str]] = None

class RealAPIEnrichmentPipeline:
    """Production-ready enrichment pipeline with real APIs"""
    
    def __init__(self, db_path: str = "smb_intelligence_enhanced.db"):
        self.db_path = db_path
        self._init_database()
        
        # API Keys (set these in .env file)
        self.google_api_key = os.getenv('GOOGLE_PLACES_API_KEY', '')
        self.hunter_api_key = os.getenv('HUNTER_API_KEY', '')
        self.usps_user_id = os.getenv('USPS_USER_ID', '')
        
        # Rate limiting
        self.rate_limits = {
            'google_places': 100,  # per second
            'hunter': 15,  # per second
            'clearbit': 60,  # per minute
            'usps': 5  # per second
        }
        
    def _init_database(self):
        """Initialize enhanced database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enriched_smbs_v2 (
                uei TEXT PRIMARY KEY,
                organization_name TEXT NOT NULL,
                email TEXT,
                state TEXT,
                city TEXT,
                address TEXT,
                phone TEXT,
                website TEXT,
                naics_code TEXT,
                
                -- Google Places data
                google_place_id TEXT,
                google_rating REAL,
                google_reviews_count INTEGER,
                google_price_level INTEGER,
                business_hours TEXT,
                google_categories TEXT,
                
                -- Logo
                company_logo_url TEXT,
                
                -- Email verification
                email_verified BOOLEAN,
                email_score INTEGER,
                domain_extracted TEXT,
                
                -- Address validation
                address_validated BOOLEAN,
                address_type TEXT,
                
                -- Social media
                linkedin_url TEXT,
                facebook_url TEXT,
                twitter_handle TEXT,
                
                -- Calculated fields
                digital_presence_score REAL,
                succession_risk_score REAL,
                data_quality_score REAL,
                estimated_revenue REAL,
                employee_count INTEGER,
                
                -- Metadata
                last_enriched TIMESTAMP,
                enrichment_sources TEXT,
                raw_api_responses TEXT
            )
        ''')
        
        # Create indices for better query performance
        indices = [
            'CREATE INDEX IF NOT EXISTS idx_state_v2 ON enriched_smbs_v2(state)',
            'CREATE INDEX IF NOT EXISTS idx_risk_v2 ON enriched_smbs_v2(succession_risk_score)',
            'CREATE INDEX IF NOT EXISTS idx_revenue_v2 ON enriched_smbs_v2(estimated_revenue)',
            'CREATE INDEX IF NOT EXISTS idx_digital_v2 ON enriched_smbs_v2(digital_presence_score)'
        ]
        
        for idx in indices:
            cursor.execute(idx)
        
        conn.commit()
        conn.close()
    
    async def enrich_with_google_places(self, session: aiohttp.ClientSession, smb: EnhancedSMB) -> Dict:
        """Enrich with Google Places API data"""
        if not self.google_api_key:
            return {}
        
        try:
            # Search for the business
            search_query = f"{smb.organization_name} {smb.city} {smb.state}"
            search_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            
            params = {
                'input': search_query,
                'inputtype': 'textquery',
                'fields': 'place_id,name,rating,user_ratings_total,price_level,types',
                'key': self.google_api_key
            }
            
            async with session.get(search_url, params=params) as resp:
                data = await resp.json()
                
                if data.get('candidates'):
                    place = data['candidates'][0]
                    smb.google_place_id = place.get('place_id')
                    smb.google_rating = place.get('rating')
                    smb.google_reviews_count = place.get('user_ratings_total')
                    smb.google_price_level = place.get('price_level')
                    smb.google_categories = place.get('types', [])
                    
                    # Get detailed info
                    if smb.google_place_id:
                        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                        detail_params = {
                            'place_id': smb.google_place_id,
                            'fields': 'opening_hours,website,formatted_phone_number',
                            'key': self.google_api_key
                        }
                        
                        async with session.get(details_url, params=detail_params) as detail_resp:
                            detail_data = await detail_resp.json()
                            if detail_data.get('result'):
                                result = detail_data['result']
                                smb.business_hours = result.get('opening_hours', {})
                                if not smb.website and result.get('website'):
                                    smb.website = result['website']
                                if not smb.phone and result.get('formatted_phone_number'):
                                    smb.phone = result['formatted_phone_number']
                    
                    return {'google_places': 'success'}
                    
        except Exception as e:
            print(f"Google Places API error for {smb.organization_name}: {e}")
        
        return {'google_places': 'failed'}
    
    async def enrich_with_clearbit_logo(self, session: aiohttp.ClientSession, smb: EnhancedSMB) -> Dict:
        """Get company logo using Clearbit's free logo API"""
        try:
            # Extract domain from email or website
            domain = None
            if smb.website:
                domain = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', smb.website)
                domain = domain.group(1) if domain else None
            elif smb.email and '@' in smb.email:
                domain = smb.email.split('@')[1]
            
            if domain:
                # Clearbit logo API is free and doesn't require authentication
                logo_url = f"https://logo.clearbit.com/{domain}"
                
                # Check if logo exists
                async with session.head(logo_url) as resp:
                    if resp.status == 200:
                        smb.company_logo_url = logo_url
                        smb.domain_extracted = domain
                        return {'clearbit_logo': 'success'}
                        
        except Exception as e:
            print(f"Clearbit logo error for {smb.organization_name}: {e}")
        
        return {'clearbit_logo': 'failed'}
    
    async def verify_email_hunter(self, session: aiohttp.ClientSession, smb: EnhancedSMB) -> Dict:
        """Verify email using Hunter.io API"""
        if not self.hunter_api_key or not smb.email:
            return {}
        
        try:
            url = "https://api.hunter.io/v2/email-verifier"
            params = {
                'email': smb.email,
                'api_key': self.hunter_api_key
            }
            
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                
                if data.get('data'):
                    result = data['data']
                    smb.email_verified = result.get('status') == 'valid'
                    smb.email_score = result.get('score', 0)
                    
                    # Extract additional emails if available
                    if result.get('sources'):
                        # This would contain other emails found for the domain
                        pass
                    
                    return {'hunter_email': 'success'}
                    
        except Exception as e:
            print(f"Hunter.io error for {smb.email}: {e}")
        
        return {'hunter_email': 'failed'}
    
    async def validate_address_usps(self, session: aiohttp.ClientSession, smb: EnhancedSMB) -> Dict:
        """Validate address using USPS API"""
        if not self.usps_user_id or not smb.address:
            return {}
        
        try:
            # USPS API requires XML format
            xml_request = f'''
            <AddressValidateRequest USERID="{self.usps_user_id}">
                <Revision>1</Revision>
                <Address ID="0">
                    <Address1>{smb.address}</Address1>
                    <Address2></Address2>
                    <City>{smb.city}</City>
                    <State>{smb.state}</State>
                    <Zip5></Zip5>
                    <Zip4></Zip4>
                </Address>
            </AddressValidateRequest>
            '''
            
            url = "https://secure.shippingapis.com/ShippingAPI.dll"
            params = {
                'API': 'Verify',
                'XML': xml_request
            }
            
            async with session.get(url, params=params) as resp:
                # Parse XML response (simplified)
                response_text = await resp.text()
                if 'Error' not in response_text:
                    smb.address_validated = True
                    smb.address_type = 'Commercial'  # Would parse from response
                    return {'usps_address': 'success'}
                    
        except Exception as e:
            print(f"USPS API error for {smb.address}: {e}")
        
        return {'usps_address': 'failed'}
    
    def calculate_enhanced_scores(self, smb: EnhancedSMB) -> None:
        """Calculate comprehensive scores based on all enrichment data"""
        
        # Digital Presence Score (0-10)
        digital_score = 0.0
        
        # Website and email
        if smb.website:
            digital_score += 1.5
        if smb.email_verified:
            digital_score += 1.5
        elif smb.email:
            digital_score += 0.5
            
        # Google presence
        if smb.google_rating:
            if smb.google_rating >= 4.0:
                digital_score += 2.0
            else:
                digital_score += 1.0
                
        if smb.google_reviews_count:
            if smb.google_reviews_count > 100:
                digital_score += 2.0
            elif smb.google_reviews_count > 25:
                digital_score += 1.0
            else:
                digital_score += 0.5
                
        # Social media
        if smb.linkedin_url:
            digital_score += 1.0
        if smb.facebook_url:
            digital_score += 0.5
        if smb.company_logo_url:
            digital_score += 0.5
            
        smb.digital_presence_score = min(digital_score, 10.0)
        
        # Data Quality Score (0-10)
        quality_score = 0.0
        fields_checked = [
            smb.email_verified, smb.address_validated, smb.phone,
            smb.website, smb.google_place_id, smb.company_logo_url
        ]
        quality_score = sum(1.67 for field in fields_checked if field) 
        smb.data_quality_score = min(quality_score, 10.0)
        
        # Enhanced Succession Risk Score (0-10)
        risk_score = 5.0  # Base score
        
        # Digital presence factor (inverse relationship)
        if smb.digital_presence_score < 3.0:
            risk_score += 2.0
        elif smb.digital_presence_score < 5.0:
            risk_score += 1.0
            
        # Industry factors
        high_risk_naics = ['23', '48', '81', '44']  # Construction, Transport, Repair, Retail
        if any(smb.naics_code.startswith(code) for code in high_risk_naics):
            risk_score += 1.5
            
        # Google reviews as proxy for business stability
        if smb.google_reviews_count and smb.google_reviews_count < 10:
            risk_score += 0.5
            
        # No website is a strong indicator
        if not smb.website:
            risk_score += 1.0
            
        smb.succession_risk_score = min(risk_score, 10.0)
        
        # Revenue estimation based on enhanced data
        base_revenue = 1000000  # $1M base
        
        # Industry multipliers
        industry_multipliers = {
            '23': 2.5,  # Construction
            '31': 5.0,  # Manufacturing  
            '54': 1.5,  # Professional Services
            '62': 3.0,  # Healthcare
        }
        
        for code, mult in industry_multipliers.items():
            if smb.naics_code.startswith(code):
                base_revenue *= mult
                break
                
        # Adjust by digital presence
        if smb.digital_presence_score > 7:
            base_revenue *= 1.5
        elif smb.digital_presence_score > 5:
            base_revenue *= 1.2
            
        # Adjust by location
        high_value_states = ['CA', 'NY', 'TX', 'FL']
        if smb.state in high_value_states:
            base_revenue *= 1.3
            
        smb.estimated_revenue = base_revenue
        smb.employee_count = int(base_revenue / 150000)
    
    async def enrich_single_smb(self, session: aiohttp.ClientSession, smb_data: Dict) -> EnhancedSMB:
        """Enrich a single SMB with all available APIs"""
        
        # Create EnhancedSMB object
        smb = EnhancedSMB(
            organization_name=smb_data.get('Organization Name', ''),
            uei=smb_data.get('UEI (Unique Entity Identifier)', ''),
            email=smb_data.get('Email', ''),
            state=smb_data.get('State', ''),
            city=smb_data.get('City', ''),
            address=smb_data.get('Address line 1', ''),
            phone=str(smb_data.get('Phone number', '')),
            website=smb_data.get('Website', ''),
            naics_code=str(smb_data.get('Primary NAICS code', ''))
        )
        
        # Track which enrichments were used
        enrichment_results = {}
        
        # Run all enrichments in parallel
        tasks = [
            self.enrich_with_google_places(session, smb),
            self.enrich_with_clearbit_logo(session, smb),
            self.verify_email_hunter(session, smb),
            self.validate_address_usps(session, smb)
        ]
        
        results = await asyncio.gather(*tasks)
        for result in results:
            enrichment_results.update(result)
        
        # Calculate scores based on enriched data
        self.calculate_enhanced_scores(smb)
        
        # Set metadata
        smb.last_enriched = datetime.now()
        smb.enrichment_sources = [k for k, v in enrichment_results.items() if v == 'success']
        
        return smb
    
    async def enrich_batch(self, smbs: List[Dict], batch_size: int = 10):
        """Enrich a batch of SMBs with rate limiting"""
        print(f"\n🚀 Starting enhanced enrichment for {len(smbs)} businesses...")
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(smbs), batch_size):
                batch = smbs[i:i+batch_size]
                
                # Process batch
                tasks = [self.enrich_single_smb(session, smb) for smb in batch]
                enriched_smbs = await asyncio.gather(*tasks)
                
                # Save to database
                self._save_batch(enriched_smbs)
                
                print(f"✅ Enriched {i+len(batch)}/{len(smbs)} businesses")
                
                # Rate limiting pause
                await asyncio.sleep(1)
    
    def _save_batch(self, enriched_smbs: List[EnhancedSMB]):
        """Save enriched SMBs to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for smb in enriched_smbs:
            cursor.execute('''
                INSERT OR REPLACE INTO enriched_smbs_v2 VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                smb.uei, smb.organization_name, smb.email, smb.state, smb.city,
                smb.address, smb.phone, smb.website, smb.naics_code,
                smb.google_place_id, smb.google_rating, smb.google_reviews_count,
                smb.google_price_level, json.dumps(smb.business_hours) if smb.business_hours else None,
                json.dumps(smb.google_categories) if smb.google_categories else None,
                smb.company_logo_url, smb.email_verified, smb.email_score,
                smb.domain_extracted, smb.address_validated, smb.address_type,
                smb.linkedin_url, smb.facebook_url, smb.twitter_handle,
                smb.digital_presence_score, smb.succession_risk_score,
                smb.data_quality_score, smb.estimated_revenue, smb.employee_count,
                smb.last_enriched, json.dumps(smb.enrichment_sources) if smb.enrichment_sources else None,
                json.dumps({})  # raw_api_responses
            ))
        
        conn.commit()
        conn.close()

# Usage example
async def main():
    # Create .env file first
    env_content = '''# API Keys for SMB Enrichment
GOOGLE_PLACES_API_KEY=your_google_api_key_here
HUNTER_API_KEY=your_hunter_api_key_here
USPS_USER_ID=your_usps_user_id_here
'''
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✏️  Created .env file - please add your API keys!")
        return
    
    # Load data
    df = pd.read_csv('data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv')
    
    # Start with a small sample for testing
    sample_size = 100
    sample_data = df.head(sample_size).to_dict('records')
    
    # Initialize pipeline
    pipeline = RealAPIEnrichmentPipeline()
    
    # Run enrichment
    await pipeline.enrich_batch(sample_data)
    
    # Show results
    conn = sqlite3.connect('smb_intelligence_enhanced.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) as total,
               AVG(digital_presence_score) as avg_digital,
               AVG(succession_risk_score) as avg_risk,
               AVG(data_quality_score) as avg_quality,
               COUNT(CASE WHEN google_rating IS NOT NULL THEN 1 END) as with_google,
               COUNT(CASE WHEN email_verified = 1 THEN 1 END) as verified_emails,
               COUNT(CASE WHEN company_logo_url IS NOT NULL THEN 1 END) as with_logos
        FROM enriched_smbs_v2
    ''')
    
    stats = cursor.fetchone()
    print(f"\n📊 Enrichment Results:")
    print(f"  Total enriched: {stats[0]}")
    print(f"  Avg digital presence: {stats[1]:.1f}/10")
    print(f"  Avg succession risk: {stats[2]:.1f}/10")
    print(f"  Avg data quality: {stats[3]:.1f}/10")
    print(f"  With Google data: {stats[4]}")
    print(f"  Verified emails: {stats[5]}")
    print(f"  With logos: {stats[6]}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
