import re

with open('company-details.html', 'r') as f:
    content = f.read()

# Find the displayEnhancedAIInsights function and fix it
old_pattern = r"document\.getElementById\('aiInsightsContent'\)\.innerHTML = `[\s\S]*?`;"
new_content = '''document.getElementById('aiInsightsContent').innerHTML = `
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h3 class="text-2xl font-bold">AI Investment Analysis</h3>
            <span class="px-6 py-3 rounded-lg font-bold text-lg border-2 ${colors[insights.recommendation || insights['Investment Recommendation']] || 'bg-gray-100'}">
                ${insights.recommendation || insights['Investment Recommendation'] || 'Hold'}
            </span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow-md border border-green-200 p-4">
                <h4 class="font-semibold text-green-800 mb-2">Key Strengths</h4>
                <ul class="space-y-1">
                    ${(insights.key_strengths || insights['Key Strengths'] || []).map(s => `<li class="text-sm">▸ ${s}</li>`).join('')}
                </ul>
            </div>
            <div class="bg-white rounded-lg shadow-md border border-blue-200 p-4">
                <h4 class="font-semibold text-blue-800 mb-2">Growth Opportunities</h4>
                <ul class="space-y-1">
                    ${(insights.growth_opportunities || insights['Growth Opportunities'] || []).map(o => `<li class="text-sm">▸ ${o}</li>`).join('')}
                </ul>
            </div>
            <div class="bg-white rounded-lg shadow-md border border-red-200 p-4">
                <h4 class="font-semibold text-red-800 mb-2">Risk Factors</h4>
                <ul class="space-y-1">
                    ${(insights.risk_factors || insights['Risk Factors'] || []).map(r => `<li class="text-sm">▸ ${r}</li>`).join('')}
                </ul>
            </div>
            <div class="bg-white rounded-lg shadow-md border border-purple-200 p-4">
                <h4 class="font-semibold text-purple-800 mb-2">Analytics</h4>
                ${insights.analytics ? `
                    <p class="text-sm">Market Share: ${insights.analytics.market_share_estimate?.toFixed(1)}%</p>
                    <p class="text-sm">Growth Potential: ${insights.analytics.growth_potential?.toFixed(1)}%</p>
                    <p class="text-sm">Efficiency: ${insights.analytics.efficiency_ratio?.toFixed(1)}%</p>
                ` : ''}
            </div>
        </div>
        ${insights.financial_projections ? `
            <div class="bg-gray-50 rounded-lg p-4">
                <h4 class="font-semibold mb-2">Financial Projections</h4>
                <p class="text-sm">Estimated IRR: ${insights.financial_projections.irr_estimate?.toFixed(1)}%</p>
            </div>
        ` : ''}
    </div>
`;'''

# Update the file
content = re.sub(old_pattern, new_content, content, flags=re.DOTALL)

with open('company-details.html', 'w') as f:
    f.write(content)

print("✅ Fixed AI insights display")
