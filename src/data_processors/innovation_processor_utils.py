import os
import pandas as pd
import glob

def find_dsbs_files():
    """Find all DSBS CSV files in the container"""
    patterns = [
        '/app/All_DSBS_processed_chunk_*.csv',
        '/app/all_dsbs_processed_chunk_*.csv',
        '/app/*DSBS*.csv',
        '/app/data/*DSBS*.csv'
    ]
    
    all_files = []
    for pattern in patterns:
        files = glob.glob(pattern)
        all_files.extend(files)
    
    return sorted(set(all_files))

def load_all_dsbs_data():
    """Load and combine all DSBS CSV files"""
    files = find_dsbs_files()
    
    if not files:
        raise FileNotFoundError("No DSBS files found in container")
    
    print(f"Found {len(files)} DSBS files")
    
    # Load all files and combine
    dfs = []
    for file in files:
        print(f"Loading {file}...")
        df = pd.read_csv(file)
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"Total records loaded: {len(combined_df)}")
    
    return combined_df
