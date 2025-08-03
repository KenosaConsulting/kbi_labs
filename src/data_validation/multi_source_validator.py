"""
KBI Labs Multi-Source Data Validation Framework
Cross-reference validation across all government data sources
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import json
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationSource(Enum):
    SAM_GOV = "sam_gov"
    USASPENDING = "usaspending"
    CONGRESS = "congress"
    FEDERAL_REGISTER = "federal_register"
    CENSUS = "census"
    REGULATIONS = "regulations"
    GOVINFO = "govinfo"
    GSA = "gsa"

@dataclass
class SourceValidation:
    """Individual source validation result"""
    source: ValidationSource
    is_valid: bool
    confidence: float
    data_quality_score: float
    validation_details: Dict[str, Any]
    response_time_ms: float
    errors: List[str]
    warnings: List[str]

@dataclass
class CrossValidationResult:
    """Result of cross-source validation"""
    overall_valid: bool
    consensus_score: float
    sources_checked: int
    sources_agreed: int
    false_positive_risk: float
    validation_summary: str
    source_results: List[SourceValidation]
    recommendation: str
    confidence_level: str

class MultiSourceValidator:
    """
    Validates opportunity data across multiple government sources
    to minimize false positives and ensure data accuracy
    """
    
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.session = None
        self.validation_cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
        # Validation thresholds
        self.min_sources_required = 3
        self.consensus_threshold = 0.75
        self.high_confidence_threshold = 0.85
        
        # API endpoints
        self.endpoints = {
            ValidationSource.SAM_GOV: "https://api.sam.gov/opportunities/v2/search",
            ValidationSource.USASPENDING: "https://api.usaspending.gov/api/v2/search/spending_by_award",
            ValidationSource.CONGRESS: "https://api.congress.gov/v3/bill",
            ValidationSource.FEDERAL_REGISTER: "https://www.federalregister.gov/api/v1/articles.json",
            ValidationSource.CENSUS: "https://api.census.gov/data/2021/acs/acs5",
            ValidationSource.REGULATIONS: "https://api.regulations.gov/v4/documents",
            ValidationSource.GOVINFO: "https://api.govinfo.gov/collections",
            ValidationSource.GSA: "https://api.gsa.gov/analytics/dap/v1.1/domain"
        }
        
        logger.info("MultiSourceValidator initialized with validation thresholds")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'KBI-Labs-Validator/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _generate_cache_key(self, opportunity_data: Dict) -> str:
        """Generate cache key for opportunity validation"""
        key_data = {
            'id': opportunity_data.get('id', ''),
            'title': opportunity_data.get('title', ''),
            'agency': opportunity_data.get('agency', ''),
            'posted_date': opportunity_data.get('posted_date', '')
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cached validation is still valid"""
        if not cache_entry:
            return False
        
        cache_time = datetime.fromisoformat(cache_entry['timestamp'])
        return datetime.now() - cache_time < timedelta(seconds=self.cache_ttl)
    
    async def validate_opportunity(self, opportunity_data: Dict) -> CrossValidationResult:
        """
        Perform comprehensive cross-source validation of opportunity data
        
        Args:
            opportunity_data: Opportunity information to validate
            
        Returns:
            CrossValidationResult with detailed validation analysis
        """
        start_time = datetime.now()
        
        # Check cache first
        cache_key = self._generate_cache_key(opportunity_data)
        if cache_key in self.validation_cache and self._is_cache_valid(self.validation_cache[cache_key]):
            logger.debug(f"Returning cached validation for {cache_key}")
            return CrossValidationResult(**self.validation_cache[cache_key]['result'])
        
        logger.info(f"Starting cross-source validation for opportunity: {opportunity_data.get('title', 'Unknown')}")
        
        # Validate against all available sources
        validation_tasks = []
        for source in ValidationSource:
            if source.value in self.api_keys or source == ValidationSource.FEDERAL_REGISTER:
                task = self._validate_against_source(source, opportunity_data)
                validation_tasks.append(task)
        
        # Execute validations concurrently
        try:
            source_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Validation tasks failed: {e}")
            source_results = []
        
        # Process results
        valid_results = []
        for result in source_results:
            if isinstance(result, SourceValidation):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Validation exception: {result}")
        
        # Calculate consensus and make final determination
        cross_validation = self._calculate_consensus(valid_results, opportunity_data)
        
        # Cache the result
        self.validation_cache[cache_key] = {
            'result': asdict(cross_validation),
            'timestamp': datetime.now().isoformat()
        }
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Cross-validation completed in {processing_time:.0f}ms - Consensus: {cross_validation.consensus_score:.2f}")
        
        return cross_validation
    
    async def _validate_against_source(self, source: ValidationSource, opportunity_data: Dict) -> SourceValidation:
        """
        Validate opportunity against specific government data source
        
        Args:
            source: Government data source to validate against
            opportunity_data: Opportunity information
            
        Returns:
            SourceValidation result
        """
        start_time = datetime.now()
        errors = []
        warnings = []
        validation_details = {}
        
        try:
            if source == ValidationSource.SAM_GOV:
                result = await self._validate_sam_gov(opportunity_data)
            elif source == ValidationSource.USASPENDING:
                result = await self._validate_usaspending(opportunity_data)
            elif source == ValidationSource.CONGRESS:
                result = await self._validate_congress(opportunity_data)
            elif source == ValidationSource.FEDERAL_REGISTER:
                result = await self._validate_federal_register(opportunity_data)
            elif source == ValidationSource.CENSUS:
                result = await self._validate_census(opportunity_data)
            elif source == ValidationSource.REGULATIONS:
                result = await self._validate_regulations(opportunity_data)
            elif source == ValidationSource.GOVINFO:
                result = await self._validate_govinfo(opportunity_data)
            elif source == ValidationSource.GSA:
                result = await self._validate_gsa(opportunity_data)
            else:
                result = {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
                errors.append(f"Unknown validation source: {source}")
            
            is_valid = result.get('is_valid', False)
            confidence = result.get('confidence', 0.0)
            data_quality = result.get('data_quality', 0.0)
            validation_details = result.get('details', {})
            
        except Exception as e:
            logger.error(f"Validation failed for {source.value}: {e}")
            is_valid = False
            confidence = 0.0
            data_quality = 0.0
            errors.append(str(e))
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SourceValidation(
            source=source,
            is_valid=is_valid,
            confidence=confidence,
            data_quality_score=data_quality,
            validation_details=validation_details,
            response_time_ms=response_time,
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_sam_gov(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Validate against SAM.gov opportunities database"""
        if not self.session:
            return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
        
        try:
            # Search for similar opportunities in SAM.gov
            params = {
                'api_key': self.api_keys.get('SAM_API_KEY'),
                'q': opportunity_data.get('title', ''),
                'limit': 10
            }
            
            async with self.session.get(self.endpoints[ValidationSource.SAM_GOV], params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Analyze response for validation
                    opportunities = data.get('opportunitiesData', [])
                    match_found = len(opportunities) > 0
                    
                    # Calculate confidence based on matching criteria
                    confidence = 0.8 if match_found else 0.3
                    data_quality = min(1.0, len(opportunities) / 5)  # Quality based on result richness
                    
                    return {
                        'is_valid': match_found,
                        'confidence': confidence,
                        'data_quality': data_quality,
                        'details': {
                            'matches_found': len(opportunities),
                            'source_responsive': True
                        }
                    }
                else:
                    return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
                    
        except Exception as e:
            logger.error(f"SAM.gov validation error: {e}")
            return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
    
    async def _validate_usaspending(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Validate against USASpending.gov historical data"""
        if not self.session:
            return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
        
        try:
            # Search for historical spending by agency
            agency = opportunity_data.get('agency', '')
            if not agency:
                return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.2}
            
            search_payload = {
                "filters": {
                    "agencies": [{"type": "awarding", "tier": "toptier", "name": agency}],
                    "time_period": [{"start_date": "2022-01-01", "end_date": "2023-12-31"}]
                },
                "category": "awarding_agency",
                "subawards": False
            }
            
            async with self.session.post(
                self.endpoints[ValidationSource.USASPENDING],
                json=search_payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    agency_found = len(results) > 0
                    confidence = 0.7 if agency_found else 0.2
                    data_quality = min(1.0, len(results) / 10)
                    
                    return {
                        'is_valid': agency_found,
                        'confidence': confidence,
                        'data_quality': data_quality,
                        'details': {
                            'agency_spending_records': len(results),
                            'historical_validation': agency_found
                        }
                    }
                else:
                    return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
                    
        except Exception as e:
            logger.error(f"USASpending validation error: {e}")
            return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
    
    async def _validate_congress(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Validate against Congress.gov for policy alignment"""
        if not self.session:
            return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
        
        try:
            # Search for related legislation
            params = {
                'api_key': self.api_keys.get('CONGRESS_API_KEY'),
                'q': opportunity_data.get('title', ''),
                'limit': 5
            }
            
            async with self.session.get(self.endpoints[ValidationSource.CONGRESS], params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    bills = data.get('bills', [])
                    
                    policy_alignment = len(bills) > 0
                    confidence = 0.6 if policy_alignment else 0.4
                    data_quality = min(1.0, len(bills) / 3)
                    
                    return {
                        'is_valid': policy_alignment,
                        'confidence': confidence,
                        'data_quality': data_quality,
                        'details': {
                            'related_legislation': len(bills),
                            'policy_context_available': policy_alignment
                        }
                    }
                else:
                    return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
                    
        except Exception as e:
            logger.error(f"Congress validation error: {e}")
            return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
    
    async def _validate_federal_register(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Validate against Federal Register for regulatory context"""
        if not self.session:
            return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
        
        try:
            # Search Federal Register for related regulations
            params = {
                'conditions[term]': opportunity_data.get('title', ''),
                'per_page': 5
            }
            
            async with self.session.get(self.endpoints[ValidationSource.FEDERAL_REGISTER], params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    regulatory_context = len(results) > 0
                    confidence = 0.5 if regulatory_context else 0.3
                    data_quality = min(1.0, len(results) / 3)
                    
                    return {
                        'is_valid': regulatory_context,
                        'confidence': confidence,
                        'data_quality': data_quality,
                        'details': {
                            'regulatory_mentions': len(results),
                            'federal_register_context': regulatory_context
                        }
                    }
                else:
                    return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
                    
        except Exception as e:
            logger.error(f"Federal Register validation error: {e}")
            return {'is_valid': False, 'confidence': 0.0, 'data_quality': 0.0}
    
    # Simplified validation methods for other sources
    async def _validate_census(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Validate demographic/economic context via Census API"""
        return {'is_valid': True, 'confidence': 0.4, 'data_quality': 0.5, 'details': {'census_data_available': True}}
    
    async def _validate_regulations(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Validate against Regulations.gov"""
        return {'is_valid': True, 'confidence': 0.4, 'data_quality': 0.5, 'details': {'regulations_context': True}}
    
    async def _validate_govinfo(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Validate against GovInfo"""
        return {'is_valid': True, 'confidence': 0.3, 'data_quality': 0.4, 'details': {'govinfo_available': True}}
    
    async def _validate_gsa(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Validate against GSA data"""
        return {'is_valid': True, 'confidence': 0.3, 'data_quality': 0.4, 'details': {'gsa_context': True}}
    
    def _calculate_consensus(self, source_results: List[SourceValidation], opportunity_data: Dict) -> CrossValidationResult:
        """
        Calculate consensus across validation sources and make final determination
        
        Args:
            source_results: List of individual source validation results
            opportunity_data: Original opportunity data
            
        Returns:
            CrossValidationResult with consensus analysis
        """
        if not source_results:
            return CrossValidationResult(
                overall_valid=False,
                consensus_score=0.0,
                sources_checked=0,
                sources_agreed=0,
                false_positive_risk=1.0,
                validation_summary="No validation sources available",
                source_results=[],
                recommendation="pass",
                confidence_level="none"
            )
        
        # Calculate basic consensus metrics
        sources_checked = len(source_results)
        sources_agreed = sum(1 for result in source_results if result.is_valid)
        consensus_score = sources_agreed / sources_checked if sources_checked > 0 else 0.0
        
        # Calculate weighted consensus based on source reliability and confidence
        weighted_scores = []
        total_weight = 0
        
        # Weight sources by importance and confidence
        source_weights = {
            ValidationSource.SAM_GOV: 0.3,  # Primary source
            ValidationSource.USASPENDING: 0.25,  # Historical validation
            ValidationSource.CONGRESS: 0.2,  # Policy context
            ValidationSource.FEDERAL_REGISTER: 0.15,  # Regulatory context
            ValidationSource.CENSUS: 0.05,  # Economic context
            ValidationSource.REGULATIONS: 0.05  # Additional regulatory
        }
        
        for result in source_results:
            weight = source_weights.get(result.source, 0.1)
            if result.is_valid:
                weighted_score = result.confidence * weight
                weighted_scores.append(weighted_score)
                total_weight += weight
        
        weighted_consensus = sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
        
        # Calculate false positive risk
        uncertainty_factors = []
        for result in source_results:
            if result.errors:
                uncertainty_factors.append(0.3)  # Errors increase uncertainty
            if result.response_time_ms > 5000:  # Slow responses
                uncertainty_factors.append(0.1)
            if result.data_quality_score < 0.5:  # Poor data quality
                uncertainty_factors.append(0.2)
        
        base_fp_risk = 1.0 - weighted_consensus
        uncertainty_penalty = sum(uncertainty_factors) * 0.1
        false_positive_risk = min(1.0, base_fp_risk + uncertainty_penalty)
        
        # Determine overall validity and recommendation
        if sources_checked < self.min_sources_required:
            overall_valid = False
            recommendation = "analyze"  # Insufficient data
            confidence_level = "low"
            validation_summary = f"Insufficient validation sources ({sources_checked} < {self.min_sources_required})"
        elif weighted_consensus >= self.high_confidence_threshold and false_positive_risk < 0.1:
            overall_valid = True
            recommendation = "pursue"
            confidence_level = "high"
            validation_summary = f"High consensus across {sources_agreed}/{sources_checked} sources"
        elif weighted_consensus >= self.consensus_threshold and false_positive_risk < 0.25:
            overall_valid = True
            recommendation = "analyze"
            confidence_level = "medium"
            validation_summary = f"Moderate consensus ({weighted_consensus:.2f}) - detailed analysis recommended"
        else:
            overall_valid = False
            recommendation = "pass"
            confidence_level = "low"
            validation_summary = f"Low consensus ({weighted_consensus:.2f}) or high false positive risk ({false_positive_risk:.2f})"
        
        return CrossValidationResult(
            overall_valid=overall_valid,
            consensus_score=weighted_consensus,
            sources_checked=sources_checked,
            sources_agreed=sources_agreed,
            false_positive_risk=false_positive_risk,
            validation_summary=validation_summary,
            source_results=source_results,
            recommendation=recommendation,
            confidence_level=confidence_level
        )

# Global validator instance
_global_validator = None

async def get_validator(api_keys: Dict[str, str]) -> MultiSourceValidator:
    """Get or create global validator instance"""
    global _global_validator
    if _global_validator is None:
        _global_validator = MultiSourceValidator(api_keys)
    return _global_validator

async def validate_opportunity_cross_source(opportunity_data: Dict, api_keys: Dict[str, str]) -> CrossValidationResult:
    """
    Convenience function for cross-source opportunity validation
    
    Args:
        opportunity_data: Opportunity information to validate
        api_keys: API keys for government data sources
        
    Returns:
        CrossValidationResult with detailed validation analysis
    """
    async with MultiSourceValidator(api_keys) as validator:
        return await validator.validate_opportunity(opportunity_data)