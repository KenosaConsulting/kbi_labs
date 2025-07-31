"""API Dependencies - Authentication, rate limiting, etc."""
from fastapi import Header, HTTPException, Depends
from typing import Optional, Dict
import jwt
from src.config.settings import get_settings

settings = get_settings()

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """Extract and validate user from JWT token"""
    if not authorization:
        return {"type": "public", "id": "anonymous"}
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

async def require_auth(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Require authenticated user"""
    if current_user.get("type") == "public":
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user

async def require_role(role: str):
    """Require specific user role"""
    async def role_checker(current_user: Dict = Depends(get_current_user)):
        if current_user.get("role") != role:
            raise HTTPException(status_code=403, detail=f"Role '{role}' required")
        return current_user
    return role_checker
