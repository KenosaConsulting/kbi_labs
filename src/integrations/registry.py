"""Registry for all external API integrations"""
from typing import Dict, Type
import logging
from src.integrations.base_enhanced import EnhancedAPIIntegration
from src.integrations.government.sam_gov import SAMGovIntegration
from src.integrations.government.usaspending import USASpendingIntegration
from src.integrations.government.sbir import SBIRIntegration

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    """Registry for all external API integrations"""
    
    def __init__(self):
        self._integrations: Dict[str, EnhancedAPIIntegration] = {}
        self._integration_classes: Dict[str, Type[EnhancedAPIIntegration]] = {
            "sam_gov": SAMGovIntegration,
            "usaspending": USASpendingIntegration,
            "sbir": SBIRIntegration,
            # Add more as implemented
        }
    
    async def initialize_all(self):
        """Initialize all registered integrations"""
        logger.info("Initializing API integrations...")
        
        for name, integration_class in self._integration_classes.items():
            try:
                integration = integration_class()
                if await integration.validate_connection():
                    self._integrations[name] = integration
                    logger.info(f"✅ Initialized {name} integration")
                else:
                    logger.warning(f"❌ Failed to validate {name} integration")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {name}: {e}")
        
        logger.info(f"Initialized {len(self._integrations)}/{len(self._integration_classes)} integrations")
    
    def get(self, name: str) -> EnhancedAPIIntegration:
        """Get integration by name"""
        if name not in self._integrations:
            raise ValueError(f"Integration {name} not found or not initialized")
        return self._integrations[name]
    
    def get_all(self) -> Dict[str, EnhancedAPIIntegration]:
        """Get all initialized integrations"""
        return self._integrations
    
    async def close_all(self):
        """Close all integrations"""
        for name, integration in self._integrations.items():
            try:
                await integration.close()
                logger.info(f"Closed {name} integration")
            except Exception as e:
                logger.error(f"Error closing {name}: {e}")


# Global registry instance
integration_registry = IntegrationRegistry()
