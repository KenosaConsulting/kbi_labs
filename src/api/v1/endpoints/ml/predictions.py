# ML Predictions API Endpoints
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
    """Predict contract success probability for a company"""
    try:
        result = ml_service.predict_contract_success(company_data.dict())
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/detect-anomalies", response_model=AnomalyResponse)
async def detect_anomalies(company_data: CompanyData):
    """Detect anomalies in company procurement patterns"""
    try:
        result = ml_service.detect_anomalies(company_data.dict())
        return AnomalyResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

@router.get("/health")
async def ml_health():
    """Check ML service health"""
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
