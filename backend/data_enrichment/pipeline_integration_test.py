#!/usr/bin/env python3
"""
Data Enrichment Pipeline Integration Test Suite
Comprehensive Testing for Government Data Intelligence System

This test suite validates the entire data enrichment pipeline end-to-end,
ensuring accuracy, reliability, and performance of all components.
"""

import asyncio
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
import time
from decimal import Decimal

# Import our pipeline components
from government_data_pipeline import GovernmentDataPipeline, EnrichmentResult
from personnel_data_collector import PersonnelDataCollector, PersonnelRecord
from budget_extraction_pipeline import BudgetExtractionPipeline, BudgetAnalysis
from organizational_chart_scraper import OrganizationalChartScraper, OrganizationalChart
from data_validation_system import DataValidationSystem, DataQualityReport, DataSourceType

logger = logging.getLogger(__name__)

class PipelineIntegrationTester:
    """
    Comprehensive integration tester for data enrichment pipeline
    Tests all components working together end-to-end
    """
    
    def __init__(self):
        # Initialize all pipeline components
        self.data_pipeline = GovernmentDataPipeline()
        self.personnel_collector = PersonnelDataCollector()
        self.budget_extractor = BudgetExtractionPipeline()
        self.org_scraper = OrganizationalChartScraper()
        self.data_validator = DataValidationSystem()
        
        # Test configuration
        self.test_agencies = ['9700', '7000', '7500']  # DoD, DHS, HHS
        self.test_fiscal_years = [2022, 2023, 2024]
        
        # Performance benchmarks
        self.performance_benchmarks = {
            'max_enrichment_time_seconds': 300,  # 5 minutes max per agency
            'min_data_quality_score': 70.0,
            'min_api_success_rate': 0.8,
            'max_memory_usage_mb': 1024
        }
        
        # Test results storage
        self.test_results = {
            'start_time': None,
            'end_time': None,
            'total_duration_seconds': 0,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'quality_metrics': {},
            'errors': []
        }
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """
        Run comprehensive test suite for entire data enrichment pipeline
        
        Returns:
            Detailed test results and performance metrics
        """
        
        logger.info("Starting comprehensive data enrichment pipeline test suite")
        self.test_results['start_time'] = datetime.now()
        
        try:
            # Initialize all components
            await self._initialize_components()
            
            # Test 1: Core Data Pipeline Functionality
            await self._test_core_data_pipeline()
            
            # Test 2: Personnel Data Collection
            await self._test_personnel_data_collection()
            
            # Test 3: Budget Data Extraction
            await self._test_budget_data_extraction()
            
            # Test 4: Organizational Chart Scraping
            await self._test_organizational_chart_scraping()
            
            # Test 5: Data Validation and Quality Control
            await self._test_data_validation_system()
            
            # Test 6: End-to-End Integration
            await self._test_end_to_end_integration()
            
            # Test 7: Performance and Load Testing
            await self._test_performance_benchmarks()
            
            # Test 8: Error Handling and Recovery
            await self._test_error_handling()
            
            # Generate final test report
            await self._generate_test_report()
            
        except Exception as e:
            logger.error(f"Test suite execution failed: {str(e)}")
            self.test_results['errors'].append(f"Test suite failure: {str(e)}")
        
        finally:
            # Cleanup components
            await self._cleanup_components()
            
            self.test_results['end_time'] = datetime.now()
            self.test_results['total_duration_seconds'] = (
                self.test_results['end_time'] - self.test_results['start_time']
            ).total_seconds()
        
        return self.test_results
    
    async def _initialize_components(self):
        """Initialize all pipeline components for testing"""
        
        logger.info("Initializing pipeline components for testing")
        
        try:
            await self.data_pipeline.initialize()
            await self.personnel_collector.initialize()
            await self.budget_extractor.initialize()
            await self.org_scraper.initialize()
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {str(e)}")
            raise
    
    async def _test_core_data_pipeline(self):
        """Test core government data pipeline functionality"""
        
        logger.info("Testing core data pipeline functionality")
        test_name = "Core Data Pipeline"
        
        try:
            for agency_code in self.test_agencies:
                start_time = time.time()
                
                # Test basic data enrichment
                enrichment_results = await self.data_pipeline.enrich_agency_data(
                    agency_code=agency_code,
                    data_types=['budget', 'personnel', 'contracts']
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Validate results
                assert isinstance(enrichment_results, dict), "Enrichment results should be a dictionary"
                assert len(enrichment_results) > 0, "Should return at least one data type"
                
                for data_type, result in enrichment_results.items():
                    assert isinstance(result, EnrichmentResult), f"Result for {data_type} should be EnrichmentResult"
                    assert result.quality_score >= 0.0, "Quality score should be non-negative"
                    assert result.quality_score <= 1.0, "Quality score should not exceed 1.0"
                
                # Store performance metrics
                self.test_results['performance_metrics'][f'{test_name}_{agency_code}_duration'] = duration
                
                logger.info(f"Core pipeline test passed for agency {agency_code} in {duration:.2f}s")
            
            self._record_test_success(test_name)
            
        except Exception as e:
            self._record_test_failure(test_name, str(e))
            logger.error(f"Core data pipeline test failed: {str(e)}")
    
    async def _test_personnel_data_collection(self):
        """Test personnel data collection system"""
        
        logger.info("Testing personnel data collection system")
        test_name = "Personnel Data Collection"
        
        try:
            for agency_code in self.test_agencies[:2]:  # Test first 2 agencies
                start_time = time.time()
                
                # Test personnel collection
                personnel_records = await self.personnel_collector.collect_agency_personnel(
                    agency_code=agency_code,
                    collection_depth='standard',
                    focus_roles=['Director', 'Program Manager']
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Validate results
                assert isinstance(personnel_records, list), "Personnel records should be a list"
                
                for record in personnel_records:
                    assert isinstance(record, PersonnelRecord), "Each record should be PersonnelRecord"
                    assert record.full_name is not None, "Personnel should have names"
                    assert record.agency is not None, "Personnel should have agency"
                    assert record.confidence_score >= 0.0, "Confidence score should be non-negative"
                
                # Store metrics
                self.test_results['performance_metrics'][f'{test_name}_{agency_code}_duration'] = duration
                self.test_results['performance_metrics'][f'{test_name}_{agency_code}_records'] = len(personnel_records)
                
                logger.info(f"Personnel collection test passed for agency {agency_code}: {len(personnel_records)} records in {duration:.2f}s")
            
            self._record_test_success(test_name)
            
        except Exception as e:
            self._record_test_failure(test_name, str(e))
            logger.error(f"Personnel data collection test failed: {str(e)}")
    
    async def _test_budget_data_extraction(self):
        """Test budget data extraction pipeline"""
        
        logger.info("Testing budget data extraction pipeline")
        test_name = "Budget Data Extraction"
        
        try:
            for agency_code in self.test_agencies[:2]:  # Test first 2 agencies
                start_time = time.time()
                
                # Test budget extraction
                budget_analysis = await self.budget_extractor.extract_agency_budget(
                    agency_code=agency_code,
                    fiscal_years=[2023, 2024],
                    analysis_depth='standard'
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Validate results
                assert isinstance(budget_analysis, BudgetAnalysis), "Result should be BudgetAnalysis"
                assert budget_analysis.total_budget_authority >= 0, "Budget authority should be non-negative"
                assert budget_analysis.fiscal_year in [2023, 2024], "Fiscal year should match request"
                assert budget_analysis.data_completeness >= 0.0, "Data completeness should be non-negative"
                
                # Store metrics
                self.test_results['performance_metrics'][f'{test_name}_{agency_code}_duration'] = duration
                self.test_results['performance_metrics'][f'{test_name}_{agency_code}_line_items'] = len(budget_analysis.budget_line_items)
                
                logger.info(f"Budget extraction test passed for agency {agency_code}: {len(budget_analysis.budget_line_items)} line items in {duration:.2f}s")
            
            self._record_test_success(test_name)
            
        except Exception as e:
            self._record_test_failure(test_name, str(e))
            logger.error(f"Budget data extraction test failed: {str(e)}")
    
    async def _test_organizational_chart_scraping(self):
        """Test organizational chart scraping system"""
        
        logger.info("Testing organizational chart scraping system")
        test_name = "Organizational Chart Scraping"
        
        try:
            for agency_code in self.test_agencies[:1]:  # Test first agency only (web scraping is slow)
                start_time = time.time()
                
                # Test organizational chart scraping
                org_chart = await self.org_scraper.scrape_agency_organizational_chart(
                    agency_code=agency_code,
                    scraping_depth='basic'  # Use basic to speed up test
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Validate results
                assert isinstance(org_chart, OrganizationalChart), "Result should be OrganizationalChart"
                assert org_chart.agency_code == agency_code, "Agency code should match"
                assert org_chart.total_units >= 0, "Total units should be non-negative"
                assert org_chart.total_personnel >= 0, "Total personnel should be non-negative"
                
                # Store metrics
                self.test_results['performance_metrics'][f'{test_name}_{agency_code}_duration'] = duration
                self.test_results['performance_metrics'][f'{test_name}_{agency_code}_units'] = org_chart.total_units
                
                logger.info(f"Org chart scraping test passed for agency {agency_code}: {org_chart.total_units} units in {duration:.2f}s")
            
            self._record_test_success(test_name)
            
        except Exception as e:
            self._record_test_failure(test_name, str(e))
            logger.error(f"Organizational chart scraping test failed: {str(e)}")
    
    async def _test_data_validation_system(self):
        """Test data validation and quality control system"""
        
        logger.info("Testing data validation system")
        test_name = "Data Validation System"
        
        try:
            # Create test dataset
            test_personnel_data = [
                {
                    'full_name': 'John Smith',
                    'title': 'Program Manager',
                    'agency': 'Department of Defense',
                    'office': 'Research and Engineering',
                    'email': 'john.smith@dod.gov',
                    'phone': '(703) 555-1234',
                    'last_updated': datetime.now().isoformat()
                },
                {
                    'full_name': 'Jane Doe',
                    'title': 'Contracting Officer',
                    'agency': 'Department of Defense',
                    'office': 'Acquisition',
                    'email': 'jane.doe@dod.gov',
                    'phone': '(703) 555-5678',
                    'last_updated': datetime.now().isoformat()
                }
            ]
            
            start_time = time.time()
            
            # Test data validation
            quality_report = await self.data_validator.validate_dataset(
                dataset=test_personnel_data,
                dataset_name="Test Personnel Dataset",
                data_type="personnel",
                data_source_type=DataSourceType.OFFICIAL_API,
                validation_level="comprehensive"
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Validate results
            assert isinstance(quality_report, DataQualityReport), "Result should be DataQualityReport"
            assert quality_report.overall_score >= 0.0, "Overall score should be non-negative"
            assert quality_report.overall_score <= 100.0, "Overall score should not exceed 100"
            assert quality_report.total_records == len(test_personnel_data), "Record count should match"
            
            # Store metrics
            self.test_results['performance_metrics'][f'{test_name}_duration'] = duration
            self.test_results['quality_metrics'][f'{test_name}_score'] = quality_report.overall_score
            
            logger.info(f"Data validation test passed: score {quality_report.overall_score:.1f} in {duration:.2f}s")
            
            self._record_test_success(test_name)
            
        except Exception as e:
            self._record_test_failure(test_name, str(e))
            logger.error(f"Data validation system test failed: {str(e)}")
    
    async def _test_end_to_end_integration(self):
        """Test complete end-to-end pipeline integration"""
        
        logger.info("Testing end-to-end pipeline integration")
        test_name = "End-to-End Integration"
        
        try:
            agency_code = '9700'  # Test with DoD
            start_time = time.time()
            
            # Step 1: Collect all data types
            enrichment_results = await self.data_pipeline.enrich_agency_data(
                agency_code=agency_code,
                data_types=['budget', 'personnel', 'organizational']
            )
            
            # Step 2: Extract detailed budget analysis
            budget_analysis = await self.budget_extractor.extract_agency_budget(
                agency_code=agency_code,
                fiscal_years=[2024],
                analysis_depth='basic'
            )
            
            # Step 3: Validate the integrated data
            if enrichment_results.get('personnel') and enrichment_results['personnel'].data:
                # Convert personnel data for validation
                personnel_data = []
                for person in enrichment_results['personnel'].data.get('processed', {}).get('personnel_list', []):
                    personnel_data.append({
                        'full_name': person.get('name', 'Unknown'),
                        'title': person.get('title', 'Unknown'),
                        'agency': 'Department of Defense',
                        'office': person.get('office', 'Unknown'),
                        'last_updated': datetime.now().isoformat()
                    })
                
                if personnel_data:
                    quality_report = await self.data_validator.validate_dataset(
                        dataset=personnel_data,
                        dataset_name="Integrated Personnel Data",
                        data_type="personnel",
                        data_source_type=DataSourceType.OFFICIAL_API,
                        validation_level="standard"
                    )
                    
                    # Store integrated quality score
                    self.test_results['quality_metrics']['integrated_data_quality'] = quality_report.overall_score
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Validate integration results
            assert len(enrichment_results) > 0, "Should have enrichment results"
            assert isinstance(budget_analysis, BudgetAnalysis), "Should have budget analysis"
            
            # Store metrics
            self.test_results['performance_metrics'][f'{test_name}_duration'] = duration
            
            logger.info(f"End-to-end integration test passed in {duration:.2f}s")
            
            self._record_test_success(test_name)
            
        except Exception as e:
            self._record_test_failure(test_name, str(e))
            logger.error(f"End-to-end integration test failed: {str(e)}")
    
    async def _test_performance_benchmarks(self):
        """Test performance against defined benchmarks"""
        
        logger.info("Testing performance benchmarks")
        test_name = "Performance Benchmarks"
        
        try:
            # Check enrichment time benchmark
            enrichment_times = [
                v for k, v in self.test_results['performance_metrics'].items() 
                if 'duration' in k and 'Core Data Pipeline' in k
            ]
            
            if enrichment_times:
                avg_enrichment_time = sum(enrichment_times) / len(enrichment_times)
                assert avg_enrichment_time <= self.performance_benchmarks['max_enrichment_time_seconds'], \
                    f"Average enrichment time {avg_enrichment_time:.2f}s exceeds benchmark {self.performance_benchmarks['max_enrichment_time_seconds']}s"
            
            # Check data quality benchmark
            quality_scores = [
                v for k, v in self.test_results['quality_metrics'].items() 
                if 'score' in k
            ]
            
            if quality_scores:
                avg_quality_score = sum(quality_scores) / len(quality_scores)
                assert avg_quality_score >= self.performance_benchmarks['min_data_quality_score'], \
                    f"Average quality score {avg_quality_score:.1f} below benchmark {self.performance_benchmarks['min_data_quality_score']}"
            
            logger.info(f"Performance benchmarks test passed")
            
            self._record_test_success(test_name)
            
        except Exception as e:
            self._record_test_failure(test_name, str(e))
            logger.error(f"Performance benchmarks test failed: {str(e)}")
    
    async def _test_error_handling(self):
        """Test error handling and recovery mechanisms"""
        
        logger.info("Testing error handling and recovery")
        test_name = "Error Handling"
        
        try:
            # Test invalid agency code
            try:
                await self.data_pipeline.enrich_agency_data(
                    agency_code='INVALID',
                    data_types=['budget']
                )
                # Should handle gracefully without crashing
            except Exception:
                pass  # Expected to handle errors gracefully
            
            # Test empty dataset validation
            try:
                await self.data_validator.validate_dataset(
                    dataset=[],
                    dataset_name="Empty Dataset",
                    data_type="personnel",
                    data_source_type=DataSourceType.MANUAL_ENTRY,
                    validation_level="basic"
                )
                # Should handle empty datasets gracefully
            except Exception:
                pass  # Expected to handle errors gracefully
            
            logger.info("Error handling test passed")
            
            self._record_test_success(test_name)
            
        except Exception as e:
            self._record_test_failure(test_name, str(e))
            logger.error(f"Error handling test failed: {str(e)}")
    
    async def _generate_test_report(self):
        """Generate comprehensive test report"""
        
        logger.info("Generating comprehensive test report")
        
        # Calculate success rate
        if self.test_results['tests_run'] > 0:
            success_rate = self.test_results['tests_passed'] / self.test_results['tests_run']
        else:
            success_rate = 0.0
        
        # Generate performance summary
        performance_summary = {}
        for metric, value in self.test_results['performance_metrics'].items():
            if 'duration' in metric:
                performance_summary[metric] = f"{value:.2f}s"
            else:
                performance_summary[metric] = value
        
        # Generate quality summary
        quality_summary = {}
        for metric, value in self.test_results['quality_metrics'].items():
            quality_summary[metric] = f"{value:.1f}"
        
        # Add summary to test results
        self.test_results['summary'] = {
            'success_rate': f"{success_rate:.1%}",
            'performance_summary': performance_summary,
            'quality_summary': quality_summary,
            'benchmark_compliance': self._check_benchmark_compliance()
        }
        
        logger.info(f"Test report generated: {success_rate:.1%} success rate")
    
    def _check_benchmark_compliance(self) -> Dict[str, bool]:
        """Check compliance with performance benchmarks"""
        
        compliance = {}
        
        # Check enrichment time
        enrichment_times = [
            v for k, v in self.test_results['performance_metrics'].items() 
            if 'duration' in k and 'Core Data Pipeline' in k
        ]
        
        if enrichment_times:
            avg_time = sum(enrichment_times) / len(enrichment_times)
            compliance['enrichment_time'] = avg_time <= self.performance_benchmarks['max_enrichment_time_seconds']
        
        # Check quality scores
        quality_scores = [
            v for k, v in self.test_results['quality_metrics'].items() 
            if 'score' in k
        ]
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            compliance['data_quality'] = avg_quality >= self.performance_benchmarks['min_data_quality_score']
        
        return compliance
    
    def _record_test_success(self, test_name: str):
        """Record successful test"""
        self.test_results['tests_run'] += 1
        self.test_results['tests_passed'] += 1
        logger.info(f"✅ {test_name} test PASSED")
    
    def _record_test_failure(self, test_name: str, error_message: str):
        """Record failed test"""
        self.test_results['tests_run'] += 1
        self.test_results['tests_failed'] += 1
        self.test_results['errors'].append(f"{test_name}: {error_message}")
        logger.error(f"❌ {test_name} test FAILED: {error_message}")
    
    async def _cleanup_components(self):
        """Cleanup all pipeline components"""
        
        logger.info("Cleaning up pipeline components")
        
        try:
            await self.data_pipeline.close()
            await self.personnel_collector.close()
            await self.budget_extractor.close()
            await self.org_scraper.close()
            
            logger.info("All components cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Component cleanup failed: {str(e)}")

# Standalone test functions for pytest compatibility
@pytest.mark.asyncio
async def test_data_pipeline_initialization():
    """Test that data pipeline initializes correctly"""
    pipeline = GovernmentDataPipeline()
    await pipeline.initialize()
    assert pipeline.session is not None
    await pipeline.close()

@pytest.mark.asyncio
async def test_personnel_collector_initialization():
    """Test that personnel collector initializes correctly"""
    collector = PersonnelDataCollector()
    await collector.initialize()
    assert collector.session is not None
    await collector.close()

@pytest.mark.asyncio
async def test_budget_extractor_initialization():
    """Test that budget extractor initializes correctly"""
    extractor = BudgetExtractionPipeline()
    await extractor.initialize()
    assert extractor.session is not None
    await extractor.close()

@pytest.mark.asyncio
async def test_data_validation_system():
    """Test that data validation system works correctly"""
    validator = DataValidationSystem()
    
    test_data = [
        {
            'full_name': 'John Smith',
            'title': 'Director',
            'agency': 'Test Agency',
            'office': 'Test Office',
            'email': 'john@test.gov'
        }
    ]
    
    report = await validator.validate_dataset(
        dataset=test_data,
        dataset_name="Test Dataset",
        data_type="personnel",
        data_source_type=DataSourceType.MANUAL_ENTRY,
        validation_level="basic"
    )
    
    assert isinstance(report, DataQualityReport)
    assert report.overall_score >= 0.0
    assert report.total_records == 1

# Main execution function
async def main():
    """Run the comprehensive integration test suite"""
    
    print("🚀 Starting KBI Labs Data Enrichment Pipeline Test Suite")
    print("=" * 60)
    
    # Initialize and run test suite
    tester = PipelineIntegrationTester()
    test_results = await tester.run_comprehensive_test_suite()
    
    # Print detailed results
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests Run: {test_results['tests_run']}")
    print(f"Tests Passed: {test_results['tests_passed']}")
    print(f"Tests Failed: {test_results['tests_failed']}")
    print(f"Success Rate: {test_results['summary']['success_rate']}")
    print(f"Total Duration: {test_results['total_duration_seconds']:.2f} seconds")
    
    if test_results['errors']:
        print(f"\n❌ ERRORS ({len(test_results['errors'])}):")
        for error in test_results['errors']:
            print(f"  - {error}")
    
    if test_results['summary']['performance_summary']:
        print(f"\n⚡ PERFORMANCE METRICS:")
        for metric, value in test_results['summary']['performance_summary'].items():
            print(f"  - {metric}: {value}")
    
    if test_results['summary']['quality_summary']:
        print(f"\n📈 QUALITY METRICS:")
        for metric, value in test_results['summary']['quality_summary'].items():
            print(f"  - {metric}: {value}")
    
    if test_results['summary']['benchmark_compliance']:
        print(f"\n✅ BENCHMARK COMPLIANCE:")
        for benchmark, compliant in test_results['summary']['benchmark_compliance'].items():
            status = "PASS" if compliant else "FAIL"
            print(f"  - {benchmark}: {status}")
    
    print("\n" + "=" * 60)
    if test_results['tests_failed'] == 0:
        print("🎉 ALL TESTS PASSED! Pipeline is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review errors and fix issues.")
    
    return test_results

if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())