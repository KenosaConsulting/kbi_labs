#!/bin/bash

# Demo API users for testing
echo "Creating demo API users..."

# Trial user
curl -X POST http://localhost:3001/api-umbrella/v1/users \
  -H "X-Admin-Auth-Token: YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "email": "trial@example.com",
      "first_name": "Trial",
      "last_name": "User",
      "use_description": "Testing trial tier",
      "throttle_by_ip": false,
      "roles": ["trial-tier"],
      "settings": {
        "rate_limit": 100,
        "rate_limit_mode": "custom"
      }
    }
  }'

echo "✅ Demo users created"
