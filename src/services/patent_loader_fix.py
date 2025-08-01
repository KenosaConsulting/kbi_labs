def _load_patent_data(self):
    """Load patent data from local files - FIXED VERSION"""
    self.patent_lookup = {}
    patent_path = 'patent_data/'
    
    if os.path.exists(patent_path):
        try:
            logger.info("Loading patent data...")
            patent_files = glob.glob(os.path.join(patent_path, '*.tsv'))
            
            # Mapping of files to their organization columns
            org_columns = {
                'g_assignee_disambiguated.tsv': ['assignee_sequence', 'assignee_id', 'disambig_assignee_individual_name_first', 'disambig_assignee_individual_name_last', 'disambig_assignee_organization', 'assignee_type'],
                'g_assignee_not_disambiguated.tsv': ['assignee_sequence', 'assignee_id', 'raw_assignee_individual_name_first', 'raw_assignee_individual_name_last', 'raw_assignee_organization', 'assignee_type'],
            }
            
            organizations_loaded = 0
            
            for file in patent_files[:10]:  # Process more files
                filename = os.path.basename(file)
                
                if filename in org_columns:
                    try:
                        cols = org_columns[filename]
                        org_col = cols[0]  # Use first org column
                        
                        # Read the file
                        df = pd.read_csv(file, sep='\t', usecols=[org_col], nrows=500000)
                        
                        # Process organizations
                        for org in df[org_col].dropna().unique():
                            org_clean = str(org).lower().strip()
                            if org_clean and len(org_clean) > 3:
                                if org_clean not in self.patent_lookup:
                                    self.patent_lookup[org_clean] = 0
                                self.patent_lookup[org_clean] += 1
                                organizations_loaded += 1
                                
                    except Exception as e:
                        logger.debug(f"Error loading {filename}: {e}")
                        
            logger.info(f"Loaded patent data for {len(self.patent_lookup):,} unique organizations")
            
        except Exception as e:
            logger.error(f"Error loading patent data: {e}")
