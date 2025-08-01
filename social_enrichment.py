#!/usr/bin/env python3
"""
Social Media Enrichment Layer
Finds Facebook, LinkedIn, and other social profiles for SMBs
"""

import asyncio
import aiohttp
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import time

class SocialMediaEnricher:
    """Find social media profiles without APIs"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    async def find_facebook(self, session: aiohttp.ClientSession, business_name: str, city: str, state: str) -> dict:
        """Search for Facebook business page"""
        try:
            # Search Google for Facebook page
            search_query = f'site:facebook.com "{business_name}" {city} {state}'
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            
            async with session.get(search_url, headers=self.headers) as resp:
                html = await resp.text()
                
                # Look for Facebook URLs in results
                fb_pattern = r'facebook\.com/[^/\s"]+(?:/[^/\s"]+)?'
                matches = re.findall(fb_pattern, html)
                
                if matches:
                    fb_url = f"https://{matches[0]}"
                    
                    # Try to get page info
                    async with session.get(fb_url, headers=self.headers) as fb_resp:
                        if fb_resp.status == 200:
                            fb_html = await fb_resp.text()
                            
                            # Extract likes/followers count
                            likes_pattern = r'(\d+(?:,\d+)*)\s*(?:people like this|likes|followers)'
                            likes_match = re.search(likes_pattern, fb_html, re.IGNORECASE)
                            
                            likes_count = 0
                            if likes_match:
                                likes_count = int(likes_match.group(1).replace(',', ''))
                            
                            return {
                                'facebook_url': fb_url,
                                'facebook_likes': likes_count,
                                'has_facebook': True
                            }
                            
        except Exception as e:
            print(f"Facebook search error for {business_name}: {e}")
            
        return {'has_facebook': False}
    
    async def find_linkedin(self, session: aiohttp.ClientSession, business_name: str) -> dict:
        """Search for LinkedIn company page"""
        try:
            # Search for LinkedIn company page
            search_query = f'site:linkedin.com/company "{business_name}"'
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            
            async with session.get(search_url, headers=self.headers) as resp:
                html = await resp.text()
                
                # Look for LinkedIn company URLs
                li_pattern = r'linkedin\.com/company/[^/\s"]+(?:/[^/\s"]+)?'
                matches = re.findall(li_pattern, html)
                
                if matches:
                    linkedin_url = f"https://{matches[0]}"
                    
                    return {
                        'linkedin_url': linkedin_url,
                        'has_linkedin': True
                    }
                    
        except Exception as e:
            print(f"LinkedIn search error for {business_name}: {e}")
            
        return {'has_linkedin': False}
    
    async def find_yelp(self, session: aiohttp.ClientSession, business_name: str, city: str, state: str) -> dict:
        """Search for Yelp listing"""
        try:
            # Search Yelp directly
            search_url = "https://www.yelp.com/search"
            params = {
                'find_desc': business_name,
                'find_loc': f"{city}, {state}"
            }
            
            async with session.get(search_url, params=params, headers=self.headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for first business result
                    biz_name = soup.find('a', {'name': business_name.lower()})
                    if biz_name:
                        # Extract rating
                        rating_elem = soup.find('div', {'role': 'img', 'aria-label': re.compile(r'rating')})
                        if rating_elem:
                            rating_match = re.search(r'(\d+\.?\d*)\s*star', rating_elem.get('aria-label', ''))
                            if rating_match:
                                return {
                                    'yelp_rating': float(rating_match.group(1)),
                                    'has_yelp': True
                                }
                                
        except Exception as e:
            print(f"Yelp search error for {business_name}: {e}")
            
        return {'has_yelp': False}
    
    async def check_bbb(self, session: aiohttp.ClientSession, business_name: str, state: str) -> dict:
        """Check Better Business Bureau"""
        try:
            # Search BBB
            search_query = f'site:bbb.org "{business_name}" {state}'
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            
            async with session.get(search_url, headers=self.headers) as resp:
                html = await resp.text()
                
                # Check if BBB profile exists
                if 'bbb.org/us/' in html:
                    # Extract rating if visible
                    rating_pattern = r'BBB Rating:\s*([A-F]\+?)'
                    rating_match = re.search(rating_pattern, html)
                    
                    return {
                        'has_bbb': True,
                        'bbb_rating': rating_match.group(1) if rating_match else None
                    }
                    
        except Exception as e:
            print(f"BBB search error for {business_name}: {e}")
            
        return {'has_bbb': False}

async def enrich_with_social(smb_data: dict) -> dict:
    """Add social media data to SMB"""
    enricher = SocialMediaEnricher()
    
    async with aiohttp.ClientSession() as session:
        # Run all social searches in parallel
        tasks = [
            enricher.find_facebook(session, smb_data['organization_name'], smb_data['city'], smb_data['state']),
            enricher.find_linkedin(session, smb_data['organization_name']),
            enricher.find_yelp(session, smb_data['organization_name'], smb_data['city'], smb_data['state']),
            enricher.check_bbb(session, smb_data['organization_name'], smb_data['state'])
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Combine all results
        social_data = {}
        for result in results:
            social_data.update(result)
            
        # Calculate social presence score
        social_score = 0
        if social_data.get('has_facebook'):
            social_score += 3
            if social_data.get('facebook_likes', 0) > 100:
                social_score += 1
        if social_data.get('has_linkedin'):
            social_score += 3
        if social_data.get('has_yelp'):
            social_score += 2
        if social_data.get('has_bbb'):
            social_score += 2
            
        social_data['social_presence_score'] = min(social_score, 10)
        
        # Add delay to avoid rate limiting
        await asyncio.sleep(0.5)
        
        return social_data

# Integration with your existing pipeline
async def enhance_smb_with_social(smb_record: dict):
    """Add this to your existing enrichment pipeline"""
    
    print(f"🔍 Searching social media for {smb_record['Organization Name']}...")
    
    social_data = await enrich_with_social({
        'organization_name': smb_record['Organization Name'],
        'city': smb_record.get('City', ''),
        'state': smb_record.get('State', '')
    })
    
    # Update succession risk based on social presence
    if social_data['social_presence_score'] < 3:
        # No social media = higher succession risk
        risk_adjustment = 1.5
    else:
        risk_adjustment = 0
        
    return {
        **smb_record,
        **social_data,
        'succession_risk_adjustment': risk_adjustment
    }

# Test it
async def test_social_enrichment():
    test_business = {
        'Organization Name': 'Starbucks',
        'City': 'Seattle',
        'State': 'WA'
    }
    
    result = await enhance_smb_with_social(test_business)
    print("\n📱 Social Media Results:")
    for key, value in result.items():
        if 'has_' in key or 'facebook' in key or 'linkedin' in key:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_social_enrichment())
