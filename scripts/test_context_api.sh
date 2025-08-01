#!/bin/bash
# Test context-aware API responses

echo "🧪 Testing Context-Aware API"
echo "==========================="

# Generate tokens
echo "Generating test tokens..."
PE_TOKEN=$(docker exec kbi_api python scripts/generate_test_tokens.py | grep -A1 "PE Firm Token" | tail -1)
SMB_TOKEN=$(docker exec kbi_api python scripts/generate_test_tokens.py | grep -A1 "SMB Owner Token" | tail -1)

# Test PE context
echo ""
echo "Testing PE Firm Context:"
echo "------------------------"
curl -s -H "Authorization: Bearer $PE_TOKEN" \
     http://localhost:8000/api/v2/companies/TEST123/intelligence | \
     python -m json.tool

# Test SMB context
echo ""
echo "Testing SMB Owner Context:"
echo "--------------------------"
curl -s -H "Authorization: Bearer $SMB_TOKEN" \
     http://localhost:8000/api/v2/companies/TEST123/intelligence | \
     python -m json.tool

# Test search endpoint
echo ""
echo "Testing Search (PE Context):"
echo "----------------------------"
curl -s -H "Authorization: Bearer $PE_TOKEN" \
     "http://localhost:8000/api/v2/intelligence/search?state=FL&min_succession_risk=7" | \
     python -m json.tool
