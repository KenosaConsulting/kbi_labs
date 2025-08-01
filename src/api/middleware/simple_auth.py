#!/usr/bin/env python3
import hashlib
import secrets
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET", "development-jwt-secret-change-in-production")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(
        {"user_id": user_id, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def verify_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except:
        return None

def generate_api_key() -> str:
    return f"kbi_{secrets.token_urlsafe(32)}"

SUBSCRIPTION_TIERS = {
    'free': {'calls_per_day': 100, 'max_results': 50},
    'pro': {'calls_per_day': 5000, 'max_results': 1000},
    'enterprise': {'calls_per_day': 50000, 'max_results': -1}
}
