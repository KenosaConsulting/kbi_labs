"""Basic API tests"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app

client = TestClient(app)

def test_health_check():
    """Test health endpoint"""
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "KBI Labs" in response.json()["message"]

def test_companies_requires_auth():
    """Test that companies endpoint requires authentication"""
    response = client.get("/api/v2/companies/")
    assert response.status_code == 403

def test_companies_with_auth():
    """Test companies endpoint with auth"""
    headers = {"Authorization": "Bearer test-token"}
    response = client.get("/api/v2/companies/?limit=5", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "companies" in data
    assert "total" in data

def test_analytics_overview():
    """Test analytics endpoint"""
    headers = {"Authorization": "Bearer test-token"}
    response = client.get("/api/v2/analytics/overview", headers=headers)
    assert response.status_code == 200
