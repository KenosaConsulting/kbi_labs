#!/bin/bash

echo "🔧 Fixing intelligence platform files..."

# First, check if files are empty
PROCESSOR_SIZE=$(stat -c%s "src/data_processors/dsbs_processor.py")
API_SIZE=$(stat -c%s "src/api/v2/intelligence.py")

echo "Current file sizes:"
echo "- dsbs_processor.py: $PROCESSOR_SIZE bytes"
echo "- intelligence.py: $API_SIZE bytes"

if [ $PROCESSOR_SIZE -lt 1000 ]; then
    echo "❌ dsbs_processor.py is too small, needs to be recreated"
fi

if [ $API_SIZE -lt 1000 ]; then
    echo "❌ intelligence.py is too small, needs to be recreated"
fi

# Create a temporary fix by creating minimal working files
echo "📝 Creating minimal working intelligence files..."

# Create a minimal working dsbs_processor.py
cat > src/data_processors/dsbs_processor.py << 'PROCESSOR_EOF'
"""Minimal DSBS Processor for testing"""
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class UserContext:
    user_type: str
    subscription_tier: str
    permissions: List[str]
    preferences: Dict[str, any]
    
    @property
    def is_pe_firm(self):
        return self.user_type == 'PE_FIRM'
    
    @property
    def is_smb_owner(self):
        return self.user_type == 'SMB_OWNER'

class DSBSProcessor:
    """Placeholder processor"""
    def __init__(self):
        pass
    
    def get_company_intelligence(self, uei: str, user_context: UserContext) -> Dict:
        return {
            "company": {"uei": uei, "name": "Test Company"},
            "intelligence": {"status": "Processor needs full implementation"},
            "metadata": {"context": user_context.user_type}
        }

class IntelligenceResponseBuilder:
    """Placeholder response builder"""
    def __init__(self, user_context: UserContext):
        self.context = user_context
PROCESSOR_EOF

# Create a minimal working intelligence.py
cat > src/api/v2/intelligence.py << 'API_EOF'
"""Minimal Intelligence API for testing"""
from fastapi import APIRouter, HTTPException
from typing import Dict

router = APIRouter(prefix="/api/v2", tags=["intelligence"])

@router.get("/health")
async def health_check():
    return {"status": "Intelligence API is running (minimal mode)"}

@router.get("/companies/{identifier}/intelligence")
async def get_company_intelligence(identifier: str):
    return {
        "company": {"identifier": identifier},
        "message": "Full implementation needed - see artifacts",
        "status": "minimal_mode"
    }
API_EOF

echo "✅ Created minimal working files"
echo ""
echo "🚀 Next steps:"
echo "1. The API should now start without import errors"
echo "2. You need to copy the full content from the artifacts"
echo "3. Use the provided artifacts to replace these minimal files"

