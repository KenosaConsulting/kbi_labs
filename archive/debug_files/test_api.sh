#!/bin/bash
# Test the SMB Intelligence API

# Set tokens
export PE_TOKEN="pe_firm_token_2024"
export SMB_TOKEN="smb_owner_token_2024"

# Use a real UEI from your data
REAL_UEI="TJB8LVJ12B53"  # 1 TARHEEL CANINE TRAINING INC from Virginia

echo "🧪 Testing API with real company data"
echo "===================================="
echo "Testing with: 1 TARHEEL CANINE TRAINING INC"
echo "UEI: $REAL_UEI"

# Health check
echo -e "\n❤️ API Health Check:"
curl -s "http://localhost:8004/api/v2/health" | python3 -m json.tool

# PE Firm View
echo -e "\n📊 PE Firm Intelligence View:"
curl -s -H "Authorization: Bearer $PE_TOKEN" \
     "http://localhost:8004/api/v2/companies/$REAL_UEI/intelligence" | python3 -m json.tool

# SMB Owner View
echo -e "\n💡 SMB Owner Intelligence View:"
curl -s -H "Authorization: Bearer $SMB_TOKEN" \
     "http://localhost:8004/api/v2/companies/$REAL_UEI/intelligence" | python3 -m json.tool

# Search test
echo -e "\n🔍 Search Test (Florida companies):"
curl -s -H "Authorization: Bearer $PE_TOKEN" \
     "http://localhost:8004/api/v2/search?state=Florida&limit=3" | python3 -m json.tool

# Market insights
echo -e "\n📈 Market Insights (PE Firm view):"
curl -s -H "Authorization: Bearer $PE_TOKEN" \
     "http://localhost:8004/api/v2/market-insights" | python3 -m json.tool
