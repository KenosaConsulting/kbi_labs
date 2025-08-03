#!/usr/bin/env python3
"""
Government API Pipeline Health Monitor
Provides real-time health status and performance metrics
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass

try:
    from .enhanced_api_client import EnhancedGovernmentAPIClient
except ImportError:
    from enhanced_api_client import EnhancedGovernmentAPIClient

@dataclass
class HealthMetrics:
    """Health metrics for the API pipeline"""
    source_name: str
    is_healthy: bool
    response_time_ms: float
    success_rate: float
    last_check: datetime
    error_message: str = None
    data_quality_score: float = 1.0

class PipelineHealthMonitor:
    """Monitor health and performance of government API pipeline"""
    
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.health_history: Dict[str, List[HealthMetrics]] = {}
        self.alert_thresholds = {
            'response_time_ms': 5000,  # 5 seconds
            'success_rate': 0.7,       # 70%
            'data_quality': 0.8        # 80%
        }
    
    async def check_pipeline_health(self) -> Dict[str, Any]:
        """Run comprehensive health check on all APIs"""
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'sources': {},
            'summary': {
                'total_sources': 0,
                'healthy_sources': 0,
                'degraded_sources': 0,
                'failed_sources': 0,
                'avg_response_time': 0.0,
                'pipeline_success_rate': 0.0
            },
            'recommendations': []
        }
        
        async with EnhancedGovernmentAPIClient(self.api_keys) as client:
            
            # Test each data source
            sources_to_test = [
                ('opportunities', lambda: client.search_sam_gov_opportunities("AI", 2)),
                ('legislation', lambda: client.search_congress_bills("technology", 2)),
                ('federal_register', lambda: client.search_federal_register("innovation", 2)),
                ('census_data', lambda: client.get_census_data("demographics")),
                ('business_patterns', lambda: client.get_census_data("business_patterns")),
                ('government_analytics', lambda: client.get_government_analytics_data("agencies")),
                ('regulatory_docs', lambda: client.search_regulations_gov("AI"))
            ]
            
            total_response_time = 0
            successful_sources = 0
            
            for source_name, test_func in sources_to_test:
                metrics = await self._test_source_health(source_name, test_func)
                health_report['sources'][source_name] = metrics.__dict__
                
                # Track history
                if source_name not in self.health_history:
                    self.health_history[source_name] = []
                self.health_history[source_name].append(metrics)
                
                # Keep only last 24 hours of history
                cutoff = datetime.now() - timedelta(hours=24)
                self.health_history[source_name] = [
                    m for m in self.health_history[source_name] 
                    if m.last_check > cutoff
                ]
                
                # Update summary
                if metrics.is_healthy:
                    successful_sources += 1
                elif metrics.response_time_ms > 0:
                    health_report['summary']['degraded_sources'] += 1
                else:
                    health_report['summary']['failed_sources'] += 1
                
                if metrics.response_time_ms > 0:
                    total_response_time += metrics.response_time_ms
            
            # Calculate summary metrics
            health_report['summary']['total_sources'] = len(sources_to_test)
            health_report['summary']['healthy_sources'] = successful_sources
            health_report['summary']['avg_response_time'] = total_response_time / len(sources_to_test)
            health_report['summary']['pipeline_success_rate'] = successful_sources / len(sources_to_test)
            
            # Determine overall status
            success_rate = health_report['summary']['pipeline_success_rate']
            if success_rate >= 0.8:
                health_report['overall_status'] = 'healthy'
            elif success_rate >= 0.6:
                health_report['overall_status'] = 'degraded'
            else:
                health_report['overall_status'] = 'critical'
                
            # Add recommendations
            health_report['recommendations'] = self._generate_recommendations(health_report)
        
        return health_report
    
    async def _test_source_health(self, source_name: str, test_func) -> HealthMetrics:
        """Test health of individual data source"""
        
        start_time = time.time()
        
        try:
            result = await test_func()
            response_time = (time.time() - start_time) * 1000
            
            # Assess health
            is_healthy = result.success and response_time < self.alert_thresholds['response_time_ms']
            data_quality = self._assess_data_quality(result.data if result.success else None)
            
            return HealthMetrics(
                source_name=source_name,
                is_healthy=is_healthy,
                response_time_ms=response_time,
                success_rate=1.0 if result.success else 0.0,
                last_check=datetime.now(),
                error_message=result.error if not result.success else None,
                data_quality_score=data_quality
            )
            
        except Exception as e:
            return HealthMetrics(
                source_name=source_name,
                is_healthy=False,
                response_time_ms=0.0,
                success_rate=0.0,
                last_check=datetime.now(),
                error_message=str(e),
                data_quality_score=0.0
            )
    
    def _assess_data_quality(self, data: Any) -> float:
        """Assess quality of returned data"""
        
        if not data:
            return 0.0
        
        if isinstance(data, list):
            if len(data) == 0:
                return 0.0
            
            # Check if items have required fields
            quality_score = 1.0
            if len(data) < 2:  # Prefer multiple results
                quality_score -= 0.2
                
            # Check data completeness
            if isinstance(data[0], dict):
                required_fields = ['title', 'name', 'NAME']  # Common important fields
                has_required = any(field in data[0] for field in required_fields)
                if not has_required:
                    quality_score -= 0.3
            
            return max(0.0, quality_score)
        
        elif isinstance(data, dict):
            return 0.8 if data else 0.0
        
        return 0.5  # Basic data available
    
    def _generate_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on health status"""
        
        recommendations = []
        
        # Response time recommendations
        slow_sources = [
            name for name, metrics in health_report['sources'].items()
            if metrics['response_time_ms'] > self.alert_thresholds['response_time_ms']
        ]
        if slow_sources:
            recommendations.append(f"Optimize slow sources: {', '.join(slow_sources)}")
        
        # Success rate recommendations
        if health_report['summary']['pipeline_success_rate'] < self.alert_thresholds['success_rate']:
            failed_count = health_report['summary']['failed_sources']
            recommendations.append(f"Investigate {failed_count} failed sources")
        
        # Data quality recommendations
        low_quality_sources = [
            name for name, metrics in health_report['sources'].items()
            if metrics['data_quality_score'] < self.alert_thresholds['data_quality']
        ]
        if low_quality_sources:
            recommendations.append(f"Improve data quality: {', '.join(low_quality_sources)}")
        
        # Overall health recommendations
        if health_report['overall_status'] == 'critical':
            recommendations.append("URGENT: Pipeline in critical state - immediate attention required")
        elif health_report['overall_status'] == 'degraded':
            recommendations.append("Pipeline performance degraded - review error logs")
        
        return recommendations
    
    async def continuous_monitoring(self, interval_minutes: int = 15):
        """Run continuous health monitoring"""
        
        print(f"🏥 Starting continuous health monitoring (every {interval_minutes} minutes)")
        
        while True:
            try:
                health_report = await self.check_pipeline_health()
                
                status_emoji = {
                    'healthy': '✅',
                    'degraded': '⚠️', 
                    'critical': '🚨'
                }
                
                print(f"\n{status_emoji[health_report['overall_status']]} Pipeline Status: {health_report['overall_status'].upper()}")
                print(f"Success Rate: {health_report['summary']['pipeline_success_rate']:.1%}")
                print(f"Avg Response: {health_report['summary']['avg_response_time']:.0f}ms")
                
                if health_report['recommendations']:
                    print("📋 Recommendations:")
                    for rec in health_report['recommendations']:
                        print(f"   • {rec}")
                
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                print(f"❌ Health monitoring error: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute

async def quick_health_check(api_keys: Dict[str, str]) -> Dict[str, Any]:
    """Run a quick health check and return status"""
    monitor = PipelineHealthMonitor(api_keys)
    return await monitor.check_pipeline_health()

# CLI usage
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    API_KEYS = {
        "SAM_API_KEY": "Ec4gRnGckZjZmwbCtTiCyCsELua6nREcoyysaXqk",
        "CONGRESS_API_KEY": "Lt9hyLPZ5yBFUreIFDHvrMljeplEviWoHkAshNq9",
        "CENSUS_API_KEY": "70e4e3355e1b7b1a42622ba9201157bd1b105629",
        "REGULATIONS_API_KEY": "eOaulCdds6asIkvxR54otUJIC6badoeSynDJN68w",
        "GSA_API_KEY": "MbeF6wFg5auoS4v2uy0ua3Dc1hfo5RV68uXbVAwY",
        "GOVINFO_API_KEY": "2y76olvQevGbWUkoWgFNAJSa1KBabOFU1FBrhWsF"
    }
    
    async def main():
        print("🏥 KBI LABS GOVERNMENT API HEALTH MONITOR")
        print("=" * 50)
        
        health_report = await quick_health_check(API_KEYS)
        
        print(f"📊 Pipeline Health: {health_report['overall_status'].upper()}")
        print(f"✅ Success Rate: {health_report['summary']['pipeline_success_rate']:.1%}")
        print(f"⚡ Avg Response: {health_report['summary']['avg_response_time']:.0f}ms")
        print(f"📈 Sources: {health_report['summary']['healthy_sources']}/{health_report['summary']['total_sources']} healthy")
        
        if health_report['recommendations']:
            print("\n📋 Recommendations:")
            for rec in health_report['recommendations']:
                print(f"   • {rec}")
    
    asyncio.run(main())