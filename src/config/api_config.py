"""
API Configuration Manager

Manages all government API keys and configuration settings securely.
"""

import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class APIConfig:
    """Centralized API configuration management"""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self._validate_keys()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables or file"""
        
        # Try to load from environment first
        keys = {
            'census': os.getenv('CENSUS_API_KEY'),
            'regulations_gov': os.getenv('REGULATIONS_GOV_API_KEY'),
            'congress_gov': os.getenv('CONGRESS_GOV_API_KEY'),
            'govinfo': os.getenv('GOVINFO_API_KEY'),
            'gsa': os.getenv('GSA_API_KEY'),
            'sam_gov': os.getenv('SAM_GOV_API_KEY'),
        }
        
        # If not in environment, try to load from file
        if not any(keys.values()):
            keys = self._load_from_file()
        
        return {k: v for k, v in keys.items() if v}
    
    def _load_from_file(self) -> Dict[str, str]:
        """Load API keys from api_keys.env file"""
        keys = {}
        env_file_path = os.path.join(os.path.dirname(__file__), '../../api_keys.env')
        
        try:
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            api_name = self._map_env_to_api_name(key.strip())
                            if api_name:
                                keys[api_name] = value.strip()
                                
                logger.info(f"Loaded {len(keys)} API keys from file")
                
        except Exception as e:
            logger.error(f"Error loading API keys from file: {e}")
        
        return keys
    
    def _map_env_to_api_name(self, env_key: str) -> Optional[str]:
        """Map environment variable names to internal API names"""
        mapping = {
            'CENSUS_API_KEY': 'census',
            'REGULATIONS_GOV_API_KEY': 'regulations_gov',
            'CONGRESS_GOV_API_KEY': 'congress_gov',
            'GOVINFO_API_KEY': 'govinfo',
            'GSA_API_KEY': 'gsa',
            'SAM_GOV_API_KEY': 'sam_gov'
        }
        return mapping.get(env_key)
    
    def _validate_keys(self):
        """Validate that critical API keys are available"""
        critical_keys = ['sam_gov', 'congress_gov', 'gsa']
        missing_keys = [key for key in critical_keys if key not in self.api_keys]
        
        if missing_keys:
            logger.warning(f"Missing critical API keys: {missing_keys}")
        else:
            logger.info("All critical API keys loaded successfully")
    
    def get_api_key(self, api_name: str) -> Optional[str]:
        """Get API key for specific service"""
        return self.api_keys.get(api_name)
    
    def has_api_key(self, api_name: str) -> bool:
        """Check if API key is available"""
        return api_name in self.api_keys
    
    def get_api_config(self, api_name: str) -> Dict[str, str]:
        """Get full API configuration including base URLs"""
        base_configs = {
            'census': {
                'base_url': 'https://api.census.gov/data',
                'key_param': 'key'
            },
            'regulations_gov': {
                'base_url': 'https://api.regulations.gov/v4',
                'key_param': 'api_key'
            },
            'congress_gov': {
                'base_url': 'https://api.congress.gov/v3',
                'key_param': 'api_key',
                'header_name': 'x-api-key'
            },
            'govinfo': {
                'base_url': 'https://api.govinfo.gov',
                'key_param': 'api_key',
                'header_name': 'x-api-key'
            },
            'gsa': {
                'base_url': 'https://api.gsa.gov',
                'key_param': 'api_key',
                'header_name': 'x-api-key'
            },
            'sam_gov': {
                'base_url': 'https://api.sam.gov',
                'key_param': 'api_key',
                'header_name': 'x-api-key'
            },
            'federal_register': {
                'base_url': 'https://www.federalregister.gov/api/v1',
                'key_param': None  # No key required
            }
        }
        
        config = base_configs.get(api_name, {})
        if self.has_api_key(api_name):
            config['api_key'] = self.get_api_key(api_name)
        
        return config
    
    def get_headers(self, api_name: str) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        config = self.get_api_config(api_name)
        headers = {'User-Agent': 'KBI-Labs-Contractor-Intelligence/1.0'}
        
        # Add API key to headers if required
        if config.get('header_name') and config.get('api_key'):
            headers[config['header_name']] = config['api_key']
        
        return headers
    
    def get_available_apis(self) -> Dict[str, bool]:
        """Get status of all available APIs"""
        all_apis = ['census', 'regulations_gov', 'congress_gov', 'govinfo', 'gsa', 'sam_gov', 'federal_register']
        return {
            api: self.has_api_key(api) if api != 'federal_register' else True 
            for api in all_apis
        }

# Global configuration instance
api_config = APIConfig()

# Convenience functions
def get_api_key(api_name: str) -> Optional[str]:
    """Get API key for service"""
    return api_config.get_api_key(api_name)

def get_api_config(api_name: str) -> Dict[str, str]:
    """Get API configuration"""
    return api_config.get_api_config(api_name)

def get_headers(api_name: str) -> Dict[str, str]:
    """Get HTTP headers for API"""
    return api_config.get_headers(api_name)

def has_api_key(api_name: str) -> bool:
    """Check if API key is available"""
    return api_config.has_api_key(api_name)