#!/usr/bin/env python3

html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Details - KBI Labs</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <header class="bg-white shadow">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <div class="flex justify-between items-center">
                <h1 class="text-2xl font-bold text-indigo-600">KBI Labs</h1>
                <a href="index.html" class="text-indigo-600 hover:text-indigo-800">← Back to Dashboard</a>
            </div>
        </div>
    </header>
    <!-- Rest of the HTML content continues... -->
</body>
</html>'''

with open('kbi_dashboard/company-details.html', 'w') as f:
    f.write(html_content)
    
print("✅ Company details page created successfully!")
