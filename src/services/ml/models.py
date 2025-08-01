# ML Models Service
import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from quick_start_ml_prototype import KBIProcurementMLPrototype

class MLModelService:
    def __init__(self):
        self.ml_prototype = KBIProcurementMLPrototype()
        self.models_loaded = False
    
    def load_models(self):
        """Load trained ML models"""
        if not self.models_loaded:
            try:
                self.ml_prototype.load_models()
                self.models_loaded = True
                return True
            except Exception as e:
                print(f"Error loading models: {e}")
                return False
        return True
    
    def predict_contract_success(self, company_data):
        """Predict contract success probability"""
        if not self.load_models():
            raise Exception("Models not available")
        return self.ml_prototype.predict_contract_success(company_data)
    
    def detect_anomalies(self, company_data):
        """Detect anomalies in company data"""
        if not self.load_models():
            raise Exception("Models not available")
        return self.ml_prototype.detect_anomalies(company_data)
