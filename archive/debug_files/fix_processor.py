import re

# Read the current processor file
with open('src/data_processors/dsbs_processor.py', 'r') as f:
    content = f.read()

# Add the safe_string method after the __init__ method
safe_string_method = '''
    def safe_string(self, value, max_length=None):
        """Safely convert value to string, handling NaN and None"""
        if pd.isna(value) or value is None:
            return None
        
        result = str(value).strip()
        if result.lower() in ['nan', 'null', '']:
            return None
            
        if max_length:
            result = result[:max_length]
            
        return result
'''

# Insert the safe_string method after the __init__ method
init_pattern = r'(def __init__\(self, db_url: str\):\s+self\.db_url = db_url\s+self\.processed_count = 0)'
content = re.sub(init_pattern, r'\1' + safe_string_method, content)

# Update the company dictionary creation to use safe_string
old_company_creation = '''                company = {
                    'organization_name': row.get('organization_name', '').strip()[:255],
                    'capabilities_narrative': row.get('capabilities_narrative'),
                    'capabilities_statement_link': self.clean_website(row.get('capabilities_statement_link')),
                    'active_sba_certifications': row.get('active_sba_certifications'),
                    'contact_first_name': row.get('first_name', '').strip()[:100] if pd.notna(row.get('first_name')) else None,
                    'contact_last_name': row.get('last_name', '').strip()[:100] if pd.notna(row.get('last_name')) else None,
                    'job_title': row.get('job_title', '').strip()[:200] if pd.notna(row.get('job_title')) else None,
                    'email': row.get('email', '').strip().lower()[:255] if pd.notna(row.get('email')) else None,
                    'address_line_1': row.get('address_line_1', '').strip()[:255] if pd.notna(row.get('address_line_1')) else None,
                    'address_line_2': row.get('address_line_2', '').strip()[:255] if pd.notna(row.get('address_line_2')) else None,
                    'city': row.get('city', '').strip()[:100] if pd.notna(row.get('city')) else None,
                    'state': row.get('state', '').strip().upper()[:50] if pd.notna(row.get('state')) else None,
                    'zipcode': str(row.get('zipcode', '')).strip()[:20] if pd.notna(row.get('zipcode')) else None,
                    'website': self.clean_website(row.get('website')),
                    'uei': row.get('uei_(unique_entity_identifier)', '').strip()[:50] if pd.notna(row.get('uei_(unique_entity_identifier)')) else None,
                    'phone_number': self.clean_phone_number(row.get('phone_number')),
                    'primary_naics_code': naics_info['code'],
                    'legal_structure': row.get('legal_structure', '').strip()[:100] if pd.notna(row.get('legal_structure')) else None,
                }'''

new_company_creation = '''                company = {
                    'organization_name': self.safe_string(row.get('organization_name'), 255),
                    'capabilities_narrative': self.safe_string(row.get('capabilities_narrative')),
                    'capabilities_statement_link': self.clean_website(row.get('capabilities_statement_link')),
                    'active_sba_certifications': self.safe_string(row.get('active_sba_certifications'), 500),
                    'contact_first_name': self.safe_string(row.get('first_name'), 100),
                    'contact_last_name': self.safe_string(row.get('last_name'), 100),
                    'job_title': self.safe_string(row.get('job_title'), 200),
                    'email': self.safe_string(row.get('email'), 255),
                    'address_line_1': self.safe_string(row.get('address_line_1'), 255),
                    'address_line_2': self.safe_string(row.get('address_line_2'), 255),
                    'city': self.safe_string(row.get('city'), 100),
                    'state': self.safe_string(row.get('state'), 50),
                    'zipcode': self.safe_string(row.get('zipcode'), 20),
                    'website': self.clean_website(row.get('website')),
                    'uei': self.safe_string(row.get('uei_(unique_entity_identifier)'), 50),
                    'phone_number': self.clean_phone_number(row.get('phone_number')),
                    'primary_naics_code': naics_info['code'],
                    'legal_structure': self.safe_string(row.get('legal_structure'), 100),
                }'''

content = content.replace(old_company_creation, new_company_creation)

# Write the updated content back
with open('src/data_processors/dsbs_processor.py', 'w') as f:
    f.write(content)

print("✅ Processor updated to handle NaN values properly!")
