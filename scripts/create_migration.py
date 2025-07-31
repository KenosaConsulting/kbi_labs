#!/usr/bin/env python3
"""
Database migration creator for KBI Labs
"""
import os
import sys
from datetime import datetime

def create_migration(name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"migrations/{timestamp}_{name}.sql"
    
    os.makedirs("migrations", exist_ok=True)
    
    template = f"""-- Migration: {name}
-- Created: {datetime.now().isoformat()}

-- UP
BEGIN;

-- Your migration SQL here

COMMIT;

-- DOWN
BEGIN;

-- Your rollback SQL here

COMMIT;
"""
    
    with open(filename, 'w') as f:
        f.write(template)
    
    print(f"Created migration: {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_migration.py <migration_name>")
        sys.exit(1)
    
    create_migration(sys.argv[1])
