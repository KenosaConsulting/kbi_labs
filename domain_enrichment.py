#!/usr/bin/env python3
"""
Domain & Website Analysis Enrichment
Extracts domain from email, checks website status, technology stack
"""

import asyncio
import aiohttp
import re
import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse
import dns.resolver
import whois

class DomainEnricher:
    """Enrich SMBs with domain and website intelligence"""
    
    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=5)
        
    async def extract_domain(self, email: str, website: str = None) -> str:
        """Extract domain from email or website"""
        if website:
            # Clean up website URL
            if not website.startswith(('http://', 'https://')):
                website = f'http://{website}'
            parsed = urlparse(website)
            return parsed.netloc.replace('www.', '')
        elif email and '@' in email:
            return email.split('@')[1].lower()
        return None
    
    async def check_website_status(self, session: aiohttp.ClientSession, domain: str) -> dict:
        """Check if website is live and get basic info"""
        results = {
            'website_status': 'unknown',
            'website_title': None,
            'has_ssl': False,
            'response_time': None,
            'technology_signals': []
        }
        
        for protocol in ['https', 'http']:
            try:
                url = f'{protocol}://{domain}'
                start_time = datetime.now()
                
                async with session.get(url, timeout=self.timeout, allow_redirects=True) as resp:
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if resp.status == 200:
                        results['website_status'] = 'active'
                        results['has_ssl'] = protocol == 'https'
                        results['response_time'] = response_time
                        results['final_url'] = str(resp.url)
                        
                        # Get page content
                        html = await resp.text()
                        
                        # Extract title
                        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
                        if title_match:
                            results['website_title'] = title_match.group(1).strip()[:100]
                        
                        # Detect technology signals
                        tech_signals = []
                        
                        # WordPress
                        if 'wp-content' in html or 'wordpress' in html.lower():
                            tech_signals.append('WordPress')
                            
                        # Shopify
                        if 'shopify' in html.lower() or 'myshopify.com' in html:
                            tech_signals.append('Shopify')
                            
                        # Wix
                        if 'wix.com' in html or 'wixstatic.com' in html:
                            tech_signals.append('Wix')
                            
                        # SquareSpace
                        if 'squarespace' in html.lower():
                            tech_signals.append('SquareSpace')
                            
                        # GoDaddy Website Builder
                        if 'godaddy' in html.lower() and 'website builder' in html.lower():
                            tech_signals.append('GoDaddy Builder')
                            
                        # Google Analytics
                        if 'google-analytics.com' in html or 'gtag(' in html:
                            tech_signals.append('Google Analytics')
                            
                        # Facebook Pixel
                        if 'facebook.com/tr' in html or 'fbq(' in html:
                            tech_signals.append('Facebook Pixel')
                            
                        results['technology_signals'] = tech_signals
                        
                        # Check for contact info
                        results['has_phone_on_site'] = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', html))
                        results['has_email_on_site'] = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', html))
                        
                        return results
                        
            except asyncio.TimeoutError:
                results['website_status'] = 'timeout'
            except Exception as e:
                continue
                
        return results
    
    async def check_domain_age(self, domain: str) -> dict:
        """Get domain registration age"""
        try:
            w = whois.whois(domain)
            
            if w.creation_date:
                # Handle both single date and list of dates
                creation_date = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
                
                if isinstance(creation_date, datetime):
                    age_days = (datetime.now() - creation_date).days
                    age_years = age_days / 365.25
                    
                    return {
                        'domain_created': creation_date.isoformat(),
                        'domain_age_years': round(age_years, 1),
                        'domain_registrar': w.registrar if hasattr(w, 'registrar') else None
                    }
                    
        except Exception as e:
            pass
            
        return {
            'domain_age_years': None,
            'domain_registrar': None
        }
    
    async def check_email_domain(self, domain: str) -> dict:
        """Check if domain has valid MX records (can receive email)"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            
            return {
                'has_mx_records': True,
                'email_provider': self._identify_email_provider(mx_records)
            }
        except:
            return {
                'has_mx_records': False,
                'email_provider': None
            }
    
    def _identify_email_provider(self, mx_records) -> str:
        """Identify email provider from MX records"""
        mx_strings = [str(r.exchange).lower() for r in mx_records]
        
        if any('google' in mx or 'googlemail' in mx for mx in mx_strings):
            return 'Google Workspace'
        elif any('outlook' in mx or 'microsoft' in mx for mx in mx_strings):
            return 'Microsoft 365'
        elif any('godaddy' in mx for mx in mx_strings):
            return 'GoDaddy'
        elif any('zoho' in mx for mx in mx_strings):
            return 'Zoho'
        else:
            return 'Other/Custom'
    
    def calculate_digital_maturity_score(self, results: dict) -> float:
        """Calculate digital maturity based on domain/website analysis"""
        score = 0.0
        
        # Website factors
        if results.get('website_status') == 'active':
            score += 2.0
            
            if results.get('has_ssl'):
                score += 1.0
                
            if results.get('response_time', 999) < 2.0:
                score += 0.5
                
            # Technology adoption
            tech_count = len(results.get('technology_signals', []))
            if tech_count >= 3:
                score += 2.0
            elif tech_count >= 1:
                score += 1.0
                
            # Professional website (not DIY)
            diy_platforms = ['Wix', 'SquareSpace', 'GoDaddy Builder']
            if not any(platform in results.get('technology_signals', []) for platform in diy_platforms):
                score += 1.0
                
        # Domain age
        domain_age = results.get('domain_age_years', 0)
        if domain_age:
            if domain_age > 10:
                score += 1.5
            elif domain_age > 5:
                score += 1.0
            elif domain_age > 2:
                score += 0.5
                
        # Email setup
        if results.get('has_mx_records'):
            score += 1.0
            if results.get('email_provider') in ['Google Workspace', 'Microsoft 365']:
                score += 0.5
                
        return min(score, 10.0)

async def enrich_smb_with_domain(smb_data: dict) -> dict:
    """Main enrichment function"""
    enricher = DomainEnricher()
    
    # Extract domain
    domain = await enricher.extract_domain(
        smb_data.get('Email', ''),
        smb_data.get('Website', '')
    )
    
    if not domain:
        return {
            'domain': None,
            'website_status': 'no_domain',
            'digital_maturity_score': 0.0
        }
    
    results = {'domain': domain}
    
    async with aiohttp.ClientSession() as session:
        # Check website
        website_data = await enricher.check_website_status(session, domain)
        results.update(website_data)
    
    # Check domain age
    domain_data = await enricher.check_domain_age(domain)
    results.update(domain_data)
    
    # Check email setup
    email_data = await enricher.check_email_domain(domain)
    results.update(email_data)
    
    # Calculate maturity score
    results['digital_maturity_score'] = enricher.calculate_digital_maturity_score(results)
    
    # Succession risk factors
    risk_factors = []
    if results.get('website_status') != 'active':
        risk_factors.append('no_active_website')
    if not results.get('has_ssl'):
        risk_factors.append('no_ssl')
    if (results.get('domain_age_years') or 0) < 3:
        risk_factors.append('new_domain')
    if not results.get('has_mx_records'):
        risk_factors.append('no_business_email')
    if 'Wix' in results.get('technology_signals', []) or 'GoDaddy Builder' in results.get('technology_signals', []):
        risk_factors.append('diy_website')
        
    results['succession_risk_factors'] = risk_factors
    results['domain_succession_risk_adjustment'] = len(risk_factors) * 0.5
    
    return results

# Test function
async def test_domain_enrichment():
    # Test with a known business
    test_cases = [
        {
            'Organization Name': 'Example Company',
            'Email': 'info@microsoft.com',
            'Website': 'microsoft.com'
        },
        {
            'Organization Name': 'Small Business',
            'Email': 'contact@example-small-biz.com',
            'Website': ''
        }
    ]
    
    for test_data in test_cases:
        print(f"\n🔍 Analyzing domain for {test_data['Organization Name']}...")
        result = await enrich_smb_with_domain(test_data)
        
        print(f"  Domain: {result.get('domain')}")
        print(f"  Website Status: {result.get('website_status')}")
        print(f"  Has SSL: {result.get('has_ssl')}")
        print(f"  Domain Age: {result.get('domain_age_years')} years")
        print(f"  Technology: {', '.join(result.get('technology_signals', []))}")
        print(f"  Digital Maturity Score: {result.get('digital_maturity_score')}/10")
        print(f"  Risk Factors: {', '.join(result.get('succession_risk_factors', []))}")

if __name__ == "__main__":
    # Install required packages first
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip3", "install", "dnspython", "python-whois"], check=True)
    
    asyncio.run(test_domain_enrichment())
