#!/usr/bin/env python3
"""
Secure Secret Generator for KBI Labs
Generates cryptographically secure secrets for production use
"""

import secrets
import string
import os
from pathlib import Path

def generate_secure_key(length: int = 32) -> str:
    """Generate a cryptographically secure random key"""
    return secrets.token_urlsafe(length)

def generate_password(length: int = 16) -> str:
    """Generate a secure password with mixed characters"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def create_env_file():
    """Create a .env file with secure defaults"""
    
    # Generate secure secrets
    jwt_secret = generate_secure_key(32)
    secret_key = generate_secure_key(32)
    postgres_password = generate_password(20)
    grafana_password = generate_password(16)
    
    env_content = f"""# KBI Labs Environment Configuration
# Generated on {os.popen('date').read().strip()}
# KEEP THIS FILE SECURE - DO NOT COMMIT TO VERSION CONTROL

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
SECRET_KEY={secret_key}
JWT_SECRET={jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
POSTGRES_USER=kbi_user
POSTGRES_PASSWORD={postgres_password}
POSTGRES_DB=kbi_labs
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://${{POSTGRES_USER}}:${{POSTGRES_PASSWORD}}@${{POSTGRES_HOST}}:${{POSTGRES_PORT}}/${{POSTGRES_DB}}

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_URL=redis://${{REDIS_HOST}}:${{REDIS_PORT}}

# =============================================================================
# KAFKA CONFIGURATION
# =============================================================================
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=kbi_labs
ZOOKEEPER_HOST=localhost
ZOOKEEPER_PORT=2181

# =============================================================================
# API KEYS & EXTERNAL SERVICES
# =============================================================================
# REPLACE THESE WITH YOUR ACTUAL API KEYS
SAM_GOV_API_KEY=your-sam-gov-api-key-here
USASPENDING_API_KEY=your-usaspending-api-key-here
CENSUS_API_KEY=your-census-api-key-here
FRED_API_KEY=your-fred-api-key-here
USPTO_API_KEY=your-uspto-api-key-here
NSF_API_KEY=your-nsf-api-key-here
GOOGLE_PLACES_API_KEY=your-google-places-api-key-here
HUNTER_API_KEY=your-hunter-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# =============================================================================
# PROCESSING SETTINGS
# =============================================================================
BATCH_SIZE=50
MAX_CONCURRENT_REQUESTS=25

# =============================================================================
# RATE LIMITING
# =============================================================================
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=200

# =============================================================================
# MONITORING & OBSERVABILITY
# =============================================================================
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD={grafana_password}

# =============================================================================
# CACHING
# =============================================================================
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000

# =============================================================================
# PRODUCTION SETTINGS
# =============================================================================
RELOAD_ON_CHANGE=false
ENABLE_CORS=false
CORS_ORIGINS=https://yourdomain.com
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
"""

    # Write to .env file
    env_path = Path(__file__).parent.parent / '.env'
    
    # Check if .env already exists
    if env_path.exists():
        backup_path = env_path.with_suffix('.env.backup')
        print(f"⚠️  Backing up existing .env to {backup_path}")
        env_path.rename(backup_path)
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created secure .env file at {env_path}")
    print(f"🔐 Generated secrets:")
    print(f"   - JWT Secret: {jwt_secret[:10]}... (length: {len(jwt_secret)})")
    print(f"   - App Secret: {secret_key[:10]}... (length: {len(secret_key)})")
    print(f"   - DB Password: {postgres_password[:4]}*** (length: {len(postgres_password)})")
    print(f"   - Grafana Password: {grafana_password[:4]}*** (length: {len(grafana_password)})")
    print()
    print("🔒 IMPORTANT SECURITY NOTES:")
    print("   - Update the API keys with your actual keys")
    print("   - Never commit .env files to version control")
    print("   - Store these secrets securely")
    print("   - Rotate secrets regularly in production")

if __name__ == "__main__":
    create_env_file()