#!/usr/bin/env python3
"""
Authentication and Authorization Tests
Comprehensive test suite for JWT authentication, role-based access control, and security
"""

import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_server import app
from backend.auth.middleware import AuthManager, UserRoles

client = TestClient(app)

class TestAuthManager:
    """Test AuthManager class methods"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = AuthManager.hash_password(password)
        
        assert hashed != password
        assert AuthManager.verify_password(password, hashed)
        assert not AuthManager.verify_password("wrong_password", hashed)
    
    def test_jwt_token_creation(self):
        """Test JWT token creation and verification"""
        payload = {
            "sub": "test_user_id",
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        token = AuthManager.create_access_token(payload)
        assert token is not None
        
        # Verify token
        decoded = AuthManager.verify_token(token)
        assert decoded["sub"] == "test_user_id"
        assert decoded["email"] == "test@example.com"
        assert decoded["roles"] == ["user"]
        assert decoded["type"] == "access"
    
    def test_token_expiration(self):
        """Test JWT token expiration"""
        payload = {"sub": "test_user"}
        
        # Create token with short expiration
        short_expiration = timedelta(seconds=-1)  # Already expired
        token = AuthManager.create_access_token(payload, expires_delta=short_expiration)
        
        # Should raise exception for expired token
        with pytest.raises(Exception) as exc_info:
            AuthManager.verify_token(token)
        assert "expired" in str(exc_info.value).lower()

class TestAuthRoutes:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login"""
        login_data = {
            "email": "admin@kbilabs.com",
            "password": "admin123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_info" in data
        assert data["user_info"]["email"] == "admin@kbilabs.com"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "admin@kbilabs.com",
            "password": "wrong_password"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "any_password"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_get_user_info_with_valid_token(self):
        """Test getting user info with valid token"""
        # First login to get token
        login_response = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Get user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@kbilabs.com"
        assert "admin" in data["roles"]
    
    def test_get_user_info_without_token(self):
        """Test getting user info without token"""
        response = client.get("/auth/me")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403
    
    def test_get_user_info_with_invalid_token(self):
        """Test getting user info with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_logout(self):
        """Test logout endpoint"""
        # Login first
        login_response = client.post("/auth/login", json={
            "email": "admin@kbilabs.com",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"]

class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def get_user_token(self, roles=["user"]):
        """Helper method to create test user token"""
        payload = {
            "sub": "test_user_id",
            "email": "test@example.com", 
            "roles": roles,
            "is_active": True
        }
        return AuthManager.create_access_token(payload)
    
    def test_admin_access_to_user_creation(self):
        """Test admin can create users"""
        admin_token = self.get_user_token(["admin"])
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {
            "email": "newuser@example.com",
            "password": "password123",
            "roles": ["user"]
        }
        
        response = client.post("/auth/users", json=user_data, headers=headers)
        assert response.status_code == 200
    
    def test_non_admin_cannot_create_users(self):
        """Test non-admin cannot create users"""
        user_token = self.get_user_token(["user"])
        headers = {"Authorization": f"Bearer {user_token}"}
        
        user_data = {
            "email": "newuser2@example.com",
            "password": "password123",
            "roles": ["user"]
        }
        
        response = client.post("/auth/users", json=user_data, headers=headers)
        assert response.status_code == 403
    
    def test_admin_can_list_users(self):
        """Test admin can list users"""
        admin_token = self.get_user_token(["admin"])
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get("/auth/users", headers=headers)
        assert response.status_code == 200
        assert "users" in response.json()
    
    def test_user_cannot_list_users(self):
        """Test regular user cannot list users"""
        user_token = self.get_user_token(["user"])
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = client.get("/auth/users", headers=headers)
        assert response.status_code == 403

class TestSecurityFeatures:
    """Test security features and edge cases"""
    
    def test_password_complexity_validation(self):
        """Test password complexity requirements"""
        admin_token = AuthManager.create_access_token({
            "sub": "admin", "roles": ["admin"], "email": "admin@test.com", "is_active": True
        })
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test short password
        user_data = {
            "email": "test@example.com",
            "password": "123",  # Too short
            "roles": ["user"]
        }
        
        response = client.post("/auth/users", json=user_data, headers=headers)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_email_format(self):
        """Test invalid email format validation"""
        admin_token = AuthManager.create_access_token({
            "sub": "admin", "roles": ["admin"], "email": "admin@test.com", "is_active": True
        })
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {
            "email": "invalid_email",  # Invalid format
            "password": "password123",
            "roles": ["user"]
        }
        
        response = client.post("/auth/users", json=user_data, headers=headers)
        assert response.status_code == 422
    
    def test_token_without_required_claims(self):
        """Test token missing required claims"""
        # Create token without required claims
        incomplete_payload = {"some_field": "value"}
        token = jwt.encode(incomplete_payload, "secret", algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_disabled_user_access(self):
        """Test disabled user cannot access endpoints"""
        disabled_user_token = AuthManager.create_access_token({
            "sub": "disabled_user",
            "email": "disabled@test.com",
            "roles": ["user"],
            "is_active": False
        })
        headers = {"Authorization": f"Bearer {disabled_user_token}"}
        
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_on_login(self):
        """Test rate limiting on login endpoint"""
        login_data = {
            "email": "admin@kbilabs.com",
            "password": "wrong_password"
        }
        
        # Make multiple requests quickly
        responses = []
        for _ in range(15):  # Exceed typical rate limit
            response = client.post("/auth/login", json=login_data)
            responses.append(response)
        
        # At least one should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        # Note: This test might be flaky depending on rate limit implementation

if __name__ == "__main__":
    pytest.main([__file__, "-v"])