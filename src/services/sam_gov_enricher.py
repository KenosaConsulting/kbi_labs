#!/usr/bin/env python3
"""
SAM.gov API integration for KBI Labs
"""
import aiohttp
import asyncio
from typing import Dict, Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class SAMGovEnricher:
    def __init__(self):
        self.api_key = os.getenv('SAM_GOV_API_KEY', 'demo_key')
        self.base_url = "https://api.sam.gov/entity-information/v3"
        self.session = None
    
    async def setup(self):
        """Initialize aiohttp session"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def cleanup(self):
        """Close session"""
        if self.session:
            await self.session.close()
    
    async def get_entity_info(self, uei: str) -> Dict:
        """Get entity information from SAM.gov"""
        if not uei or not self.session:
            return {}
        
        try:
            url = f"{self.base_url}/entities/{uei}"
            headers = {'X-Api-Key': self.api_key}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract key information
                    entity = data.get('entityData', [{}])[0] if data.get('entityData') else {}
                    registration = entity.get('entityRegistration', {})
                    core_data = entity.get('coreData', {})
                    
                    return {
                        'sam_registration_status': registration.get('registrationStatus', 'NOT_REGISTERED'),
                        'sam_registration_date': registration.get('registrationDate'),
                        'sam_expiration_date': registration.get('expirationDate'),
                        'cage_code': entity.get('cageCode'),
                        'legal_business_name': core_data.get('legalBusinessName'),
                        'dba_name': core_data.get('dbaName'),
                        'entity_structure': core_data.get('entityStructureDesc'),
                        'state_of_incorporation': core_data.get('stateOfIncorporationCode'),
                        'sam_extracted_on': data.get('extractedOn')
                    }
                elif response.status == 404:
                    logger.info(f"Entity not found in SAM.gov: {uei}")
                    return {'sam_registration_status': 'NOT_FOUND'}
                else:
                    logger.warning(f"SAM.gov API error: {response.status}")
                    return {'sam_registration_status': 'ERROR'}
                    
        except Exception as e:
            logger.error(f"Error fetching SAM.gov data for {uei}: {e}")
            return {'sam_registration_status': 'ERROR'}

async def test_sam_enricher():
    """Test the SAM.gov enricher"""
    enricher = SAMGovEnricher()
    await enricher.setup()
    
    # Test with a known UEI (you would need a real one)
    test_uei = "ZQGGHJH74DW7"  # Example UEI
    
    print(f"Testing SAM.gov API with UEI: {test_uei}")
    result = await enricher.get_entity_info(test_uei)
    
    print("\nResult:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    await enricher.cleanup()

if __name__ == "__main__":
    asyncio.run(test_sam_enricher())
