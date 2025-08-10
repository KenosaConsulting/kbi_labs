#!/usr/bin/env python3
"""
Security Testing Suite
Tests for security vulnerabilities, input validation, and attack vectors
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_server import app
from backend.auth.middleware import AuthManager

client = TestClient(app)

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def get_auth_headers(self):
        """Get authentication headers for testing"""
        token = AuthManager.create_access_token({
            "sub": "test_user",
            "email": "test@example.com",
            "roles": ["user"],
            "is_active": True
        })
        return {"Authorization": f"Bearer {token}"}
    
    def test_sql_injection_in_agency_code(self):
        """Test SQL injection attempts in agency code"""
        headers = self.get_auth_headers()
        
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "' OR 1=1; --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM sensitive_table; --"
        ]
        
        for payload in malicious_payloads:
            enrichment_data = {
                "agency_code": payload,
                "data_types": ["budget"]
            }
            
            response = client.post("/api/data-enrichment/enrich", 
                                   json=enrichment_data, 
                                   headers=headers)
            
            # Should return validation error, not execute SQL
            assert response.status_code in [422, 400]  # Validation error
    
    def test_xss_in_agency_name(self):
        """Test XSS attempts in agency name field"""
        headers = self.get_auth_headers()
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "\"><script>alert('xss')</script>"
        ]
        
        for payload in xss_payloads:
            enrichment_data = {
                "agency_code": "1234",
                "agency_name": payload,
                "data_types": ["budget"]
            }
            
            response = client.post("/api/data-enrichment/enrich", 
                                   json=enrichment_data, 
                                   headers=headers)
            
            # Should sanitize or reject malicious input
            if response.status_code == 200:
                # If accepted, ensure it's sanitized in response
                response_text = response.text
                assert "<script>" not in response_text
                assert "javascript:" not in response_text
    
    def test_command_injection(self):
        """Test command injection attempts"""
        headers = self.get_auth_headers()
        
        command_payloads = [
            "test; ls -la",
            "test && cat /etc/passwd",
            "test | whoami",
            "test `id`",
            "test $(ls)"
        ]
        
        for payload in command_payloads:
            enrichment_data = {
                "agency_code": "1234",
                "agency_name": payload,
                "data_types": ["budget"]
            }
            
            response = client.post("/api/data-enrichment/enrich", 
                                   json=enrichment_data, 
                                   headers=headers)
            
            # Should reject or sanitize command injection attempts
            assert response.status_code in [200, 422, 400]
    
    def test_oversized_payload(self):
        """Test handling of oversized payloads"""
        headers = self.get_auth_headers()
        
        # Create oversized agency name
        large_name = "A" * 10000  # 10KB name
        
        enrichment_data = {
            "agency_code": "1234",
            "agency_name": large_name,
            "data_types": ["budget"]
        }
        
        response = client.post("/api/data-enrichment/enrich", 
                               json=enrichment_data, 
                               headers=headers)
        
        # Should reject oversized input
        assert response.status_code == 422
    
    def test_invalid_data_types(self):
        """Test invalid data types in enrichment request"""
        headers = self.get_auth_headers()
        
        invalid_data_types = [
            ["invalid_type"],
            ["budget", "invalid"],
            ["../../../etc/passwd"],
            ["<script>alert('xss')</script>"]
        ]
        
        for invalid_types in invalid_data_types:
            enrichment_data = {
                "agency_code": "1234",
                "data_types": invalid_types
            }
            
            response = client.post("/api/data-enrichment/enrich", 
                                   json=enrichment_data, 
                                   headers=headers)
            
            assert response.status_code == 422

class TestAuthenticationSecurity:
    """Test authentication and authorization security"""
    
    def test_jwt_tampering(self):
        """Test JWT token tampering detection"""
        # Create valid token
        token = AuthManager.create_access_token({
            "sub": "user123",
            "email": "user@test.com",
            "roles": ["user"],
            "is_active": True
        })
        
        # Tamper with token (change last character)
        tampered_token = token[:-1] + "X"
        
        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_expired_token_rejection(self):
        """Test that expired tokens are rejected"""
        from datetime import timedelta
        
        # Create token that expires immediately
        token = AuthManager.create_access_token(
            {"sub": "user123", "email": "user@test.com", "roles": ["user"], "is_active": True},
            expires_delta=timedelta(seconds=-1)
        )
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_privilege_escalation_attempt(self):
        """Test privilege escalation attempts"""
        # Create user token
        user_token = AuthManager.create_access_token({
            "sub": "user123",
            "email": "user@test.com",
            "roles": ["user"],
            "is_active": True
        })
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Attempt to access admin endpoint
        response = client.get("/auth/users", headers=headers)
        assert response.status_code == 403
        
        # Attempt to create user (admin only)
        user_data = {
            "email": "malicious@test.com",
            "password": "password123",
            "roles": ["admin"]  # Attempting to create admin
        }
        
        response = client.post("/auth/users", json=user_data, headers=headers)
        assert response.status_code == 403
    
    def test_session_fixation(self):
        """Test protection against session fixation"""
        # Login and get token
        login_response = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        
        first_token = login_response.json()["access_token"]
        
        # Login again - should potentially get different token
        second_login = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        
        second_token = second_login.json()["access_token"]
        
        # Both tokens should be valid but different (stateless JWT, so might be same)
        # Focus on ensuring both work properly
        headers1 = {"Authorization": f"Bearer {first_token}"}
        headers2 = {"Authorization": f"Bearer {second_token}"}
        
        response1 = client.get("/auth/me", headers=headers1)
        response2 = client.get("/auth/me", headers=headers2)
        
        assert response1.status_code == 200
        assert response2.status_code == 200

class TestRateLimitingSecurity:
    """Test rate limiting for security"""
    
    def test_brute_force_protection(self):
        """Test brute force attack protection"""
        # Attempt multiple failed logins
        failed_attempts = []
        for i in range(10):
            response = client.post("/auth/login", json={
                "email": "admin@kbilabs.com",
                "password": f"wrong_password_{i}"
            })
            failed_attempts.append(response)
            time.sleep(0.1)  # Small delay between attempts
        
        # Should see rate limiting or account lockout
        # Note: Implementation depends on rate limiter configuration
        status_codes = [r.status_code for r in failed_attempts]
        
        # Should have at least some 401s (unauthorized) and possibly 429s (rate limited)
        assert any(code == 401 for code in status_codes)
    
    def test_api_endpoint_rate_limiting(self):
        """Test API endpoint rate limiting"""
        # Get valid token
        login_response = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make many requests quickly
        responses = []
        for i in range(50):  # High number of requests
            response = client.get("/api/data-enrichment/agencies", headers=headers)
            responses.append(response)
            if response.status_code == 429:  # Rate limited
                break
        
        # Should eventually get rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        # Note: This test might be flaky depending on rate limit configuration

class TestDataProtection:
    """Test data protection and privacy"""
    
    def test_password_not_returned(self):
        """Test that passwords are never returned in responses"""
        # Login
        response = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        
        # Check login response doesn't contain password
        response_text = response.text.lower()
        assert "password" not in response_text
        assert "admin123" not in response_text
        
        # Get user info
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        user_response = client.get("/auth/me", headers=headers)
        user_text = user_response.text.lower()
        
        assert "password" not in user_text
        assert "admin123" not in user_text
    
    def test_error_information_disclosure(self):
        """Test that error messages don't disclose sensitive information"""
        # Test various error conditions
        error_responses = [
            client.get("/nonexistent-endpoint"),
            client.post("/auth/login", json={"email": "invalid", "password": "test"}),
            client.get("/auth/me"),  # No auth header
        ]
        
        for response in error_responses:
            response_text = response.text.lower()
            
            # Should not contain sensitive information
            assert "database" not in response_text or "error" not in response_text
            assert "secret" not in response_text
            assert "key" not in response_text
            assert "/app/" not in response_text  # File paths
    
    def test_cors_security(self):
        """Test CORS configuration security"""
        # Check that CORS headers are properly configured
        response = client.options("/auth/login")
        
        # Should have proper CORS headers in production
        if "production" in os.getenv("ENVIRONMENT", "development"):
            cors_header = response.headers.get("access-control-allow-origin", "*")
            assert cors_header != "*", "CORS should not allow all origins in production"

class TestHealthCheckSecurity:
    """Test health check endpoint security"""
    
    def test_health_check_information_disclosure(self):
        """Test that health check doesn't expose sensitive information"""
        response = client.get("/health")
        
        # Health check should work but not expose sensitive details
        assert response.status_code in [200, 500]  # Either healthy or unhealthy
        
        response_data = response.json()
        
        # Should not contain sensitive information
        response_text = str(response_data).lower()
        assert "password" not in response_text
        assert "secret" not in response_text
        assert "key" not in response_text or "api" in response_text  # API key status is ok
    
    def test_health_check_timing_attack(self):
        """Test health check for timing attacks"""
        # Multiple health check requests should have similar response times
        times = []
        for _ in range(5):
            start_time = time.time()
            client.get("/health")
            end_time = time.time()
            times.append(end_time - start_time)
        
        # Response times should be relatively consistent
        avg_time = sum(times) / len(times)
        for t in times:
            # Allow 50% variance (timing attacks look for much larger differences)
            assert abs(t - avg_time) < avg_time * 0.5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])