from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import secrets
import hashlib
from datetime import datetime, timedelta
import jwt
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    subscription_tier: str

class APIKeyCreate(BaseModel):
    name: str

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_api_key() -> str:
    """Generate secure API key"""
    return f"kbi_{secrets.token_urlsafe(32)}"

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    existing = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "subscription_tier": user.subscription_tier
    }

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "subscription_tier": user.subscription_tier
    }

@router.post("/api-keys", response_model=dict)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new API key for user"""
    # Check user's tier limits
    existing_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).count()
    
    tier_limits = {'free': 1, 'pro': 5, 'enterprise': -1}
    limit = tier_limits.get(current_user.subscription_tier, 1)
    
    if limit != -1 and existing_keys >= limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API key limit reached for {current_user.subscription_tier} tier"
        )
    
    # Create new API key
    api_key = APIKey(
        key=generate_api_key(),
        name=key_data.name,
        user_id=current_user.id,
        rate_limit=SUBSCRIPTION_TIERS[current_user.subscription_tier]['api_calls_per_day']
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return {
        "api_key": api_key.key,
        "name": api_key.name,
        "created_at": api_key.created_at.isoformat()
    }

@router.get("/usage-stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's usage statistics"""
    # Get today's usage
    today = datetime.utcnow().date()
    today_usage = db.query(UsageLog).filter(
        UsageLog.user_id == current_user.id,
        UsageLog.timestamp >= today
    ).count()
    
    # Get tier limits
    tier_info = SUBSCRIPTION_TIERS[current_user.subscription_tier]
    
    return {
        "user_id": current_user.id,
        "subscription_tier": current_user.subscription_tier,
        "api_calls_today": today_usage,
        "api_calls_limit": tier_info['api_calls_per_day'],
        "features": tier_info['features']
    }

# Middleware to track API usage
async def track_usage(request: Request, user_id: int, db: Session):
    """Track API usage for billing and analytics"""
    usage_log = UsageLog(
        user_id=user_id,
        endpoint=str(request.url.path),
        ip_address=request.client.host
    )
    db.add(usage_log)
    db.commit()

# Rate limiting decorator
def rate_limit(user: User, db: Session):
    """Check if user has exceeded rate limit"""
    today = datetime.utcnow().date()
    today_usage = db.query(UsageLog).filter(
        UsageLog.user_id == user.id,
        UsageLog.timestamp >= today
    ).count()
    
    tier_info = SUBSCRIPTION_TIERS[user.subscription_tier]
    if today_usage >= tier_info['api_calls_per_day']:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily API limit exceeded. Please upgrade your plan."
        )
