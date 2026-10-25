"""
Enterprise RBAC Engine.
Evaluates role memberships and enforces permission boundaries with role inheritance.
"""

from typing import Set, Dict, List
from .permissions import SecurityPermission


ROLE_HIERARCHY: Dict[str, Set[SecurityPermission]] = {
    "CHIEF_MEDICAL_OFFICER": {
        SecurityPermission.READ_PHI,
        SecurityPermission.WRITE_PHI,
        SecurityPermission.EXPORT_PHI,
        SecurityPermission.ORDER_MEDICATION,
        SecurityPermission.ADMINISTER_MEDICATION,
        SecurityPermission.SIGN_NOTE,
        SecurityPermission.OVERRIDE_EMERGENCY,
        SecurityPermission.QUERY_AI_COPILOT,
        SecurityPermission.VIEW_AI_CITATIONS,
        SecurityPermission.VIEW_AUDIT_LOGS,
    },
    "ATTENDING_PHYSICIAN": {
        SecurityPermission.READ_PHI,
        SecurityPermission.WRITE_PHI,
        SecurityPermission.ORDER_MEDICATION,
        SecurityPermission.SIGN_NOTE,
        SecurityPermission.OVERRIDE_EMERGENCY,
        SecurityPermission.QUERY_AI_COPILOT,
        SecurityPermission.VIEW_AI_CITATIONS,
    },
    "RESIDENT_PHYSICIAN": {
        SecurityPermission.READ_PHI,
        SecurityPermission.WRITE_PHI,
        SecurityPermission.ORDER_MEDICATION,
        SecurityPermission.QUERY_AI_COPILOT,
        SecurityPermission.VIEW_AI_CITATIONS,
    },
    "REGISTERED_NURSE": {
        SecurityPermission.READ_PHI,
        SecurityPermission.WRITE_PHI,
        SecurityPermission.ADMINISTER_MEDICATION,
        SecurityPermission.OVERRIDE_EMERGENCY,
        SecurityPermission.QUERY_AI_COPILOT,
    },
    "COMPLIANCE_AUDITOR": {
        SecurityPermission.VIEW_AUDIT_LOGS,
        SecurityPermission.VIEW_AI_CITATIONS,
    },
    "SYSTEM_ADMIN": {
        SecurityPermission.MANAGE_USERS,
        SecurityPermission.MANAGE_KEYS,
        SecurityPermission.VIEW_AUDIT_LOGS,
    },
}


class EnterpriseRBAC:
    """Evaluates role-based permissions."""

    @classmethod
    def get_role_permissions(cls, role_name: str) -> Set[SecurityPermission]:
        return ROLE_HIERARCHY.get(role_name.upper(), set())

    @classmethod
    def check_access(cls, user_roles: List[str], required_permission: SecurityPermission) -> bool:
        for role in user_roles:
            permissions = cls.get_role_permissions(role)
            if required_permission in permissions:
                return True
        return False
