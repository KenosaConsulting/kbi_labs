"""Authentication API Router"""
from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
async def login():
    """User login"""
    return {"message": "Auth endpoint - to be implemented"}
