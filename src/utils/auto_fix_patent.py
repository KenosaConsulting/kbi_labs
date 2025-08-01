#!/usr/bin/env python3
"""Automatically fix the patent loading in the pipeline"""

# Read the original file
with open('fixed_pipeline_final.py', 'r') as f:
    content = f.read()

# Find the _load_patent_data method and replace it
start_marker = "    def _load_patent_data(self):"
end_marker = "            except Exception as e:\n                logger.error(f\"Error loading patent data: {e}\")"

# Find the start position
start_pos = content.find(start_marker)
if start_pos == -1:
    print("Error: Could not find _load_patent_data method")
    exit(1)

# Find the end position
end_pos = content.find(end_marker, start_pos)
if end_pos == -1:
    print("Error: Could not find end of _load_patent_data method")
    exit(1)

# Add the length of the end marker
end_pos += len(end_marker)

# The new method
new_method = '''    def _load_patent_data(self):
        """Load patent data from local files - FIXED VERSION"""
        self.patent_lookup = {}
        patent_path = 'patent_data/'
        
        if os.path.exists(patent_path):
            try:
                logger.info("Loading patent data...")
                
                # Process assignee files specifically
                assignee_files = [
                    'g_assignee_disambiguated.tsv',
                    'g_assignee_not_disambiguated.tsv'
                ]
                
                total_patents = 0
                
                for filename in assignee_files:
                    filepath = os.path.join(patent_path, filename)
                    if os.path.exists(filepath):
                        try:
                            logger.info(f"Loading {filename}...")
                            
                            if 'disambiguated' in filename:
                                # For disambiguated file
                                df = pd.read_csv(filepath, sep='\\t', 
                                               usecols=['patent_id', 'disambig_assignee_organization'],
                                               dtype={'disambig_assignee_organization': str})
                                org_col = 'disambig_assignee_organization'
                            else:
                                # For not disambiguated file
                                df = pd.read_csv(filepath, sep='\\t',
                                               usecols=['patent_id', 'raw_assignee_organization'],
                                               dtype={'raw_assignee_organization': str})
                                org_col = 'raw_assignee_organization'
                            
                            # Count patents per organization
                            org_counts = df[org_col].dropna().value_counts()
                            
                            # Add to lookup
                            for org, count in org_counts.items():
                                org_clean = str(org).lower().strip()
                                if org_clean and len(org_clean) > 3 and org_clean != 'nan':
                                    if org_clean not in self.patent_lookup:
                                        self.patent_lookup[org_clean] = 0
                                    self.patent_lookup[org_clean] += count
                                    total_patents += count
                                    
                            logger.info(f"Loaded {len(org_counts)} organizations from {filename}")
                            
                        except Exception as e:
                            logger.error(f"Error loading {filename}: {e}")
                
                logger.info(f"Loaded patent data for {len(self.patent_lookup):,} unique organizations with {total_patents:,} total patents")
                
            except Exception as e:
                logger.error(f"Error loading patent data: {e}")'''

# Replace the method
new_content = content[:start_pos] + new_method + content[end_pos:]

# Write to new file
with open('fixed_pipeline_final_working.py', 'w') as f:
    f.write(new_content)

print("✅ Successfully created fixed_pipeline_final_working.py with corrected patent loading!")
print("The patent loading method has been fixed.")
