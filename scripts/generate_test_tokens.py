#!/usr/bin/env python3
"""Generate test JWT tokens for different user contexts"""

import jwt
from datetime import datetime, timedelta

JWT_SECRET = "your-secret-key"  # Same as in API
JWT_ALGORITHM = "HS256"

def generate_token(user_type, subscription_tier="professional"):
    payload = {
        "sub": f"test-{user_type.lower()}-user",
        "aud": "alpha" if user_type == "PE_FIRM" else "compass",
        "context": {
            "user_type": user_type,
            "firm_id": "test-firm-123",
            "permissions": ["read", "analyze", "export"],
            "subscription_tier": subscription_tier,
            "preferences": {
                "default_view": "acquisition" if user_type == "PE_FIRM" else "operations",
                "risk_tolerance": "moderate"
            }
        },
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

# Generate tokens
print("🔐 Test JWT Tokens")
print("==================")
print()

pe_token = generate_token("PE_FIRM", "enterprise")
print("PE Firm Token (Enterprise):")
print(pe_token)
print()

smb_token = generate_token("SMB_OWNER", "professional")
print("SMB Owner Token (Professional):")
print(smb_token)
print()

api_token = generate_token("API_DEVELOPER", "enterprise")
print("API Developer Token:")
print(api_token)
print()

print("Usage:")
print('curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v2/companies/{uei}/intelligence')
