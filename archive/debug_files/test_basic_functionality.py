#!/usr/bin/env python3
"""
Basic functionality tests for KBI Labs
Tests core functionality without external dependencies
"""
import pytest
import sys
import os
import json
from fastapi.testclient import TestClient

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that basic imports work"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_simple_api():
    """Test our simple API"""
    from simple_api_test import app
    
    client = TestClient(app)
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "test_endpoints" in data
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Test companies endpoint
    response = client.get("/api/test/companies")
    assert response.status_code == 200
    data = response.json()
    assert "companies" in data
    assert data["count"] == 2
    assert len(data["companies"]) == 2

def test_file_structure():
    """Test that important files exist"""
    required_files = [
        "requirements.txt",
        "docker-compose.yml",
        "README.md",
        "src/main.py"
    ]
    
    for file_path in required_files:
        assert os.path.exists(file_path), f"Required file missing: {file_path}"

def test_configuration_files():
    """Test that configuration files are valid"""
    # Test docker-compose.yml is valid YAML
    try:
        import yaml
        with open("docker-compose.yml", "r") as f:
            yaml.safe_load(f)
    except ImportError:
        # Skip if PyYAML not installed
        pass
    except Exception as e:
        pytest.fail(f"docker-compose.yml is invalid: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])