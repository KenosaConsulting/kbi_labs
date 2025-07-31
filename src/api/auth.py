"""Authentication module"""
from typing import Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Get current user from auth token"""
    # For now, return a mock user - implement real auth later
    return {
        "id": "user123",
        "email": "user@example.com",
        "roles": ["admin"]
    }
