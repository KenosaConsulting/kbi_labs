from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional

security = HTTPBearer()

class UserContext:
    PE_FIRM = "pe_firm"
    SMB_OWNER = "smb_owner"
    API_DEVELOPER = "api_developer"
    CONSULTANT = "consultant"

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token with user context"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "your-secret-key", algorithm="HS256")
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return {
            "user_id": payload.get("sub"),
            "context": payload.get("context", UserContext.API_DEVELOPER),
            "permissions": payload.get("permissions", [])
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
