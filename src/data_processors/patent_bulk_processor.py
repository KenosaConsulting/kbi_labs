#!/usr/bin/env python3
"""
Patent Bulk Data Processor
Processes PatentsView bulk downloads for production use
"""

import pandas as pd
import sqlite3
import logging
from typing import Dict, List
import os

class PatentBulkProcessor:
    def __init__(self, data_path="/app/patent_data"):
        self.data_path = data_path
        self.db_path = os.path.join(data_path, "patents.db")
        
    def build_patent_database(self):
        """Build SQLite database from bulk files for fast queries"""
        conn = sqlite3.connect(self.db_path)
        
        # Load assignee data
        assignee_df = pd.read_csv(
            f"{self.data_path}/assignee.tsv", 
            sep="\t",
            usecols=["id", "organization", "type"],
            dtype={"id": str, "organization": str}
        )
        assignee_df.to_sql("assignees", conn, if_exists="replace", index=True)
        
        # Load patent data
        patent_df = pd.read_csv(
            f"{self.data_path}/patent.tsv",
            sep="\t", 
            usecols=["id", "number", "date", "title", "type"],
            dtype={"id": str, "number": str}
        )
        patent_df.to_sql("patents", conn, if_exists="replace", index=True)
        
        # Create indexes for fast lookups
        conn.execute("CREATE INDEX idx_assignee_org ON assignees(organization)")
        conn.execute("CREATE INDEX idx_patent_date ON patents(date)")
        
        conn.close()
        return True
    
    def search_by_organization(self, org_name: str) -> List[Dict]:
        """Fast patent search using indexed database"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT p.number, p.title, p.date, a.organization
        FROM patents p
        JOIN patent_assignee pa ON p.id = pa.patent_id
        JOIN assignees a ON pa.assignee_id = a.id
        WHERE UPPER(a.organization) LIKE ?
        ORDER BY p.date DESC
        LIMIT 100
        """
        
        results = pd.read_sql_query(
            query, 
            conn, 
            params=[f"%{org_name.upper()}%"]
        )
        
        conn.close()
        return results.to_dict("records")
