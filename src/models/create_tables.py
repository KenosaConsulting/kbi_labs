#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from src.enrichment.models import Base
from src.database.connection import engine

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✓ Tables created successfully!")
