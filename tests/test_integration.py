#!/usr/bin/env python3
"""
Integration Test Suite
End-to-end integration tests for complete API workflows
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_server import app
from backend.auth.middleware import AuthManager

client = TestClient(app)

class TestCompleteUserWorkflow:
    """Test complete user workflows from login to data enrichment"""
    
    def test_complete_admin_workflow(self):
        """Test complete admin workflow: login -> create user -> manage users -> enrichment"""
        
        # Step 1: Admin login
        admin_login = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Step 2: Check admin user info
        user_info = client.get("/auth/me", headers=admin_headers)
        assert user_info.status_code == 200
        assert "admin" in user_info.json()["roles"]
        
        # Step 3: Create new user
        new_user_data = {
            "email": "analyst@kbilabs.com",
            "password": "analyst123",
            "roles": ["analyst", "user"],
            "is_active": True
        }
        
        create_response = client.post("/auth/users", json=new_user_data, headers=admin_headers)
        assert create_response.status_code == 200
        created_user = create_response.json()
        
        # Step 4: List users to verify creation
        users_list = client.get("/auth/users", headers=admin_headers)
        assert users_list.status_code == 200
        users = users_list.json()["users"]
        
        analyst_user = next((u for u in users if u["email"] == "analyst@kbilabs.com"), None)
        assert analyst_user is not None
        assert "analyst" in analyst_user["roles"]
        
        # Step 5: Test new user login
        analyst_login = client.post("/auth/login", json={
            "email": "analyst@kbilabs.com",
            "password": "analyst123"
        })
        assert analyst_login.status_code == 200
        analyst_token = analyst_login.json()["access_token"]
        analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
        
        # Step 6: Test data enrichment with analyst user
        enrichment_request = {
            "agency_code": "9700",
            "agency_name": "Department of Defense",
            "data_types": ["budget", "personnel"],
            "enrichment_depth": "standard",
            "priority": "normal"
        }
        
        enrichment_response = client.post(
            "/api/data-enrichment/enrich",
            json=enrichment_request,
            headers=analyst_headers
        )
        assert enrichment_response.status_code == 200
        enrichment_data = enrichment_response.json()
        assert enrichment_data["success"] is True
        assert "job_id" in enrichment_data
        
        # Step 7: Admin updates user permissions
        user_update = {
            "roles": ["user"],  # Remove analyst role
            "is_active": True
        }
        
        update_response = client.put(
            "/auth/users/analyst@kbilabs.com",
            json=user_update,
            headers=admin_headers
        )
        assert update_response.status_code == 200
        
        # Step 8: Verify updated permissions (analyst endpoints should fail)
        # Note: This would require analyst-specific endpoints to test properly
        
        # Step 9: Admin logout
        admin_logout = client.post("/auth/logout", headers=admin_headers)
        assert admin_logout.status_code == 200
    
    def test_user_data_enrichment_workflow(self):
        """Test complete data enrichment workflow for regular user"""
        
        # Step 1: Login as admin to create regular user
        admin_login = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Step 2: Create regular user
        user_data = {
            "email": "user@kbilabs.com",
            "password": "user123",
            "roles": ["user"],
            "is_active": True
        }
        
        client.post("/auth/users", json=user_data, headers=admin_headers)
        
        # Step 3: Login as regular user
        user_login = client.post("/auth/login", json={
            "email": "user@kbilabs.com",
            "password": "user123"
        })
        assert user_login.status_code == 200
        user_token = user_login.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Step 4: Get supported agencies
        agencies_response = client.get("/api/data-enrichment/agencies", headers=user_headers)
        assert agencies_response.status_code == 200
        agencies = agencies_response.json()["agencies"]
        assert len(agencies) > 0
        
        # Step 5: Get supported data types
        data_types_response = client.get("/api/data-enrichment/data-types", headers=user_headers)
        assert data_types_response.status_code == 200
        data_types = data_types_response.json()["data_types"]
        assert len(data_types) > 0
        
        # Step 6: Submit enrichment request
        enrichment_request = {
            "agency_code": "7000",
            "agency_name": "Department of Homeland Security",
            "data_types": ["contracts", "organizational"],
            "enrichment_depth": "comprehensive",
            "priority": "high"
        }
        
        enrichment_response = client.post(
            "/api/data-enrichment/enrich",
            json=enrichment_request,
            headers=user_headers
        )
        assert enrichment_response.status_code == 200
        enrichment_data = enrichment_response.json()
        
        assert enrichment_data["success"] is True
        assert "job_id" in enrichment_data
        assert enrichment_data["status"] in ["queued", "processing", "completed"]
        
        # Step 7: User tries to access admin endpoints (should fail)
        admin_endpoints = [
            "/auth/users",
            "/auth/generate-api-key"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=user_headers)
            assert response.status_code == 403
        
        # Step 8: User changes password
        password_change = {
            "current_password": "user123",
            "new_password": "newuser123"
        }
        
        change_response = client.post("/auth/change-password", json=password_change, headers=user_headers)
        assert change_response.status_code == 200
        
        # Step 9: Login with new password
        new_login = client.post("/auth/login", json={
            "email": "user@kbilabs.com",
            "password": "newuser123"
        })
        assert new_login.status_code == 200
        
        # Step 10: Old password should fail
        old_login = client.post("/auth/login", json={
            "email": "user@kbilabs.com",
            "password": "user123"
        })
        assert old_login.status_code == 401

class TestHealthCheckIntegration:
    """Test health check integration with other services"""
    
    def test_health_check_comprehensive(self):
        """Test comprehensive health check functionality"""
        
        # Test health check
        health_response = client.get("/health")
        
        # Should return either healthy or degraded status
        assert health_response.status_code in [200, 500]
        
        health_data = health_response.json()
        
        # Verify response structure
        assert "status" in health_data
        assert "service" in health_data
        assert "version" in health_data
        assert "environment" in health_data
        assert "services" in health_data
        assert "timestamp" in health_data
        
        # Verify service checks
        services = health_data["services"]
        assert "database" in services
        assert "enrichment_system" in services
        assert "api_server" in services
        
        # API server should always be running if we got a response
        assert services["api_server"] == "running"
    
    def test_root_endpoint_integration(self):
        """Test root endpoint provides correct information"""
        
        root_response = client.get("/")
        assert root_response.status_code == 200
        
        root_data = root_response.json()
        
        # Verify response structure
        assert "message" in root_data
        assert "version" in root_data
        assert "environment" in root_data
        assert "status" in root_data
        assert "endpoints" in root_data
        
        # Verify endpoints are listed
        endpoints = root_data["endpoints"]
        assert "health" in endpoints
        assert "enrichment" in endpoints
        
        # Verify each listed endpoint is accessible
        for endpoint_name, endpoint_path in endpoints.items():
            if endpoint_name in ["docs", "test_page"]:  # These might not exist in production
                continue
                
            if endpoint_name == "enrichment":
                # This requires auth, so we expect 403
                response = client.get(endpoint_path)
                assert response.status_code in [403, 422]  # No auth or method not allowed
            else:
                response = client.get(endpoint_path)
                assert response.status_code in [200, 405, 422]  # Success or method not allowed

class TestErrorHandling:
    """Test error handling across different scenarios"""
    
    def test_database_connection_error_handling(self):
        """Test graceful handling of database connection errors"""
        
        # Health check should handle database errors gracefully
        health_response = client.get("/health")
        
        # Should return response even if database is down
        assert health_response.status_code in [200, 500]
        
        if health_response.status_code == 500:
            health_data = health_response.json()
            assert "error" in health_data or "services" in health_data
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in requests"""
        
        # Get auth token first
        login_response = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Send invalid JSON
        invalid_json_response = client.post(
            "/api/data-enrichment/enrich",
            data="{invalid json}",
            headers=headers
        )
        
        # Should return proper error response
        assert invalid_json_response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test handling of requests with missing required fields"""
        
        # Get auth token
        login_response = client.post("/auth/login", json={
            "email": "admin@kbilabs.com", 
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Send request without required agency_code
        incomplete_request = {
            "agency_name": "Some Agency",
            "data_types": ["budget"]
        }
        
        response = client.post(
            "/api/data-enrichment/enrich",
            json=incomplete_request,
            headers=headers
        )
        
        assert response.status_code == 422
        
        error_data = response.json()
        assert "detail" in error_data

class TestConcurrency:
    """Test concurrent request handling"""
    
    def test_concurrent_login_requests(self):
        """Test handling of concurrent login requests"""
        import threading
        import time
        
        results = []
        
        def login_attempt():
            response = client.post("/auth/login", json={
                "email": "admin@kbilabs.com",
                "password": "admin123"
            })
            results.append(response.status_code)
        
        # Start multiple concurrent login requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=login_attempt)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All should succeed (or some may be rate limited)
        success_count = sum(1 for status in results if status == 200)
        rate_limited_count = sum(1 for status in results if status == 429)
        
        # At least some should succeed
        assert success_count > 0
        
        # Total should equal number of requests
        assert len(results) == 5
    
    def test_concurrent_enrichment_requests(self):
        """Test handling of concurrent enrichment requests"""
        
        # Login first
        login_response = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        import threading
        results = []
        
        def enrichment_request():
            enrichment_data = {
                "agency_code": "9700",
                "data_types": ["budget"]
            }
            response = client.post(
                "/api/data-enrichment/enrich",
                json=enrichment_data,
                headers=headers
            )
            results.append(response.status_code)
        
        # Start concurrent enrichment requests
        threads = []
        for _ in range(3):  # Fewer to avoid overwhelming rate limits
            thread = threading.Thread(target=enrichment_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should handle concurrent requests properly
        success_count = sum(1 for status in results if status == 200)
        rate_limited_count = sum(1 for status in results if status == 429)
        
        # At least some should succeed
        assert success_count > 0 or rate_limited_count > 0
        assert len(results) == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])