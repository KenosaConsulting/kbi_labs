#!/usr/bin/env python3
import sqlite3
import hashlib
import secrets
import jwt
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Initialize SQLite database
def init_auth_db():
    conn = sqlite3.connect('/app/data/auth.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        subscription_tier TEXT DEFAULT 'free'
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        name TEXT,
        user_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        rate_limit INTEGER DEFAULT 1000
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        endpoint TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        response_time REAL,
        status_code INTEGER,
        ip_address TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on import
init_auth_db()

SECRET_KEY = os.getenv("JWT_SECRET", "development-jwt-secret-change-in-production")
ALGORITHM = "HS256"

class UserRegister(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(
        {"user_id": user_id, "username": username, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None

@router.post("/register")
async def register(user: UserRegister):
    conn = sqlite3.connect('/app/data/auth.db')
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute(
            "SELECT id FROM users WHERE email = ? OR username = ?",
            (user.email, user.username)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user
        cursor.execute(
            "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
            (user.email, user.username, hash_password(user.password))
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        token = create_token(user_id, user.username)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id,
            "username": user.username,
            "subscription_tier": "free"
        }
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        conn.close()

@router.post("/login")
async def login(user: UserLogin):
    conn = sqlite3.connect('/app/data/auth.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, password_hash, subscription_tier FROM users WHERE username = ?",
            (user.username,)
        )
        result = cursor.fetchone()
        
        if not result or result[1] != hash_password(user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_id, _, tier = result
        token = create_token(user_id, user.username)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id,
            "username": user.username,
            "subscription_tier": tier
        }
        
    finally:
        conn.close()

@router.post("/api-keys")
async def create_api_key(name: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = sqlite3.connect('/app/data/auth.db')
    cursor = conn.cursor()
    
    try:
        api_key = f"kbi_{secrets.token_urlsafe(32)}"
        cursor.execute(
            "INSERT INTO api_keys (key, name, user_id) VALUES (?, ?, ?)",
            (api_key, name, payload["user_id"])
        )
        conn.commit()
        
        return {"api_key": api_key, "name": name}
        
    finally:
        conn.close()

@router.get("/verify")
async def verify_auth(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if authorization.startswith("Bearer kbi_"):
        # API key verification
        api_key = authorization.split(" ")[1]
        conn = sqlite3.connect('/app/data/auth.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT u.id, u.username, u.subscription_tier FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.key = ? AND ak.is_active = 1",
            (api_key,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return {
            "user_id": result[0],
            "username": result[1],
            "subscription_tier": result[2],
            "auth_type": "api_key"
        }
    
    elif authorization.startswith("Bearer "):
        # JWT token verification
        token = authorization.split(" ")[1]
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {
            "user_id": payload["user_id"],
            "username": payload["username"],
            "auth_type": "jwt_token"
        }
    
    raise HTTPException(status_code=401, detail="Invalid authorization header")

# Create auth router instance
auth_router = router
