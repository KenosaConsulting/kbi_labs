#!/usr/bin/env python3
"""
Setup script for KBI Labs enrichment
"""
import os
import sys

print("Setting up KBI Labs enrichment pipeline...")

# Check for required directories
dirs_to_create = [
    'data/dsbs_raw',
    'data/exports',
    'logs',
    'src/enrichment',
    'src/database',
    'src/api'
]

for dir_path in dirs_to_create:
    os.makedirs(dir_path, exist_ok=True)
    print(f"✓ Created {dir_path}")

# Create __init__.py files
init_files = [
    'src/__init__.py',
    'src/enrichment/__init__.py',
    'src/database/__init__.py',
    'src/api/__init__.py'
]

for init_file in init_files:
    open(init_file, 'a').close()
    print(f"✓ Created {init_file}")

print("\n✓ Basic setup complete!")
