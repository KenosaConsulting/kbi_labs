// Fix for portfolio table loading
(function() {
    let attempts = 0;
    const maxAttempts = 10;
    
    function tryLoadTable() {
        const tbody = document.getElementById('topCompaniesTable');
        
        if (!tbody) {
            console.log('Table body not found, attempt', attempts);
            if (attempts < maxAttempts) {
                attempts++;
                setTimeout(tryLoadTable, 500);
            }
            return;
        }
        
        console.log('Loading portfolio table...');
        
        fetch('/api/companies')
            .then(response => response.json())
            .then(companies => {
                console.log(`Loaded ${companies.length} companies`);
                
                // Clear any existing content
                tbody.innerHTML = '';
                
                // Sort by score
                companies.sort((a, b) => (b.pe_investment_score || 0) - (a.pe_investment_score || 0));
                
                // Add rows
                companies.slice(0, 25).forEach((company, index) => {
                    const row = tbody.insertRow();
                    row.className = 'hover:bg-gray-50';
                    row.innerHTML = `
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm font-medium text-gray-900">${company.company_name || 'Unknown'}</div>
                            <div class="text-sm text-gray-500">${company.uei || ''}</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm text-gray-900">${company.city || ''}, ${company.state || ''}</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                ${company.pe_investment_score || 0}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${company.business_health_grade || ''}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${company.patent_count || 0}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${((company.federal_contracts_value || 0) / 1000000).toFixed(2)}M</td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <a href="company-details.html?uei=${company.uei}" class="text-indigo-600 hover:text-indigo-900">View Details</a>
                        </td>
                    `;
                });
                
                console.log('Portfolio table loaded successfully!');
            })
            .catch(error => console.error('Error loading portfolio:', error));
    }
    
    // Start trying when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', tryLoadTable);
    } else {
        tryLoadTable();
    }
})();
