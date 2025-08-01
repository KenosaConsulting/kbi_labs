"""
Procurement Intelligence Integration Module

This module provides comprehensive data ingestion from 70+ government sources
for the KBI Labs AI-Powered Senior Procurement Analyst Platform.
"""

from .government_data_manager import GovernmentDataManager
from .source_registry import ProcurementSourceRegistry
from .data_pipeline import ProcurementDataPipeline

__all__ = [
    'GovernmentDataManager',
    'ProcurementSourceRegistry', 
    'ProcurementDataPipeline'
]