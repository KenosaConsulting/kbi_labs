
#!/usr/bin/env python3
"""
Fix dashboard display issues
"""

import json
import re

def fix_companies_json():
    """Fix the companies.json to ensure all fields are properly formatted"""
    
    print("🔧 Fixing companies.json format...")
    
    # Load current companies
    with open('companies.json', 'r') as f:
        companies = json.load(f)
    
    print(f"📊 Processing {len(companies)} companies...")
    
    # Fix each company
    for i, company in enumerate(companies):
        # Ensure company_name is set
        if not company.get('company_name') or company['company_name'] == 'undefined':
            company['company_name'] = company.get('organization_name', f'Company {i+1}')
        
        # Clean up UEI - remove any dashes or special characters for consistency
        if company.get('uei'):
            company['uei'] = company['uei'].replace('-', '').strip()
        
        # Ensure all required fields exist
        company['pe_investment_score'] = float(company.get('pe_investment_score', 75))
        company['federal_contracts_value'] = int(company.get('federal_contracts_value', 0))
        company['patent_count'] = int(company.get('patent_count', 0))
        company['business_health_grade'] = company.get('business_health_grade', 'B')
        company['state'] = company.get('state', 'Unknown')
        company['city'] = company.get('city', 'Unknown')
        
        # Add display name for the table
        company['display_name'] = company['company_name']
    
    # Save fixed companies
    with open('companies.json', 'w') as f:
        json.dump(companies, f, indent=2)
    
    print(f"✅ Fixed {len(companies)} companies")
    
    # Show sample
    if companies:
        print("\n📋 Sample fixed company:")
        sample = companies[0]
        print(f"  Name: {sample['company_name']}")
        print(f"  UEI: {sample['uei']}")
        print(f"  Score: {sample['pe_investment_score']}")

def create_portfolio_fix():
    """Create a fix for the portfolio.html to display company names correctly"""
    
    fix_js = """
    // Fix for company name display
    function updatePortfolioTable() {
        fetch('/api/companies')
            .then(response => response.json())
            .then(companies => {
                const tbody = document.getElementById('topCompaniesTable');
                if (!tbody) return;
                
                tbody.innerHTML = '';
                
                // Sort by score and take top companies
                companies.sort((a, b) => (b.pe_investment_score || 0) - (a.pe_investment_score || 0));
                
                companies.slice(0, 25).forEach(company => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm font-medium text-gray-900">
                                ${company.company_name || company.organization_name || 'Unknown Company'}
                            </div>
                            <div class="text-sm text-gray-500">${company.uei || 'No UEI'}</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm text-gray-900">${company.city || 'Unknown'}, ${company.state || 'Unknown'}</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                ${company.pe_investment_score || 0}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            ${company.business_health_grade || 'N/A'}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            ${company.patent_count || 0}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            $${((company.federal_contracts_value || 0) / 1000000).toFixed(2)}M
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <a href="company-details.html?uei=${encodeURIComponent(company.uei || '')}" 
                               class="text-indigo-600 hover:text-indigo-900">View Details</a>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            })
            .catch(error => console.error('Error loading companies:', error));
    }
    
    // Call the fix on page load
    document.addEventListener('DOMContentLoaded', updatePortfolioTable);
    """
    
    print("\n📝 Portfolio display fix created")
    print("Add this script to your portfolio.html before the closing </body> tag:")
    print("-" * 50)
    print(fix_js)
    print("-" * 50)

def check_ai_service():
    """Check and provide fix for AI service"""
    
    print("\n🤖 Checking AI service...")
    
    import requests
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=2)
        if response.status_code == 200:
            print("✅ AI service is running on port 5001")
        else:
            print(f"⚠️  AI service returned status {response.status_code}")
    except:
        print("❌ AI service not responding")
        print("\n🔧 To fix AI insights:")
        print("   1. cd ~/KBILabs/ai_insights")
        print("   2. pkill -f enhanced_insights_api")
        print("   3. python3 enhanced_insights_api_fixed.py &")
        print("\n   Or disable AI loading indicator:")
        print("   Edit company-details.html and remove the 'GPT-4 is analyzing' message")

def main():
    print("🚀 KBI Labs Dashboard Fix")
    print("=" * 50)
    
    # Fix companies.json
    fix_companies_json()
    
    # Create portfolio fix
    create_portfolio_fix()
    
    # Check AI service
    check_ai_service()
    
    print("\n✅ Fixes complete!")
    print("\n🔄 Restart the server to apply changes:")
    print("   pkill -f combined_server")
    print("   python3 combined_server_v2.py &")

if __name__ == "__main__":
    main()
