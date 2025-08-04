"""
KBI Labs Foundation Authentication System
Simple, clean auth that can be enhanced for production
"""

from fastapi import Header, HTTPException, Depends
from typing import Optional, Dict, Any
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FoundationAuth:
    """Simple authentication system for KBI Labs platform"""
    
    def __init__(self):
        # Environment-based configuration
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.development_mode = self.environment in ["development", "dev", "local"]
        
        # Simple API keys for development
        self.api_keys = {
            "dev-key-admin": {"role": "admin", "name": "Development Admin"},
            "dev-key-user": {"role": "user", "name": "Development User"},
            "demo-key": {"role": "demo", "name": "Demo User"},
            "test-token": {"role": "user", "name": "Test User"}
        }
        
        logger.info(f"Foundation Auth initialized - Environment: {self.environment}")
        if self.development_mode:
            logger.info("🔓 Development mode: Relaxed authentication enabled")
    
    async def get_current_user(self, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
        """Get current user with development-friendly fallback"""
        
        # Development mode: Allow anonymous access
        if self.development_mode and not authorization:
            return {
                "type": "development",
                "role": "admin",  # Full access in development
                "name": "Development User",
                "id": "dev-user",
                "authenticated": True,
                "timestamp": datetime.now().isoformat()
            }
        
        # Check for API key
        if authorization:
            # Handle Bearer token format
            token = authorization.replace("Bearer ", "").replace("bearer ", "")
            
            # Check against our simple API keys
            if token in self.api_keys:
                user_info = self.api_keys[token].copy()
                user_info.update({
                    "type": "api_key",
                    "authenticated": True,
                    "id": f"user-{token[-4:]}",  # Last 4 chars of key
                    "timestamp": datetime.now().isoformat()
                })
                return user_info
        
        # Production mode: Require authentication
        if not self.development_mode:
            raise HTTPException(
                status_code=401, 
                detail="Authentication required. Use Bearer token or API key."
            )
        
        # Fallback for development
        return {
            "type": "anonymous",
            "role": "user",
            "name": "Anonymous User",
            "id": "anonymous",
            "authenticated": False,
            "timestamp": datetime.now().isoformat()
        }
    
    async def require_auth(self, current_user: Dict = Depends(lambda: auth.get_current_user())) -> Dict:
        """Require authenticated user"""
        if not current_user.get("authenticated", False):
            if self.development_mode:
                # In development, promote anonymous to authenticated
                current_user["authenticated"] = True
                current_user["role"] = "user"
                logger.debug("🔓 Development mode: Auto-authenticating user")
            else:
                raise HTTPException(status_code=401, detail="Authentication required")
        
        return current_user
    
    async def require_role(self, required_role: str):
        """Require specific user role"""
        async def role_checker(current_user: Dict = Depends(self.get_current_user)):
            user_role = current_user.get("role", "anonymous")
            
            # Admin has access to everything
            if user_role == "admin":
                return current_user
            
            # Check specific role
            if user_role != required_role:
                if self.development_mode:
                    logger.debug(f"🔓 Development mode: Role '{required_role}' bypassed (user has '{user_role}')")
                    return current_user
                else:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Role '{required_role}' required. You have '{user_role}'"
                    )
            
            return current_user
        return role_checker
    
    async def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication system status"""
        return {
            "system": "KBI Labs Foundation Auth",
            "environment": self.environment,
            "development_mode": self.development_mode,
            "available_keys": len(self.api_keys) if self.development_mode else "hidden",
            "features": {
                "api_keys": True,
                "role_based_access": True,
                "development_bypass": self.development_mode,
                "production_ready": not self.development_mode
            },
            "usage": {
                "header": "Authorization: Bearer <key>",
                "development": "No auth required in development mode",
                "production": "API key or JWT token required"
            }
        }

# Global instance
auth = FoundationAuth()

# Convenience functions for backward compatibility
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Get current user - foundation auth"""
    return await auth.get_current_user(authorization)

async def require_auth(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Require authenticated user - foundation auth"""
    return await auth.require_auth(current_user)

def require_role(role: str):
    """Require specific role - foundation auth"""
    return auth.require_role(role)