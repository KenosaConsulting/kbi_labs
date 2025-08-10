#!/usr/bin/env python3
"""
Authentication and Authorization Middleware
JWT-based authentication with role-based access control
"""

import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import secrets

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Generate a secure random key for development (should be set in production)
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning("SECRET_KEY not set, generated temporary key for development")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Security scheme
security = HTTPBearer()

class UserRoles:
    """User role definitions"""
    ADMIN = "admin"
    USER = "user" 
    ANALYST = "analyst"
    READONLY = "readonly"

class AuthManager:
    """Authentication and authorization manager"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

# Dependency functions for FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    try:
        payload = AuthManager.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Here you would typically fetch user details from database
        # For now, returning payload data
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "is_active": payload.get("is_active", True)
        }
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user (extends get_current_user with active check)"""
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user

def require_roles(required_roles: List[str]):
    """Decorator factory for role-based access control"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_active_user)):
        user_roles = current_user.get("roles", [])
        
        # Admin has access to everything
        if UserRoles.ADMIN in user_roles:
            return current_user
            
        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        return current_user
    
    return role_checker

# Convenience dependencies for common role requirements
require_admin = require_roles([UserRoles.ADMIN])
require_analyst = require_roles([UserRoles.ADMIN, UserRoles.ANALYST])
require_user = require_roles([UserRoles.ADMIN, UserRoles.ANALYST, UserRoles.USER])

# Optional authentication (for public endpoints that can benefit from user context)
async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get user if authenticated, None otherwise (for optional auth endpoints)"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
            
        token = auth_header[7:]  # Remove "Bearer " prefix
        payload = AuthManager.verify_token(token)
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "is_active": payload.get("is_active", True)
        }
        
    except Exception:
        # Silent fail for optional auth
        return None

class RateLimiter:
    """Simple in-memory rate limiter (should use Redis in production)"""
    def __init__(self):
        self.requests = {}
        
    async def check_rate_limit(self, identifier: str, limit: int = 100, window: int = 60) -> bool:
        """Check if request is within rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window)
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= limit:
            return False
            
        # Add current request
        self.requests[identifier].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

async def check_rate_limit(request: Request) -> None:
    """Rate limiting dependency"""
    # Use IP address as identifier (could use user ID for authenticated requests)
    client_ip = request.client.host
    limit = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))
    
    if not await rate_limiter.check_rate_limit(client_ip, limit):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )