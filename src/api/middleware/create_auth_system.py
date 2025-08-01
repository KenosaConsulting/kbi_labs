#!/usr/bin/env python3
"""
User Authentication System for KBI Labs
Includes: User registration, login, API keys, usage tracking
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timedelta
import secrets
import hashlib
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(50), default='free')  # free, pro, enterprise
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")

class APIKey(Base):
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False)
    name = Column(String(100))
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=1000)  # requests per day
    
    user = relationship("User", back_populates="api_keys")

class UsageLog(Base):
    __tablename__ = 'usage_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    endpoint = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float)
    status_code = Column(Integer)
    ip_address = Column(String(45))
    
    user = relationship("User", back_populates="usage_logs")

# Subscription tiers configuration
SUBSCRIPTION_TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'api_calls_per_day': 100,
        'features': ['basic_search', 'limited_export'],
        'max_results': 50
    },
    'pro': {
        'name': 'Professional',
        'price': 99,
        'api_calls_per_day': 5000,
        'features': ['advanced_search', 'full_export', 'api_access', 'analytics'],
        'max_results': 1000
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': 499,
        'api_calls_per_day': 50000,
        'features': ['all_features', 'priority_support', 'custom_integration', 'white_label'],
        'max_results': -1  # unlimited
    }
}

# Create tables
if __name__ == '__main__':
    # Use PostgreSQL for production
    engine = create_engine('postgresql://kbiuser:kbipass@localhost:5432/kbi_compass')
    Base.metadata.create_all(engine)
    print("✅ Authentication tables created!")
