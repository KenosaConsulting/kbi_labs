#!/usr/bin/env python3
"""
Fix the patent loading in the pipeline
"""

# Find the _load_patent_data method in fixed_pipeline_final.py and replace it with:

def _load_patent_data(self):
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
                            df = pd.read_csv(filepath, sep='\t', 
                                           usecols=['patent_id', 'disambig_assignee_organization'],
                                           dtype={'disambig_assignee_organization': str})
                            org_col = 'disambig_assignee_organization'
                        else:
                            # For not disambiguated file
                            df = pd.read_csv(filepath, sep='\t',
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
            logger.error(f"Error loading patent data: {e}")
