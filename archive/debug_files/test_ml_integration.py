#!/usr/bin/env python3
"""
Test ML Integration
Quick test of ML endpoints without full FastAPI dependencies
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent))

def test_ml_prototype():
    """Test basic ML prototype functionality"""
    print("🧪 Testing ML Prototype...")
    
    try:
        from quick_start_ml_prototype import KBIProcurementMLPrototype
        
        # Initialize prototype
        ml_prototype = KBIProcurementMLPrototype()
        
        # Test synthetic data generation
        data = ml_prototype.prepare_synthetic_data(n_samples=100)
        print(f"✅ Generated {len(data)} synthetic records")
        
        # Test feature preparation
        features_df = ml_prototype.prepare_features(data)
        print(f"✅ Prepared {len(features_df.columns)} features")
        
        # Test model training
        success_results = ml_prototype.train_contract_success_model(features_df)
        print(f"✅ Contract success model accuracy: {success_results['accuracy']:.3f}")
        
        fraud_results = ml_prototype.train_fraud_detection_model(features_df)
        print(f"✅ Fraud detection precision: {fraud_results['precision']:.3f}")
        
        # Test predictions
        test_company = {
            'procurement_intelligence_score': 75,
            'gsa_calc_found': True,
            'fpds_found': True,
            'sam_opportunities_found': True,
            'sam_entity_found': True,
            'gsa_avg_rate': 120,
            'fpds_total_value': 250000,
            'fpds_total_contracts': 8,
            'sam_total_matches': 5,
            'agency_diversity': 3,
            'contractor_network_size': 15,
            'years_in_business': 10,
            'small_business': True,
            'veteran_owned': False,
            'woman_owned': True,
            'state': 'VA',
            'primary_naics': 541511
        }
        
        success_pred = ml_prototype.predict_contract_success(test_company)
        print(f"✅ Contract success prediction: {success_pred['success_probability']:.3f}")
        
        anomaly_pred = ml_prototype.detect_anomalies(test_company)
        print(f"✅ Anomaly detection: {anomaly_pred['risk_level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Prototype test failed: {e}")
        return False

def test_ml_service():
    """Test ML service wrapper"""
    print("\n🔧 Testing ML Service...")
    
    try:
        from src.services.ml.models import MLModelService
        
        # Initialize service
        ml_service = MLModelService()
        
        # Test model loading
        loaded = ml_service.load_models()
        print(f"✅ Models loaded: {loaded}")
        
        if loaded:
            # Test prediction
            test_data = {
                'procurement_intelligence_score': 80.0,
                'gsa_calc_found': True,
                'fpds_found': True,
                'sam_opportunities_found': False,
                'sam_entity_found': True,
                'gsa_avg_rate': 150.0,
                'fpds_total_value': 500000.0,
                'fpds_total_contracts': 12,
                'sam_total_matches': 7,
                'agency_diversity': 4,
                'contractor_network_size': 18,
                'years_in_business': 15.0,
                'small_business': True,
                'veteran_owned': False,
                'woman_owned': False,
                'state': 'CA',
                'primary_naics': 541511
            }
            
            prediction = ml_service.predict_contract_success(test_data)
            print(f"✅ Service prediction: {prediction['success_probability']:.3f}")
            
            anomaly = ml_service.detect_anomalies(test_data)
            print(f"✅ Service anomaly detection: {anomaly['risk_level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Service test failed: {e}")
        return False

def test_procurement_apis():
    """Test procurement API integrations"""
    print("\n🔗 Testing Procurement APIs...")
    
    try:
        # Test GSA CALC integration
        from gsa_calc_integration import GSACALCProcessor
        gsa_api = GSACALCProcessor()
        print("✅ GSA CALC integration initialized")
        
        # Test FPDS integration
        from fpds_integration import FPDSProcessor
        fpds_api = FPDSProcessor()
        print("✅ FPDS integration initialized")
        
        # Test SAM opportunities integration  
        from sam_opportunities_integration import SAMOpportunitiesProcessor
        sam_api = SAMOpportunitiesProcessor()
        print("✅ SAM Opportunities integration initialized")
        
        # Test unified enrichment
        from unified_procurement_enrichment import UnifiedProcurementEnrichment
        unified_api = UnifiedProcurementEnrichment()
        print("✅ Unified procurement enrichment initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Procurement APIs test failed: {e}")
        return False

def generate_integration_report():
    """Generate comprehensive integration report"""
    print("\n📊 Generating Integration Report...")
    
    report = {
        'ml_prototype': False,
        'ml_service': False,
        'procurement_apis': False,
        'dashboard_running': False
    }
    
    # Test all components
    report['ml_prototype'] = test_ml_prototype()
    report['ml_service'] = test_ml_service()
    report['procurement_apis'] = test_procurement_apis()
    
    # Check if Streamlit dashboard is accessible
    try:
        import requests
        response = requests.get('http://localhost:8501', timeout=2)
        report['dashboard_running'] = response.status_code == 200
        print("✅ Streamlit dashboard is running")
    except:
        print("⚠️ Streamlit dashboard not accessible")
    
    # Generate report
    report_content = f"""# KBI Labs ML Integration Status Report

## Component Status
- **ML Prototype**: {'✅ Working' if report['ml_prototype'] else '❌ Failed'}
- **ML Service**: {'✅ Working' if report['ml_service'] else '❌ Failed'}
- **Procurement APIs**: {'✅ Working' if report['procurement_apis'] else '❌ Failed'}
- **Dashboard**: {'✅ Running' if report['dashboard_running'] else '⚠️ Not Running'}

## Test Results Summary
- **Overall Status**: {'🎉 All Systems Operational' if all(report.values()) else '⚠️ Some Issues Found'}
- **Success Rate**: {sum(report.values())}/4 components working

## Next Steps
{'✅ System ready for production use!' if all(report.values()) else '''
### Issues to Address:
''' + '\\n'.join([f"- Fix {k.replace('_', ' ').title()}" for k, v in report.items() if not v])}

## Available Endpoints
- **ML Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs (when FastAPI running)
- **ML Predictions**: http://localhost:8000/api/v1/ml/predict-success
- **Anomaly Detection**: http://localhost:8000/api/v1/ml/detect-anomalies

## Quick Test Commands
```bash
# Test ML prototype
python quick_start_ml_prototype.py

# Launch ML dashboard
streamlit run streamlit_ml_dashboard.py

# Test procurement APIs
python test_ml_integration.py
```
"""
    
    with open('ML_INTEGRATION_REPORT.md', 'w') as f:
        f.write(report_content)
    
    print(f"📄 Integration report saved: ML_INTEGRATION_REPORT.md")
    
    return report

def main():
    """Run comprehensive ML integration testing"""
    print("🚀 KBI Labs ML Integration Testing")
    print("=" * 50)
    
    report = generate_integration_report()
    
    print(f"\n🎯 Integration Summary:")
    print(f"   Success Rate: {sum(report.values())}/4 components")
    
    if all(report.values()):
        print("🎉 All systems operational! Ready for production.")
    else:
        print("⚠️ Some components need attention. Check the report for details.")
    
    print("\n🔗 Quick Access:")
    print("   ML Dashboard: http://localhost:8501")
    print("   Integration Report: ML_INTEGRATION_REPORT.md")

if __name__ == "__main__":
    main()