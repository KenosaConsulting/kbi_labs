import csv

sample_companies = [
    ["Tech Solutions LLC", "IT consulting and software development services", "", "8(a)", "John", "Smith", "CEO", "john@techsolutions.com", "123 Main St", "", "Austin", "TX", "78701", "https://techsolutions.com", "ABC123456789", "(512) 555-0123", "541511", "LLC"],
    ["Green Energy Corp", "Solar panel installation and renewable energy", "", "SDB", "Sarah", "Johnson", "President", "sarah@greenenergy.com", "456 Oak Ave", "Suite 200", "Denver", "CO", "80202", "https://greenenergy.com", "DEF987654321", "(303) 555-0456", "238220", "Corporation"],
    ["Metro Construction", "Commercial building and renovation services", "", "HUBZone", "Mike", "Davis", "Owner", "mike@metroconstruction.com", "789 Pine St", "", "Seattle", "WA", "98101", "", "GHI456789123", "(206) 555-0789", "236220", "Partnership"],
    ["Food Express", "Restaurant and catering services", "", "", "Lisa", "Williams", "Manager", "lisa@foodexpress.com", "321 Elm Dr", "", "Miami", "FL", "33101", "https://foodexpress.com", "JKL789123456", "(305) 555-0321", "722511", "LLC"],
    ["Auto Repair Plus", "Vehicle maintenance and repair services", "", "VOSB", "Robert", "Brown", "Owner", "rob@autorepairplus.com", "654 Maple Ave", "", "Phoenix", "AZ", "85001", "", "MNO123456789", "(602) 555-0654", "811111", "Sole Proprietorship"]
]

headers = [
    "Organization Name", "Capabilities narrative", "Capabilities statement link", 
    "Active SBA certifications", "First Name", "Last Name", "Job Title", "Email",
    "Address line 1", "Address line 2", "City", "State", "Zipcode", "Website",
    "UEI (Unique Entity Identifier)", "Phone number", "Primary NAICS code", "Legal structure"
]

with open('All_DSBS_processed_chunk_001_20250727_182259.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(sample_companies)

print("✅ Sample CSV created!")
