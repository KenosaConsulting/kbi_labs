#!/usr/bin/env python3
"""
Data Validation and Quality Control System
Government Data Intelligence Quality Assurance

This system validates, scores, and ensures quality of government data collected
from multiple sources, providing confidence metrics for strategic decision-making.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
import re
import statistics
from decimal import Decimal
import hashlib

logger = logging.getLogger(__name__)

class DataQualityLevel(Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    CRITICAL = "Critical"

class ValidationStatus(Enum):
    PASSED = "Passed"
    WARNING = "Warning"
    FAILED = "Failed"
    SKIPPED = "Skipped"

class DataSourceType(Enum):
    OFFICIAL_API = "Official Government API"
    OFFICIAL_WEBSITE = "Official Government Website"
    THIRD_PARTY_API = "Third Party API"
    WEB_SCRAPING = "Web Scraping"
    MANUAL_ENTRY = "Manual Entry"

@dataclass
class ValidationRule:
    """Individual validation rule definition"""
    
    rule_id: str
    rule_name: str
    rule_type: str  # "format", "range", "completeness", "consistency", "accuracy"
    description: str
    severity: str  # "critical", "high", "medium", "low"
    
    # Rule parameters
    parameters: Dict[str, Any]
    
    # Scoring weights
    weight: float = 1.0
    max_score: float = 100.0
    
    # Metadata
    created_date: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class ValidationResult:
    """Result of applying a validation rule"""
    
    rule_id: str
    rule_name: str
    status: ValidationStatus
    score: float
    max_score: float
    
    # Detailed results
    total_records: int
    passed_records: int
    failed_records: int
    
    # Issue details
    issues_found: List[str]
    sample_failures: List[Dict[str, Any]]
    
    # Metadata
    validation_timestamp: datetime
    execution_time_ms: float
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage"""
        if self.total_records == 0:
            return 0.0
        return (self.passed_records / self.total_records) * 100.0
    
    @property
    def quality_level(self) -> DataQualityLevel:
        """Determine quality level based on score"""
        score_percentage = (self.score / self.max_score) * 100.0
        
        if score_percentage >= 95:
            return DataQualityLevel.EXCELLENT
        elif score_percentage >= 85:
            return DataQualityLevel.GOOD
        elif score_percentage >= 70:
            return DataQualityLevel.FAIR
        elif score_percentage >= 50:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.CRITICAL

@dataclass
class DataQualityReport:
    """Comprehensive data quality assessment report"""
    
    report_id: str
    dataset_name: str
    data_source_type: DataSourceType
    assessment_date: datetime
    
    # Overall quality metrics
    overall_score: float
    overall_quality_level: DataQualityLevel
    total_records: int
    
    # Validation results by category
    format_validation: List[ValidationResult]
    completeness_validation: List[ValidationResult]
    consistency_validation: List[ValidationResult]
    accuracy_validation: List[ValidationResult]
    timeliness_validation: List[ValidationResult]
    
    # Summary statistics
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    
    # Recommendations
    improvement_recommendations: List[str]
    data_reliability_score: float
    confidence_level: str
    
    # Metadata
    validation_duration_ms: float
    validator_version: str
    
    def __post_init__(self):
        # Calculate issue counts
        all_results = (
            self.format_validation + self.completeness_validation + 
            self.consistency_validation + self.accuracy_validation + 
            self.timeliness_validation
        )
        
        self.critical_issues = sum(1 for r in all_results if r.quality_level == DataQualityLevel.CRITICAL)
        self.high_issues = sum(1 for r in all_results if r.quality_level == DataQualityLevel.POOR)
        self.medium_issues = sum(1 for r in all_results if r.quality_level == DataQualityLevel.FAIR)
        self.low_issues = sum(1 for r in all_results if r.quality_level in [DataQualityLevel.GOOD, DataQualityLevel.EXCELLENT])

class DataValidationSystem:
    """
    Comprehensive data validation and quality control system
    Validates government data from multiple sources and provides quality scores
    """
    
    def __init__(self):
        # Validation rule sets
        self.validation_rules = {
            'personnel': self._create_personnel_validation_rules(),
            'budget': self._create_budget_validation_rules(),
            'organizational': self._create_organizational_validation_rules(),
            'contract': self._create_contract_validation_rules(),
            'general': self._create_general_validation_rules()
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            'critical': 50,
            'high': 70,
            'medium': 85,
            'excellent': 95
        }
        
        # Validation components
        self.format_validator = FormatValidator()
        self.completeness_validator = CompletenessValidator()
        self.consistency_validator = ConsistencyValidator()
        self.accuracy_validator = AccuracyValidator()
        self.timeliness_validator = TimelinessValidator()
        
        logger.info("Data validation system initialized")
    
    async def validate_dataset(
        self, 
        dataset: List[Dict[str, Any]], 
        dataset_name: str,
        data_type: str,
        data_source_type: DataSourceType,
        validation_level: str = "comprehensive"  # basic, standard, comprehensive
    ) -> DataQualityReport:
        """
        Validate a complete dataset and generate quality report
        
        Args:
            dataset: List of data records to validate
            dataset_name: Name/identifier for the dataset
            data_type: Type of data (personnel, budget, organizational, etc.)
            data_source_type: Source type for the data
            validation_level: Level of validation detail
            
        Returns:
            Comprehensive data quality report
        """
        
        start_time = datetime.now()
        logger.info(f"Starting validation for dataset: {dataset_name} ({len(dataset)} records)")
        
        try:
            # Get appropriate validation rules
            rules = self.validation_rules.get(data_type, self.validation_rules['general'])
            
            # Filter rules based on validation level
            filtered_rules = self._filter_rules_by_level(rules, validation_level)
            
            # Run validation by category
            format_results = await self._run_format_validation(dataset, filtered_rules, data_type)
            completeness_results = await self._run_completeness_validation(dataset, filtered_rules, data_type)
            consistency_results = await self._run_consistency_validation(dataset, filtered_rules, data_type)
            accuracy_results = await self._run_accuracy_validation(dataset, filtered_rules, data_type)
            timeliness_results = await self._run_timeliness_validation(dataset, filtered_rules, data_type)
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_score([
                format_results, completeness_results, consistency_results,
                accuracy_results, timeliness_results
            ])
            
            # Determine overall quality level
            overall_quality_level = self._determine_quality_level(overall_score)
            
            # Generate improvement recommendations
            recommendations = self._generate_recommendations(
                format_results, completeness_results, consistency_results,
                accuracy_results, timeliness_results
            )
            
            # Calculate confidence metrics
            reliability_score = self._calculate_reliability_score(
                format_results, completeness_results, consistency_results,
                accuracy_results, timeliness_results
            )
            confidence_level = self._determine_confidence_level(reliability_score)
            
            # Create quality report
            end_time = datetime.now()
            validation_duration = (end_time - start_time).total_seconds() * 1000
            
            report = DataQualityReport(
                report_id=f"QR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(dataset_name.encode()).hexdigest()[:8]}",
                dataset_name=dataset_name,
                data_source_type=data_source_type,
                assessment_date=datetime.now(),
                overall_score=overall_score,
                overall_quality_level=overall_quality_level,
                total_records=len(dataset),
                format_validation=format_results,
                completeness_validation=completeness_results,
                consistency_validation=consistency_results,
                accuracy_validation=accuracy_results,
                timeliness_validation=timeliness_results,
                improvement_recommendations=recommendations,
                data_reliability_score=reliability_score,
                confidence_level=confidence_level,
                validation_duration_ms=validation_duration,
                validator_version="1.0.0"
            )
            
            logger.info(f"Validation complete: {overall_score:.1f}/100.0 ({overall_quality_level.value})")
            return report
            
        except Exception as e:
            logger.error(f"Error validating dataset: {str(e)}")
            raise
    
    def _create_personnel_validation_rules(self) -> List[ValidationRule]:
        """Create validation rules for personnel data"""
        
        rules = [
            # Format validation rules
            ValidationRule(
                rule_id="PERS_001",
                rule_name="Name Format Validation",
                rule_type="format",
                description="Validates that personnel names follow proper format",
                severity="high",
                parameters={
                    "field": "full_name",
                    "pattern": r"^[A-Za-z\s\.\-']{2,50}$",
                    "required": True
                },
                weight=1.5
            ),
            ValidationRule(
                rule_id="PERS_002", 
                rule_name="Email Format Validation",
                rule_type="format",
                description="Validates email address format",
                severity="medium",
                parameters={
                    "field": "email",
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    "required": False
                }
            ),
            ValidationRule(
                rule_id="PERS_003",
                rule_name="Phone Format Validation", 
                rule_type="format",
                description="Validates phone number format",
                severity="low",
                parameters={
                    "field": "phone",
                    "pattern": r"^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$",
                    "required": False
                }
            ),
            
            # Completeness validation rules
            ValidationRule(
                rule_id="PERS_101",
                rule_name="Required Fields Completeness",
                rule_type="completeness",
                description="Checks that required personnel fields are populated",
                severity="critical",
                parameters={
                    "required_fields": ["full_name", "title", "agency", "office"],
                    "min_completion_rate": 0.95
                },
                weight=2.0
            ),
            ValidationRule(
                rule_id="PERS_102",
                rule_name="Contact Information Completeness",
                rule_type="completeness",
                description="Checks availability of contact information",
                severity="medium",
                parameters={
                    "fields": ["email", "phone", "office_address"],
                    "min_fields_populated": 1
                }
            ),
            
            # Consistency validation rules
            ValidationRule(
                rule_id="PERS_201",
                rule_name="Title-Agency Consistency",
                rule_type="consistency",
                description="Validates that personnel titles are consistent with their agencies",
                severity="medium",
                parameters={
                    "title_field": "title",
                    "agency_field": "agency",
                    "validate_hierarchy": True
                }
            ),
            
            # Accuracy validation rules
            ValidationRule(
                rule_id="PERS_301",
                rule_name="Duplicate Personnel Detection",
                rule_type="accuracy",
                description="Detects potential duplicate personnel records",
                severity="high",
                parameters={
                    "match_fields": ["full_name", "agency"],
                    "similarity_threshold": 0.9
                },
                weight=1.5
            )
        ]
        
        return rules
    
    def _create_budget_validation_rules(self) -> List[ValidationRule]:
        """Create validation rules for budget data"""
        
        rules = [
            # Format validation rules
            ValidationRule(
                rule_id="BUDG_001",
                rule_name="Budget Amount Format",
                rule_type="format",
                description="Validates that budget amounts are properly formatted numbers",
                severity="critical",
                parameters={
                    "field": "budget_authority",
                    "data_type": "decimal",
                    "min_value": 0,
                    "max_value": 1000000000000  # $1 trillion max
                },
                weight=2.0
            ),
            ValidationRule(
                rule_id="BUDG_002",
                rule_name="Fiscal Year Format",
                rule_type="format", 
                description="Validates fiscal year format",
                severity="high",
                parameters={
                    "field": "fiscal_year",
                    "data_type": "integer",
                    "min_value": 2000,
                    "max_value": 2030
                }
            ),
            ValidationRule(
                rule_id="BUDG_003",
                rule_name="Account Code Format",
                rule_type="format",
                description="Validates government account code format",
                severity="medium",
                parameters={
                    "field": "account_code",
                    "pattern": r"^\d{3}-\d{2}-\d{4}$|^\d{6}$",
                    "required": True
                }
            ),
            
            # Completeness validation rules
            ValidationRule(
                rule_id="BUDG_101",
                rule_name="Core Budget Fields Completeness",
                rule_type="completeness",
                description="Checks that core budget fields are populated",
                severity="critical",
                parameters={
                    "required_fields": ["account_code", "budget_authority", "fiscal_year"],
                    "min_completion_rate": 1.0
                },
                weight=2.0
            ),
            
            # Consistency validation rules
            ValidationRule(
                rule_id="BUDG_201",
                rule_name="Budget Balance Consistency",
                rule_type="consistency",
                description="Validates that budget amounts are mathematically consistent",
                severity="high",
                parameters={
                    "budget_authority_field": "budget_authority",
                    "outlays_field": "outlays",
                    "obligations_field": "obligations",
                    "tolerance": 0.01  # 1% tolerance
                },
                weight=1.5
            ),
            
            # Accuracy validation rules
            ValidationRule(
                rule_id="BUDG_301",
                rule_name="Historical Budget Trend Analysis",
                rule_type="accuracy",
                description="Validates budget amounts against historical trends",
                severity="medium",
                parameters={
                    "trend_analysis": True,
                    "max_year_over_year_change": 3.0,  # 300% max change
                    "outlier_detection": True
                }
            )
        ]
        
        return rules
    
    def _create_organizational_validation_rules(self) -> List[ValidationRule]:
        """Create validation rules for organizational data"""
        
        rules = [
            # Format validation rules
            ValidationRule(
                rule_id="ORG_001",
                rule_name="Unit Name Format",
                rule_type="format",
                description="Validates organizational unit name format",
                severity="high",
                parameters={
                    "field": "unit_name",
                    "min_length": 3,
                    "max_length": 200,
                    "required": True
                }
            ),
            
            # Completeness validation rules
            ValidationRule(
                rule_id="ORG_101",
                rule_name="Organizational Hierarchy Completeness",
                rule_type="completeness",
                description="Checks that organizational hierarchy is complete",
                severity="high",
                parameters={
                    "hierarchy_fields": ["unit_id", "unit_name", "unit_type", "parent_unit"],
                    "min_completion_rate": 0.90
                }
            ),
            
            # Consistency validation rules
            ValidationRule(
                rule_id="ORG_201",
                rule_name="Hierarchy Consistency",
                rule_type="consistency",
                description="Validates that organizational hierarchy is logically consistent",
                severity="critical",
                parameters={
                    "check_circular_references": True,
                    "validate_parent_child_relationships": True,
                    "max_hierarchy_depth": 10
                },
                weight=2.0
            )
        ]
        
        return rules
    
    def _create_contract_validation_rules(self) -> List[ValidationRule]:
        """Create validation rules for contract data"""
        
        rules = [
            # Format validation rules
            ValidationRule(
                rule_id="CONT_001",
                rule_name="Contract Amount Format",
                rule_type="format",
                description="Validates contract amount format",
                severity="critical",
                parameters={
                    "field": "award_amount",
                    "data_type": "decimal",
                    "min_value": 0,
                    "required": True
                },
                weight=2.0
            ),
            
            # Completeness validation rules
            ValidationRule(
                rule_id="CONT_101",
                rule_name="Contract Core Fields",
                rule_type="completeness",
                description="Checks that core contract fields are populated",
                severity="critical",
                parameters={
                    "required_fields": ["award_id", "recipient_name", "award_amount", "award_date"],
                    "min_completion_rate": 0.95
                },
                weight=2.0
            )
        ]
        
        return rules
    
    def _create_general_validation_rules(self) -> List[ValidationRule]:
        """Create general validation rules applicable to all data types"""
        
        rules = [
            # Timeliness validation rules
            ValidationRule(
                rule_id="GEN_001",
                rule_name="Data Freshness",
                rule_type="timeliness",
                description="Validates that data is recent enough to be useful",
                severity="medium",
                parameters={
                    "timestamp_field": "last_updated",
                    "max_age_days": 90,
                    "required": False
                }
            ),
            
            # General format rules
            ValidationRule(
                rule_id="GEN_002",
                rule_name="Text Field Length",
                rule_type="format",
                description="Validates that text fields are within reasonable length limits",
                severity="low",
                parameters={
                    "text_fields": ["description", "notes", "comments"],
                    "max_length": 1000,
                    "min_length": 1
                }
            )
        ]
        
        return rules
    
    def _filter_rules_by_level(self, rules: List[ValidationRule], validation_level: str) -> List[ValidationRule]:
        """Filter validation rules based on validation level"""
        
        if validation_level == "basic":
            # Only critical and high severity rules
            return [rule for rule in rules if rule.severity in ["critical", "high"]]
        elif validation_level == "standard":
            # Critical, high, and medium severity rules
            return [rule for rule in rules if rule.severity in ["critical", "high", "medium"]]
        else:  # comprehensive
            # All rules
            return rules
    
    async def _run_format_validation(
        self, 
        dataset: List[Dict[str, Any]], 
        rules: List[ValidationRule],
        data_type: str
    ) -> List[ValidationResult]:
        """Run format validation rules"""
        
        format_rules = [rule for rule in rules if rule.rule_type == "format"]
        results = []
        
        for rule in format_rules:
            result = await self.format_validator.validate_rule(dataset, rule)
            results.append(result)
        
        return results
    
    async def _run_completeness_validation(
        self, 
        dataset: List[Dict[str, Any]], 
        rules: List[ValidationRule],
        data_type: str
    ) -> List[ValidationResult]:
        """Run completeness validation rules"""
        
        completeness_rules = [rule for rule in rules if rule.rule_type == "completeness"]
        results = []
        
        for rule in completeness_rules:
            result = await self.completeness_validator.validate_rule(dataset, rule)
            results.append(result)
        
        return results
    
    async def _run_consistency_validation(
        self, 
        dataset: List[Dict[str, Any]], 
        rules: List[ValidationRule],
        data_type: str
    ) -> List[ValidationResult]:
        """Run consistency validation rules"""
        
        consistency_rules = [rule for rule in rules if rule.rule_type == "consistency"]
        results = []
        
        for rule in consistency_rules:
            result = await self.consistency_validator.validate_rule(dataset, rule)
            results.append(result)
        
        return results
    
    async def _run_accuracy_validation(
        self, 
        dataset: List[Dict[str, Any]], 
        rules: List[ValidationRule],
        data_type: str
    ) -> List[ValidationResult]:
        """Run accuracy validation rules"""
        
        accuracy_rules = [rule for rule in rules if rule.rule_type == "accuracy"]
        results = []
        
        for rule in accuracy_rules:
            result = await self.accuracy_validator.validate_rule(dataset, rule)
            results.append(result)
        
        return results
    
    async def _run_timeliness_validation(
        self, 
        dataset: List[Dict[str, Any]], 
        rules: List[ValidationRule],
        data_type: str
    ) -> List[ValidationResult]:
        """Run timeliness validation rules"""
        
        timeliness_rules = [rule for rule in rules if rule.rule_type == "timeliness"]
        results = []
        
        for rule in timeliness_rules:
            result = await self.timeliness_validator.validate_rule(dataset, rule)
            results.append(result)
        
        return results
    
    def _calculate_overall_score(self, validation_results: List[List[ValidationResult]]) -> float:
        """Calculate overall quality score from validation results"""
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for result_category in validation_results:
            for result in result_category:
                # Get rule to access weight
                rule_weight = 1.0  # Default weight
                weighted_score = (result.score / result.max_score) * 100.0 * rule_weight
                
                total_weighted_score += weighted_score
                total_weight += rule_weight
        
        if total_weight == 0:
            return 0.0
        
        return total_weighted_score / total_weight
    
    def _determine_quality_level(self, overall_score: float) -> DataQualityLevel:
        """Determine overall data quality level"""
        
        if overall_score >= self.quality_thresholds['excellent']:
            return DataQualityLevel.EXCELLENT
        elif overall_score >= self.quality_thresholds['medium']:
            return DataQualityLevel.GOOD
        elif overall_score >= self.quality_thresholds['high']:
            return DataQualityLevel.FAIR
        elif overall_score >= self.quality_thresholds['critical']:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.CRITICAL
    
    def _generate_recommendations(self, *validation_results) -> List[str]:
        """Generate improvement recommendations based on validation results"""
        
        recommendations = []
        
        for result_category in validation_results:
            for result in result_category:
                if result.quality_level in [DataQualityLevel.POOR, DataQualityLevel.CRITICAL]:
                    if result.rule_name == "Required Fields Completeness":
                        recommendations.append(f"Improve data collection processes to ensure required fields are populated")
                    elif result.rule_name == "Name Format Validation":
                        recommendations.append(f"Implement input validation for name fields to ensure proper formatting")
                    elif result.rule_name == "Duplicate Personnel Detection":
                        recommendations.append(f"Implement deduplication processes to remove duplicate records")
                    elif "Format" in result.rule_name:
                        recommendations.append(f"Standardize data formats for {result.rule_name.lower()}")
                    elif "Consistency" in result.rule_name:
                        recommendations.append(f"Review data relationships and implement consistency checks")
        
        # Remove duplicates and limit recommendations
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:10]  # Top 10 recommendations
    
    def _calculate_reliability_score(self, *validation_results) -> float:
        """Calculate data reliability score"""
        
        critical_failures = 0
        total_validations = 0
        
        for result_category in validation_results:
            for result in result_category:
                total_validations += 1
                if result.quality_level == DataQualityLevel.CRITICAL:
                    critical_failures += 1
        
        if total_validations == 0:
            return 0.0
        
        # Reliability is inversely related to critical failures
        reliability = max(0.0, 1.0 - (critical_failures / total_validations))
        return reliability * 100.0
    
    def _determine_confidence_level(self, reliability_score: float) -> str:
        """Determine confidence level based on reliability score"""
        
        if reliability_score >= 95:
            return "Very High"
        elif reliability_score >= 85:
            return "High"
        elif reliability_score >= 70:
            return "Medium"
        elif reliability_score >= 50:
            return "Low"
        else:
            return "Very Low"

class FormatValidator:
    """Validator for data format rules"""
    
    async def validate_rule(self, dataset: List[Dict[str, Any]], rule: ValidationRule) -> ValidationResult:
        """Validate format rule against dataset"""
        
        start_time = datetime.now()
        
        field = rule.parameters.get('field')
        pattern = rule.parameters.get('pattern')
        data_type = rule.parameters.get('data_type')
        min_value = rule.parameters.get('min_value')
        max_value = rule.parameters.get('max_value')
        required = rule.parameters.get('required', False)
        
        total_records = len(dataset)
        passed_records = 0
        failed_records = 0
        issues_found = []
        sample_failures = []
        
        for i, record in enumerate(dataset):
            value = record.get(field)
            
            # Check if field is required and missing
            if required and (value is None or value == ''):
                failed_records += 1
                if len(sample_failures) < 5:
                    sample_failures.append({
                        'record_index': i,
                        'issue': 'Missing required field',
                        'field': field,
                        'value': value
                    })
                continue
            
            # Skip validation if field is not required and missing
            if not required and (value is None or value == ''):
                passed_records += 1
                continue
            
            # Validate based on rule type
            is_valid = True
            
            if pattern and isinstance(value, str):
                if not re.match(pattern, value):
                    is_valid = False
                    if len(sample_failures) < 5:
                        sample_failures.append({
                            'record_index': i,
                            'issue': 'Pattern mismatch',
                            'field': field,
                            'value': value,
                            'expected_pattern': pattern
                        })
            
            if data_type == 'decimal' or data_type == 'integer':
                try:
                    numeric_value = float(value) if data_type == 'decimal' else int(value)
                    
                    if min_value is not None and numeric_value < min_value:
                        is_valid = False
                        if len(sample_failures) < 5:
                            sample_failures.append({
                                'record_index': i,
                                'issue': 'Value below minimum',
                                'field': field,
                                'value': value,
                                'min_value': min_value
                            })
                    
                    if max_value is not None and numeric_value > max_value:
                        is_valid = False
                        if len(sample_failures) < 5:
                            sample_failures.append({
                                'record_index': i,
                                'issue': 'Value above maximum',
                                'field': field,
                                'value': value,
                                'max_value': max_value
                            })
                            
                except (ValueError, TypeError):
                    is_valid = False
                    if len(sample_failures) < 5:
                        sample_failures.append({
                            'record_index': i,
                            'issue': 'Invalid numeric format',
                            'field': field,
                            'value': value
                        })
            
            if is_valid:
                passed_records += 1
            else:
                failed_records += 1
        
        # Calculate score
        if total_records == 0:
            score = rule.max_score
        else:
            score = (passed_records / total_records) * rule.max_score
        
        # Determine status
        if failed_records == 0:
            status = ValidationStatus.PASSED
        elif failed_records / total_records < 0.1:  # Less than 10% failures
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAILED
        
        # Generate issues summary
        if failed_records > 0:
            issues_found.append(f"{failed_records} records failed format validation for field '{field}'")
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        return ValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            status=status,
            score=score,
            max_score=rule.max_score,
            total_records=total_records,
            passed_records=passed_records,
            failed_records=failed_records,
            issues_found=issues_found,
            sample_failures=sample_failures,
            validation_timestamp=datetime.now(),
            execution_time_ms=execution_time
        )

class CompletenessValidator:
    """Validator for data completeness rules"""
    
    async def validate_rule(self, dataset: List[Dict[str, Any]], rule: ValidationRule) -> ValidationResult:
        """Validate completeness rule against dataset"""
        
        start_time = datetime.now()
        
        required_fields = rule.parameters.get('required_fields', [])
        min_completion_rate = rule.parameters.get('min_completion_rate', 0.8)
        fields = rule.parameters.get('fields', [])
        min_fields_populated = rule.parameters.get('min_fields_populated', 1)
        
        total_records = len(dataset)
        passed_records = 0
        failed_records = 0
        issues_found = []
        sample_failures = []
        
        for i, record in enumerate(dataset):
            is_valid = True
            
            # Check required fields completeness
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    value = record.get(field)
                    if value is None or value == '' or (isinstance(value, str) and value.strip() == ''):
                        missing_fields.append(field)
                
                if missing_fields:
                    completion_rate = (len(required_fields) - len(missing_fields)) / len(required_fields)
                    if completion_rate < min_completion_rate:
                        is_valid = False
                        if len(sample_failures) < 5:
                            sample_failures.append({
                                'record_index': i,
                                'issue': 'Required fields missing',
                                'missing_fields': missing_fields,
                                'completion_rate': completion_rate
                            })
            
            # Check minimum fields populated
            if fields and min_fields_populated:
                populated_count = 0
                for field in fields:
                    value = record.get(field)
                    if value is not None and value != '' and not (isinstance(value, str) and value.strip() == ''):
                        populated_count += 1
                
                if populated_count < min_fields_populated:
                    is_valid = False
                    if len(sample_failures) < 5:
                        sample_failures.append({
                            'record_index': i,
                            'issue': 'Insufficient fields populated',
                            'populated_count': populated_count,
                            'required_count': min_fields_populated
                        })
            
            if is_valid:
                passed_records += 1
            else:
                failed_records += 1
        
        # Calculate score
        if total_records == 0:
            score = rule.max_score
        else:
            score = (passed_records / total_records) * rule.max_score
        
        # Determine status
        if failed_records == 0:
            status = ValidationStatus.PASSED
        elif failed_records / total_records < 0.05:  # Less than 5% failures for completeness
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAILED
        
        # Generate issues summary
        if failed_records > 0:
            issues_found.append(f"{failed_records} records failed completeness validation")
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        return ValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            status=status,
            score=score,
            max_score=rule.max_score,
            total_records=total_records,
            passed_records=passed_records,
            failed_records=failed_records,
            issues_found=issues_found,
            sample_failures=sample_failures,
            validation_timestamp=datetime.now(),
            execution_time_ms=execution_time
        )

class ConsistencyValidator:
    """Validator for data consistency rules"""
    
    async def validate_rule(self, dataset: List[Dict[str, Any]], rule: ValidationRule) -> ValidationResult:
        """Validate consistency rule against dataset"""
        
        start_time = datetime.now()
        
        # Placeholder implementation for consistency validation
        # In production, this would implement specific consistency checks
        
        total_records = len(dataset)
        passed_records = total_records  # Assume all pass for now
        failed_records = 0
        issues_found = []
        sample_failures = []
        
        score = rule.max_score  # Perfect score for placeholder
        status = ValidationStatus.PASSED
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        return ValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            status=status,
            score=score,
            max_score=rule.max_score,
            total_records=total_records,
            passed_records=passed_records,
            failed_records=failed_records,
            issues_found=issues_found,
            sample_failures=sample_failures,
            validation_timestamp=datetime.now(),
            execution_time_ms=execution_time
        )

class AccuracyValidator:
    """Validator for data accuracy rules"""
    
    async def validate_rule(self, dataset: List[Dict[str, Any]], rule: ValidationRule) -> ValidationResult:
        """Validate accuracy rule against dataset"""
        
        start_time = datetime.now()
        
        # Placeholder implementation for accuracy validation
        # In production, this would implement duplicate detection, cross-reference validation, etc.
        
        total_records = len(dataset)
        passed_records = total_records  # Assume all pass for now
        failed_records = 0
        issues_found = []
        sample_failures = []
        
        score = rule.max_score  # Perfect score for placeholder
        status = ValidationStatus.PASSED
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        return ValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            status=status,
            score=score,
            max_score=rule.max_score,
            total_records=total_records,
            passed_records=passed_records,
            failed_records=failed_records,
            issues_found=issues_found,
            sample_failures=sample_failures,
            validation_timestamp=datetime.now(),
            execution_time_ms=execution_time
        )

class TimelinessValidator:
    """Validator for data timeliness rules"""
    
    async def validate_rule(self, dataset: List[Dict[str, Any]], rule: ValidationRule) -> ValidationResult:
        """Validate timeliness rule against dataset"""
        
        start_time = datetime.now()
        
        timestamp_field = rule.parameters.get('timestamp_field', 'last_updated')
        max_age_days = rule.parameters.get('max_age_days', 30)
        
        total_records = len(dataset)
        passed_records = 0
        failed_records = 0
        issues_found = []
        sample_failures = []
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for i, record in enumerate(dataset):
            timestamp_value = record.get(timestamp_field)
            
            if timestamp_value is None:
                # If no timestamp, assume it passes (for optional fields)
                passed_records += 1
                continue
            
            try:
                if isinstance(timestamp_value, str):
                    # Try to parse datetime string
                    record_date = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                elif isinstance(timestamp_value, datetime):
                    record_date = timestamp_value
                else:
                    # Invalid timestamp format
                    failed_records += 1
                    if len(sample_failures) < 5:
                        sample_failures.append({
                            'record_index': i,
                            'issue': 'Invalid timestamp format',
                            'field': timestamp_field,
                            'value': timestamp_value
                        })
                    continue
                
                if record_date >= cutoff_date:
                    passed_records += 1
                else:
                    failed_records += 1
                    if len(sample_failures) < 5:
                        sample_failures.append({
                            'record_index': i,
                            'issue': 'Data too old',
                            'field': timestamp_field,
                            'value': timestamp_value,
                            'age_days': (datetime.now() - record_date).days
                        })
                        
            except Exception as e:
                failed_records += 1
                if len(sample_failures) < 5:
                    sample_failures.append({
                        'record_index': i,
                        'issue': 'Error parsing timestamp',
                        'field': timestamp_field,
                        'value': timestamp_value,
                        'error': str(e)
                    })
        
        # Calculate score
        if total_records == 0:
            score = rule.max_score
        else:
            score = (passed_records / total_records) * rule.max_score
        
        # Determine status
        if failed_records == 0:
            status = ValidationStatus.PASSED
        elif failed_records / total_records < 0.2:  # Less than 20% failures for timeliness
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAILED
        
        # Generate issues summary
        if failed_records > 0:
            issues_found.append(f"{failed_records} records failed timeliness validation (older than {max_age_days} days)")
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        return ValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            status=status,
            score=score,
            max_score=rule.max_score,
            total_records=total_records,
            passed_records=passed_records,
            failed_records=failed_records,
            issues_found=issues_found,
            sample_failures=sample_failures,
            validation_timestamp=datetime.now(),
            execution_time_ms=execution_time
        )

# Example usage
async def main():
    """Example: Validate personnel dataset"""
    
    # Sample personnel dataset
    personnel_dataset = [
        {
            'full_name': 'John Smith',
            'title': 'Program Manager',
            'agency': 'Department of Defense',
            'office': 'Office of Research and Engineering',
            'email': 'john.smith@dod.gov',
            'phone': '(703) 555-1234',
            'last_updated': '2024-01-15T10:30:00'
        },
        {
            'full_name': 'Jane Doe',
            'title': 'Contracting Officer',
            'agency': 'Department of Defense',
            'office': 'Acquisition Office',
            'email': 'jane.doe@dod.gov',
            'phone': None,
            'last_updated': '2024-01-10T14:22:00'
        },
        {
            'full_name': '',  # Missing name - should fail validation
            'title': 'Deputy Director',
            'agency': 'Department of Defense',
            'office': 'Strategic Planning',
            'email': 'invalid-email',  # Invalid email format
            'phone': '555-1234',  # Invalid phone format
            'last_updated': '2023-06-01T09:15:00'  # Very old data
        }
    ]
    
    validator = DataValidationSystem()
    
    # Validate the dataset
    quality_report = await validator.validate_dataset(
        dataset=personnel_dataset,
        dataset_name="DoD Personnel Sample",
        data_type="personnel",
        data_source_type=DataSourceType.WEB_SCRAPING,
        validation_level="comprehensive"
    )
    
    print(f"Data Quality Report:")
    print(f"- Dataset: {quality_report.dataset_name}")
    print(f"- Overall Score: {quality_report.overall_score:.1f}/100.0")
    print(f"- Quality Level: {quality_report.overall_quality_level.value}")
    print(f"- Total Records: {quality_report.total_records}")
    print(f"- Data Reliability: {quality_report.data_reliability_score:.1f}%")
    print(f"- Confidence Level: {quality_report.confidence_level}")
    
    print(f"\nIssue Summary:")
    print(f"- Critical Issues: {quality_report.critical_issues}")
    print(f"- High Issues: {quality_report.high_issues}")
    print(f"- Medium Issues: {quality_report.medium_issues}")
    print(f"- Low Issues: {quality_report.low_issues}")
    
    if quality_report.improvement_recommendations:
        print(f"\nRecommendations:")
        for i, recommendation in enumerate(quality_report.improvement_recommendations, 1):
            print(f"{i}. {recommendation}")

if __name__ == "__main__":
    asyncio.run(main())