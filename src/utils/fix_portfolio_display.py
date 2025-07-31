with open('kbi_dashboard/portfolio.html', 'r') as f:
    content = f.read()

# Fix the chart container heights
content = content.replace(
    '<canvas id="industryChart" width="400" height="300"></canvas>',
    '<div style="height: 300px; position: relative;"><canvas id="industryChart"></canvas></div>'
)
content = content.replace(
    '<canvas id="geoChart" width="400" height="300"></canvas>',
    '<div style="height: 300px; position: relative;"><canvas id="geoChart"></canvas></div>'
)

# Update the chart options to maintain aspect ratio
old_chart_options = '''options: {
                responsive: true,
                maintainAspectRatio: false
            }'''

new_chart_options = '''options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: { size: 10 }
                        }
                    }
                }
            }'''

content = content.replace(old_chart_options, new_chart_options)

# Save the updated file
with open('kbi_dashboard/portfolio.html', 'w') as f:
    f.write(content)

print("✅ Fixed chart sizing")
