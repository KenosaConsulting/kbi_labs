#!/usr/bin/env python3
"""
KBI Labs Repository Cleanup Script
Removes duplicate files, organizes structure, and prepares for ML integration
"""

import os
import shutil
import glob
from pathlib import Path

class KBIRepositoryCleanup:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.backup_dir = self.repo_path / "cleanup_backup"
        self.cleanup_report = []
        
    def create_backup_dir(self):
        """Create backup directory for moved files"""
        self.backup_dir.mkdir(exist_ok=True)
        print(f"📁 Created backup directory: {self.backup_dir}")
    
    def identify_duplicate_apis(self):
        """Identify duplicate API implementations"""
        api_patterns = [
            "kbi_api_*.py",
            "api_server_*.py", 
            "*_backup.py",
            "*_old.py",
            "*_broken.py",
            "*_test.py"
        ]
        
        duplicates = []
        for pattern in api_patterns:
            files = list(self.repo_path.glob(pattern))
            duplicates.extend(files)
        
        return duplicates
    
    def identify_main_files(self):
        """Identify the main/canonical versions to keep"""
        keep_files = [
            "src/main.py",  # Main FastAPI application
            "src/api/v1/api.py",  # Official API v1
            "streamlit_ml_dashboard.py",  # ML Dashboard
            "quick_start_ml_prototype.py",  # ML Prototype
            # Procurement APIs
            "gsa_calc_integration.py",
            "fpds_integration.py", 
            "sam_opportunities_integration.py",
            "unified_procurement_enrichment.py"
        ]
        
        return [self.repo_path / f for f in keep_files if (self.repo_path / f).exists()]
    
    def move_to_backup(self, file_path, reason="duplicate"):
        """Move file to backup directory"""
        if not file_path.exists():
            return
            
        backup_path = self.backup_dir / file_path.name
        counter = 1
        while backup_path.exists():
            name_parts = file_path.name.split('.')
            backup_path = self.backup_dir / f"{name_parts[0]}_{counter}.{'.'.join(name_parts[1:])}"
            counter += 1
        
        shutil.move(str(file_path), str(backup_path))
        self.cleanup_report.append(f"MOVED: {file_path} → {backup_path} ({reason})")
        print(f"📦 Moved: {file_path.name} → backup ({reason})")
    
    def clean_duplicate_apis(self):
        """Clean up duplicate API files"""
        print("\n🧹 Cleaning duplicate API files...")
        
        main_files = self.identify_main_files()
        main_file_names = {f.name for f in main_files}
        
        duplicates = self.identify_duplicate_apis()
        
        for duplicate in duplicates:
            if duplicate.name not in main_file_names:
                self.move_to_backup(duplicate, "duplicate_api")
    
    def clean_backup_files(self):
        """Remove obvious backup files"""
        print("\n🗂️ Cleaning backup files...")
        
        backup_patterns = [
            "*_backup*",
            "*_old*", 
            "*_broken*",
            "*.bak",
            "*~"
        ]
        
        for pattern in backup_patterns:
            for file_path in self.repo_path.rglob(pattern):
                if file_path.is_file():
                    self.move_to_backup(file_path, "backup_file")
    
    def organize_structure(self):
        """Organize remaining files into proper structure"""
        print("\n📁 Organizing file structure...")
        
        # Ensure proper directory structure exists
        directories = [
            "src/api/v1/endpoints/ml",
            "src/services/ml", 
            "src/services/procurement",
            "tests/unit/ml",
            "tests/integration"
        ]
        
        for directory in directories:
            (self.repo_path / directory).mkdir(parents=True, exist_ok=True)
            print(f"📂 Created directory: {directory}")
    
    def create_ml_integration_structure(self):
        """Create proper structure for ML integration"""
        print("\n🤖 Setting up ML integration structure...")
        
        ml_files = {
            "src/services/ml/__init__.py": "",
            "src/services/ml/models.py": """# ML Models Service
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from quick_start_ml_prototype import KBIProcurementMLPrototype

class MLModelService:
    def __init__(self):
        self.ml_prototype = KBIProcurementMLPrototype()
        self.models_loaded = False
    
    def load_models(self):
        \"\"\"Load trained ML models\"\"\"
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
        \"\"\"Predict contract success probability\"\"\"
        if not self.load_models():
            raise Exception("Models not available")
        return self.ml_prototype.predict_contract_success(company_data)
    
    def detect_anomalies(self, company_data):
        \"\"\"Detect anomalies in company data\"\"\"
        if not self.load_models():
            raise Exception("Models not available")
        return self.ml_prototype.detect_anomalies(company_data)
""",
            "src/api/v1/endpoints/ml/__init__.py": "",
            "src/api/v1/endpoints/ml/predictions.py": """# ML Predictions API Endpoints
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.services.ml.models import MLModelService

router = APIRouter(prefix="/ml", tags=["ML Predictions"])

# Pydantic models for request/response
class CompanyData(BaseModel):
    procurement_intelligence_score: float = 50.0
    gsa_calc_found: bool = False
    fpds_found: bool = False
    sam_opportunities_found: bool = False
    sam_entity_found: bool = True
    gsa_avg_rate: float = 100.0
    fpds_total_value: float = 100000.0
    fpds_total_contracts: int = 5
    sam_total_matches: int = 3
    agency_diversity: int = 2
    contractor_network_size: int = 10
    years_in_business: float = 10.0
    small_business: bool = True
    veteran_owned: bool = False
    woman_owned: bool = False
    state: str = "VA"
    primary_naics: int = 541511

class PredictionResponse(BaseModel):
    success_probability: float
    predicted_success: bool
    confidence: str

class AnomalyResponse(BaseModel):
    anomaly_score: float
    is_anomaly: bool
    risk_level: str

# Initialize ML service
ml_service = MLModelService()

@router.post("/predict-success", response_model=PredictionResponse)
async def predict_contract_success(company_data: CompanyData):
    \"\"\"Predict contract success probability for a company\"\"\"
    try:
        result = ml_service.predict_contract_success(company_data.dict())
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/detect-anomalies", response_model=AnomalyResponse)
async def detect_anomalies(company_data: CompanyData):
    \"\"\"Detect anomalies in company procurement patterns\"\"\"
    try:
        result = ml_service.detect_anomalies(company_data.dict())
        return AnomalyResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

@router.get("/health")
async def ml_health():
    \"\"\"Check ML service health\"\"\"
    try:
        models_loaded = ml_service.load_models()
        return {
            "status": "healthy" if models_loaded else "unhealthy",
            "models_loaded": models_loaded,
            "service": "KBI Labs ML Service"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "service": "KBI Labs ML Service"
        }
"""
        }
        
        for file_path, content in ml_files.items():
            full_path = self.repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"✨ Created: {file_path}")
    
    def generate_cleanup_report(self):
        """Generate cleanup report"""
        print("\n📊 Generating cleanup report...")
        
        report_path = self.repo_path / "CLEANUP_REPORT.md"
        
        report_content = f"""# KBI Labs Repository Cleanup Report

## Summary
- **Files processed**: {len(self.cleanup_report)}
- **Backup directory**: {self.backup_dir}
- **Date**: {Path().cwd()}

## Actions Taken

### Files Moved to Backup
"""
        
        for action in self.cleanup_report:
            report_content += f"- {action}\n"
        
        report_content += """
## New Structure Created

### ML Integration
- `src/services/ml/` - ML model services
- `src/api/v1/endpoints/ml/` - ML API endpoints
- Integrated ML predictions into FastAPI

### Next Steps
1. Test ML endpoints: `/api/v1/ml/predict-success`
2. Verify main application still works: `src/main.py`
3. Run ML dashboard: `streamlit run streamlit_ml_dashboard.py`
4. Integration testing with existing APIs

## Files Preserved
- `src/main.py` - Main FastAPI application
- `streamlit_ml_dashboard.py` - ML Dashboard
- All ML models and procurement APIs
- Core KBI Labs functionality
"""
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"📄 Cleanup report saved: {report_path}")
    
    def run_cleanup(self):
        """Run complete cleanup process"""
        print("🚀 Starting KBI Labs Repository Cleanup")
        print("=" * 50)
        
        self.create_backup_dir()
        self.clean_backup_files()
        self.clean_duplicate_apis()
        self.organize_structure()
        self.create_ml_integration_structure()
        self.generate_cleanup_report()
        
        print("\n✅ Cleanup completed successfully!")
        print(f"📊 {len(self.cleanup_report)} files processed")
        print(f"🔗 ML integration structure created")
        print("\n🚀 Next steps:")
        print("1. Test ML endpoints: python -m pytest tests/")
        print("2. Run main API: python src/main.py")
        print("3. Test ML dashboard: streamlit run streamlit_ml_dashboard.py")

if __name__ == "__main__":
    cleanup = KBIRepositoryCleanup()
    cleanup.run_cleanup()