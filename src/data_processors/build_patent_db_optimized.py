#!/usr/bin/env python3
import pandas as pd
import sqlite3
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentDatabaseBuilder:
    def __init__(self, data_path='/app/patent_data'):
        self.data_path = data_path
        self.db_path = os.path.join(data_path, 'patents_kbi.db')
        self.conn = None
        
    def build(self):
        self.conn = sqlite3.connect(self.db_path)
        
        try:
            # Load assignees
            logger.info('Loading assignee data...')
            assignee_df = pd.read_csv(
                os.path.join(self.data_path, 'g_assignee_disambiguated.tsv'),
                sep='	',
                usecols=['assignee_id', 'organization', 'assignee_type'],
                dtype={'assignee_id': str, 'organization': str},
                nrows=1000000
            )
            
            assignee_df['org_clean'] = assignee_df['organization'].str.upper().str.strip()
            assignee_df = assignee_df[assignee_df['organization'].notna()]
            assignee_df.to_sql('assignees', self.conn, if_exists='replace', index=False)
            logger.info(f'Loaded {len(assignee_df):,} assignees')
            
            # Load patents in chunks
            logger.info('Loading patent data...')
            chunk_num = 0
            for chunk in pd.read_csv(
                os.path.join(self.data_path, 'g_patent.tsv'),
                sep='	',
                usecols=['patent_id', 'patent_number', 'patent_date', 'patent_title', 'patent_type'],
                dtype={'patent_id': str, 'patent_number': str},
                chunksize=500000
            ):
                chunk.to_sql('patents', self.conn, if_exists='append' if chunk_num > 0 else 'replace', index=False)
                chunk_num += 1
                logger.info(f'Processed {chunk_num * 500000:,} patents...')
                if chunk_num >= 10:
                    break
            
            # Load mappings
            logger.info('Loading patent-assignee mappings...')
            mapping_df = pd.read_csv(
                os.path.join(self.data_path, 'g_assignee_not_disambiguated.tsv'),
                sep='	',
                usecols=['patent_id', 'assignee_id'],
                dtype=str,
                nrows=2000000
            )
            mapping_df = mapping_df.dropna()
            mapping_df.to_sql('patent_assignee', self.conn, if_exists='replace', index=False)
            logger.info(f'Loaded {len(mapping_df):,} relationships')
            
            # Create indexes
            logger.info('Creating indexes...')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_org_clean ON assignees(org_clean)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_patent_date ON patents(patent_date)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_pa_patent ON patent_assignee(patent_id)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_pa_assignee ON patent_assignee(assignee_id)')
            
            logger.info('Patent database built successfully!')
            self.conn.close()
            return True
            
        except Exception as e:
            logger.error(f'Build failed: {e}')
            self.conn.close()
            return False

if __name__ == '__main__':
    builder = PatentDatabaseBuilder()
    builder.build()
