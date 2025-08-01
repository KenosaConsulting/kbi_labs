#!/usr/bin/env python3
"""Minimal KBI Labs API for testing enrichment"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our routers
from src.api.routers import enrichment

app = FastAPI(
    title="KBI Labs API (Minimal)",
    version="1.0.0",
    docs_url="/docs"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(enrichment.router, prefix="/api/v3")

@app.get("/")
async def root():
    return {"message": "KBI Labs API (Minimal) - Use /docs for API documentation"}

@app.get("/health/")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
