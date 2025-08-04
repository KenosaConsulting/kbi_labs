"""API Dependencies - Foundation Authentication System"""
from src.auth.foundation import get_current_user, require_auth, require_role, auth

# Re-export for backward compatibility
__all__ = ["get_current_user", "require_auth", "require_role", "auth"]
