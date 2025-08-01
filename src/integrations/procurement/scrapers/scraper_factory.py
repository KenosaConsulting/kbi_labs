"""
Scraper Factory

Creates appropriate scrapers based on source configuration and data format.
Follows factory pattern for extensible scraper management.
"""

import logging
from typing import Dict, Type, Optional
from ..source_registry import ProcurementSource, DataFormat, SourceType
from .base_scraper import BaseProcurementScraper
from .api_scrapers import SAMGovScraper, USASpendingScraper, FPDSScraper  
from .web_scrapers import FedConnectScraper, AgencyScraper
from .document_scrapers import PDFScraper, ExcelScraper

logger = logging.getLogger(__name__)

class ScraperFactory:
    """Factory for creating appropriate scrapers based on source configuration"""
    
    def __init__(self):
        # Register scraper classes by data format
        self.format_scrapers: Dict[DataFormat, Type[BaseProcurementScraper]] = {
            DataFormat.JSON_API: self._get_api_scraper_class,
            DataFormat.XML_API: self._get_api_scraper_class,
            DataFormat.HTML_SCRAPING: AgencyScraper,
            DataFormat.PDF_SCRAPING: PDFScraper,
            DataFormat.CSV_DOWNLOAD: ExcelScraper,
            DataFormat.RSS_FEED: AgencyScraper
        }
        
        # Register specific scrapers by source ID
        self.source_scrapers: Dict[str, Type[BaseProcurementScraper]] = {
            'sam_gov': SAMGovScraper,
            'usaspending': USASpendingScraper,
            'fpds_ng': FPDSScraper,
            'fedconnect': FedConnectScraper
        }
    
    def _get_api_scraper_class(self, source: ProcurementSource) -> Type[BaseProcurementScraper]:
        """Determine appropriate API scraper based on source"""
        if 'sam.gov' in source.url.lower():
            return SAMGovScraper
        elif 'usaspending' in source.url.lower():
            return USASpendingScraper  
        elif 'fpds' in source.url.lower():
            return FPDSScraper
        else:
            return BaseProcurementScraper
    
    async def create_scraper(self, source: ProcurementSource) -> BaseProcurementScraper:
        """Create appropriate scraper for the given source"""
        
        try:
            # Check for source-specific scraper first
            if source.id in self.source_scrapers:
                scraper_class = self.source_scrapers[source.id]
                logger.debug(f"Using source-specific scraper for {source.id}")
            
            # Fall back to format-based scraper
            elif source.data_format in self.format_scrapers:
                scraper_selector = self.format_scrapers[source.data_format]
                
                if callable(scraper_selector) and scraper_selector != self._get_api_scraper_class:
                    scraper_class = scraper_selector
                elif scraper_selector == self._get_api_scraper_class:
                    scraper_class = self._get_api_scraper_class(source)
                else:
                    scraper_class = scraper_selector
                    
                logger.debug(f"Using format-based scraper for {source.data_format}")
            
            else:
                logger.warning(f"No specific scraper for {source.data_format}, using base scraper")
                scraper_class = BaseProcurementScraper
            
            # Create scraper instance
            scraper = scraper_class(source)
            logger.info(f"Created {scraper_class.__name__} for {source.name}")
            
            return scraper
            
        except Exception as e:
            logger.error(f"Failed to create scraper for {source.name}: {e}")
            # Fall back to base scraper
            return BaseProcurementScraper(source)
    
    def register_scraper(self, source_id: str, scraper_class: Type[BaseProcurementScraper]):
        """Register a custom scraper for a specific source"""
        self.source_scrapers[source_id] = scraper_class
        logger.info(f"Registered custom scraper {scraper_class.__name__} for {source_id}")
    
    def register_format_scraper(self, data_format: DataFormat, scraper_class: Type[BaseProcurementScraper]):
        """Register a scraper for a specific data format"""
        self.format_scrapers[data_format] = scraper_class
        logger.info(f"Registered format scraper {scraper_class.__name__} for {data_format}")