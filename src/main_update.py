# Add this to your existing main.py

from src.api.v2.intelligence import router as intelligence_router

# Add to your FastAPI app
app.include_router(intelligence_router)

# Add startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Initializing KBI Labs Intelligence Platform...")
    
    # Test database connections
    try:
        # Test PostgreSQL
        from sqlalchemy import create_engine
        engine = create_engine(os.getenv('DATABASE_URL'))
        engine.connect()
        logger.info("✅ PostgreSQL connected")
        
        # Test MongoDB
        from pymongo import MongoClient
        mongo = MongoClient(os.getenv('MONGODB_URL'))
        mongo.server_info()
        logger.info("✅ MongoDB connected")
        
        # Test Redis
        import redis
        r = redis.from_url(os.getenv('REDIS_URL'))
        r.ping()
        logger.info("✅ Redis connected")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
