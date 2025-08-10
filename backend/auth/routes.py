#!/usr/bin/env python3
"""
Authentication Routes
Login, logout, user management endpoints
"""

import logging
from typing import Dict, Any
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, validator
import secrets

from .middleware import AuthManager, get_current_active_user, require_admin

logger = logging.getLogger(__name__)

# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict[str, Any]

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    roles: list = ["user"]
    is_active: bool = True
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserUpdate(BaseModel):
    email: EmailStr = None
    roles: list = None
    is_active: bool = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory user store (should be database in production)
USERS_DB = {
    "admin@kbilabs.com": {
        "user_id": "admin-001",
        "email": "admin@kbilabs.com",
        "hashed_password": AuthManager.hash_password("admin123"),  # Default admin password
        "roles": ["admin"],
        "is_active": True
    }
}

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    
    user = USERS_DB.get(login_data.email)
    
    if not user or not AuthManager.verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Create access token
    token_data = {
        "sub": user["user_id"],
        "email": user["email"],
        "roles": user["roles"],
        "is_active": user["is_active"]
    }
    
    access_token = AuthManager.create_access_token(token_data)
    
    logger.info(f"User {user['email']} logged in successfully")
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=24 * 3600,  # 24 hours in seconds
        user_info={
            "user_id": user["user_id"],
            "email": user["email"], 
            "roles": user["roles"]
        }
    )

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Logout user (client-side token removal in stateless JWT)"""
    logger.info(f"User {current_user['email']} logged out")
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Get current authenticated user information"""
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "roles": current_user["roles"],
        "is_active": current_user["is_active"]
    }

@router.post("/users", dependencies=[Depends(require_admin)])
async def create_user(user_data: UserCreate, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Create a new user (admin only)"""
    
    if user_data.email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Generate user ID
    user_id = f"user-{secrets.token_hex(8)}"
    
    # Create user
    USERS_DB[user_data.email] = {
        "user_id": user_id,
        "email": user_data.email,
        "hashed_password": AuthManager.hash_password(user_data.password),
        "roles": user_data.roles,
        "is_active": user_data.is_active
    }
    
    logger.info(f"User {user_data.email} created by admin {current_user['email']}")
    
    return {
        "user_id": user_id,
        "email": user_data.email,
        "roles": user_data.roles,
        "is_active": user_data.is_active
    }

@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """List all users (admin only)"""
    
    users = []
    for email, user_data in USERS_DB.items():
        users.append({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "roles": user_data["roles"],
            "is_active": user_data["is_active"]
        })
    
    return {"users": users, "total": len(users)}

@router.put("/users/{user_email}", dependencies=[Depends(require_admin)])
async def update_user(
    user_email: str,
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Update user information (admin only)"""
    
    if user_email not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = USERS_DB[user_email]
    
    # Update fields
    if user_update.email and user_update.email != user_email:
        # Handle email change
        USERS_DB[user_update.email] = USERS_DB.pop(user_email)
        user["email"] = user_update.email
        user_email = user_update.email
    
    if user_update.roles is not None:
        user["roles"] = user_update.roles
        
    if user_update.is_active is not None:
        user["is_active"] = user_update.is_active
    
    logger.info(f"User {user_email} updated by admin {current_user['email']}")
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "roles": user["roles"],
        "is_active": user["is_active"]
    }

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Change user password"""
    
    user = USERS_DB.get(current_user["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not AuthManager.verify_password(password_change.current_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user["hashed_password"] = AuthManager.hash_password(password_change.new_password)
    
    logger.info(f"Password changed for user {current_user['email']}")
    
    return {"message": "Password changed successfully"}

@router.post("/generate-api-key", dependencies=[Depends(require_admin)])
async def generate_api_key(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Generate API key for system integration (admin only)"""
    
    api_key = f"kbi_{secrets.token_urlsafe(32)}"
    
    # In production, store this in database with associated permissions
    logger.info(f"API key generated by admin {current_user['email']}")
    
    return {
        "api_key": api_key,
        "message": "Store this API key securely - it won't be shown again"
    }