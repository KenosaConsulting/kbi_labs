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
