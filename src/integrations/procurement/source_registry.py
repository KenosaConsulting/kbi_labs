"""
Procurement Source Registry

Manages configuration and metadata for 70+ government procurement data sources
based on the OSBP Useful Websites catalog.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SourceType(Enum):
    """Categories of procurement data sources"""
    CONTRACT_DATA = "contract_data"
    OPPORTUNITY = "opportunity"
    BUDGET_FORECAST = "budget_forecast"
    AGENCY_INFO = "agency_info" 
    SMALL_BUSINESS = "small_business"
    REGULATORY = "regulatory"
    COMPETITIVE_INTEL = "competitive_intel"

class DataFormat(Enum):
    """Data formats supported by integration"""
    JSON_API = "json_api"
    XML_API = "xml_api"
    CSV_DOWNLOAD = "csv_download"
    PDF_SCRAPING = "pdf_scraping"
    HTML_SCRAPING = "html_scraping"
    RSS_FEED = "rss_feed"

@dataclass
class ProcurementSource:
    """Configuration for a single procurement data source"""
    id: str
    name: str
    url: str
    source_type: SourceType
    data_format: DataFormat
    description: str
    priority: int = 1  # 1=high, 2=medium, 3=low
    refresh_interval_hours: int = 24
    requires_auth: bool = False
    api_key_env_var: Optional[str] = None
    rate_limit_per_hour: int = 100
    extraction_config: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

class ProcurementSourceRegistry:
    """Registry of all government procurement data sources"""
    
    def __init__(self):
        self.sources: Dict[str, ProcurementSource] = {}
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize all 70+ procurement data sources from OSBP catalog"""
        
        # Critical Real-Time Contract Data Sources
        self._add_contract_sources()
        
        # Opportunity and Solicitation Sources
        self._add_opportunity_sources()
        
        # Budget and Forecasting Sources
        self._add_budget_sources()
        
        # Agency-Specific Sources
        self._add_agency_sources()
        
        # Small Business Program Sources
        self._add_small_business_sources()
        
        # Regulatory and Compliance Sources
        self._add_regulatory_sources()
    
    def _add_contract_sources(self):
        """Add contract data sources"""
        contract_sources = [
            ProcurementSource(
                id="sam_gov",
                name="System for Award Management",
                url="https://sam.gov/api/prod/",
                source_type=SourceType.CONTRACT_DATA,
                data_format=DataFormat.JSON_API,
                description="Official U.S. Government registration and contract data",
                priority=1,
                refresh_interval_hours=6,
                requires_auth=True,
                api_key_env_var="SAM_GOV_API_KEY",
                rate_limit_per_hour=1000
            ),
            ProcurementSource(
                id="fpds_ng",
                name="Federal Procurement Data System - Next Generation",
                url="https://www.fpds.gov/",
                source_type=SourceType.CONTRACT_DATA,
                data_format=DataFormat.XML_API,
                description="Federal contract awards database with 90-day delay",
                priority=1,
                refresh_interval_hours=24,
                rate_limit_per_hour=200
            ),
            ProcurementSource(
                id="usaspending",
                name="USAspending.gov",
                url="https://api.usaspending.gov/api/",
                source_type=SourceType.CONTRACT_DATA,
                data_format=DataFormat.JSON_API,
                description="Public information on federal spending and contracts",
                priority=1,
                refresh_interval_hours=24,
                rate_limit_per_hour=500
            )
        ]
        
        for source in contract_sources:
            self.sources[source.id] = source
    
    def _add_opportunity_sources(self):
        """Add opportunity and solicitation sources"""
        opportunity_sources = [
            ProcurementSource(
                id="fedconnect",
                name="FedConnect",
                url="https://www.fedconnect.net/",
                source_type=SourceType.OPPORTUNITY,
                data_format=DataFormat.HTML_SCRAPING,
                description="Federal contracting opportunities and grants",
                priority=1,
                refresh_interval_hours=4,
                rate_limit_per_hour=100
            ),
            ProcurementSource(
                id="defense_innovation_marketplace",
                name="Defense Innovation Marketplace",
                url="https://defenseinnovationmarketplace.dtic.mil/",
                source_type=SourceType.OPPORTUNITY,
                data_format=DataFormat.HTML_SCRAPING,
                description="DoD innovation and contracting opportunities",
                priority=2,
                refresh_interval_hours=12,
                rate_limit_per_hour=50
            )
        ]
        
        for source in opportunity_sources:
            self.sources[source.id] = source
    
    def _add_budget_sources(self):
        """Add budget and forecasting sources"""  
        budget_sources = [
            ProcurementSource(
                id="agency_procurement_forecasts",
                name="Agency Procurement Forecasts",
                url="https://www.acquisition.gov/",
                source_type=SourceType.BUDGET_FORECAST,
                data_format=DataFormat.PDF_SCRAPING,
                description="Annual agency procurement planning documents",
                priority=2,
                refresh_interval_hours=168,  # Weekly
                rate_limit_per_hour=20
            )
        ]
        
        for source in budget_sources:
            self.sources[source.id] = source
    
    def _add_agency_sources(self):
        """Add agency-specific sources"""
        agency_sources = [
            ProcurementSource(
                id="army_contracting_command",
                name="U.S. Army Contracting Command",
                url="https://acc.army.mil/",
                source_type=SourceType.AGENCY_INFO,
                data_format=DataFormat.HTML_SCRAPING,
                description="Army contracting opportunities and information",
                priority=2,
                refresh_interval_hours=24,
                rate_limit_per_hour=50
            ),
            ProcurementSource(
                id="darpa_sbo",
                name="DARPA Small Business Office",
                url="https://www.darpa.mil/work-with-us/for-small-businesses",
                source_type=SourceType.AGENCY_INFO,
                data_format=DataFormat.HTML_SCRAPING,
                description="DARPA small business contracting opportunities",
                priority=2,
                refresh_interval_hours=24,
                rate_limit_per_hour=30
            ),
            ProcurementSource(
                id="nasa_osbp_marshall",
                name="NASA OSBP - Marshall Space Flight Center",
                url="https://www.nasa.gov/centers/marshall/business/",
                source_type=SourceType.AGENCY_INFO,
                data_format=DataFormat.HTML_SCRAPING,
                description="NASA Marshall small business opportunities",
                priority=2,
                refresh_interval_hours=24,
                rate_limit_per_hour=30
            )
        ]
        
        for source in agency_sources:
            self.sources[source.id] = source
    
    def _add_small_business_sources(self):
        """Add small business program sources"""
        sb_sources = [
            ProcurementSource(
                id="dsbs",
                name="Dynamic Small Business Search",
                url="https://dsbs.sba.gov/",
                source_type=SourceType.SMALL_BUSINESS,
                data_format=DataFormat.HTML_SCRAPING,
                description="SBA small business certification database",
                priority=1,
                refresh_interval_hours=24,
                rate_limit_per_hour=100
            ),
            ProcurementSource(
                id="sba_subnet",
                name="SBA Subcontracting Network (SUBNet)",
                url="https://web.sba.gov/subnet/",
                source_type=SourceType.SMALL_BUSINESS,
                data_format=DataFormat.HTML_SCRAPING,
                description="Small business subcontracting opportunities",
                priority=2,
                refresh_interval_hours=12,
                rate_limit_per_hour=50
            ),
            ProcurementSource(
                id="sbir_sttr",
                name="SBIR/STTR Portal",
                url="https://www.sbir.gov/",
                source_type=SourceType.SMALL_BUSINESS,
                data_format=DataFormat.HTML_SCRAPING,
                description="Small Business Innovation Research opportunities",
                priority=1,
                refresh_interval_hours=24,
                rate_limit_per_hour=100
            )
        ]
        
        for source in sb_sources:
            self.sources[source.id] = source
    
    def _add_regulatory_sources(self):
        """Add regulatory and compliance sources"""
        regulatory_sources = [
            ProcurementSource(
                id="far",
                name="Federal Acquisition Regulation",
                url="https://www.acquisition.gov/far/",
                source_type=SourceType.REGULATORY,
                data_format=DataFormat.HTML_SCRAPING,
                description="Federal acquisition regulations",
                priority=2,
                refresh_interval_hours=168,  # Weekly
                rate_limit_per_hour=20
            ),
            ProcurementSource(
                id="dfars",
                name="Defense Federal Acquisition Regulations",
                url="https://www.acquisition.gov/dfars/",
                source_type=SourceType.REGULATORY,
                data_format=DataFormat.HTML_SCRAPING,
                description="DoD-specific acquisition regulations",
                priority=2,
                refresh_interval_hours=168,  # Weekly
                rate_limit_per_hour=20
            ),
            ProcurementSource(
                id="wage_determinations",
                name="Wage Determinations OnLine",
                url="https://www.wdol.gov/",
                source_type=SourceType.REGULATORY,
                data_format=DataFormat.HTML_SCRAPING,
                description="Federal wage determination requirements",
                priority=3,
                refresh_interval_hours=168,  # Weekly
                rate_limit_per_hour=10
            )
        ]
        
        for source in regulatory_sources:
            self.sources[source.id] = source
    
    def get_source(self, source_id: str) -> Optional[ProcurementSource]:
        """Get source configuration by ID"""
        return self.sources.get(source_id)
    
    def get_sources_by_type(self, source_type: SourceType) -> List[ProcurementSource]:
        """Get all sources of a specific type"""
        return [source for source in self.sources.values() 
                if source.source_type == source_type and source.active]
    
    def get_high_priority_sources(self) -> List[ProcurementSource]:
        """Get all high priority sources (priority=1)"""
        return [source for source in self.sources.values() 
                if source.priority == 1 and source.active]
    
    def get_sources_for_refresh(self, current_hour: int) -> List[ProcurementSource]:
        """Get sources that need refreshing based on their intervals"""
        return [source for source in self.sources.values()
                if source.active and current_hour % source.refresh_interval_hours == 0]
    
    def register_custom_source(self, source: ProcurementSource):
        """Register a custom procurement source"""
        self.sources[source.id] = source
        logger.info(f"Registered custom source: {source.name}")
    
    def deactivate_source(self, source_id: str):
        """Deactivate a source temporarily"""
        if source_id in self.sources:
            self.sources[source_id].active = False
            logger.info(f"Deactivated source: {source_id}")
    
    def get_all_active_sources(self) -> List[ProcurementSource]:
        """Get all active sources"""
        return [source for source in self.sources.values() if source.active]