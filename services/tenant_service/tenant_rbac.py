"""
Tenant Role-Based Access Control (RBAC).
Defines hospital-specific clinical roles, permissions, and hierarchical authorization checks.
"""

from enum import Enum
from typing import Set, Dict, List


class Permission(str, Enum):
    # Clinical Data Permissions
    VIEW_PATIENT_RECORDS = "clinical:records:read"
    EDIT_PATIENT_RECORDS = "clinical:records:write"
    SIGN_CLINICAL_ORDERS = "clinical:orders:sign"
    ADMINISTER_MEDICATION = "clinical:medication:administer"
    TRIGGER_EMERGENCY_OVERRIDE = "clinical:emergency:break_glass"
    ACCESS_AI_COPILOT = "ai:copilot:query"

    # Administrative Permissions
    MANAGE_PHYSICIAN_SEATS = "admin:users:manage"
    VIEW_TENANT_METRICS = "admin:analytics:read"
    MANAGE_BILLING = "admin:billing:manage"
    VIEW_AUDIT_LOGS = "admin:audit:read"
    CONFIG_EHR_INTEGRATION = "admin:ehr:configure"
    MANAGE_TENANTS = "admin:tenants:manage"


class HospitalRole(str, Enum):
    SYSTEM_SUPER_ADMIN = "SYSTEM_SUPER_ADMIN"
    ATTENDING_PHYSICIAN = "ATTENDING_PHYSICIAN"
    RESIDENT_PHYSICIAN = "RESIDENT_PHYSICIAN"
    TRIAGE_NURSE = "TRIAGE_NURSE"
    BEDSIDE_NURSE = "BEDSIDE_NURSE"
    HOSPITAL_ADMINISTRATOR = "HOSPITAL_ADMINISTRATOR"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    PATIENT = "PATIENT"
    CAREGIVER = "CAREGIVER"


ROLE_PERMISSIONS: Dict[HospitalRole, Set[Permission]] = {
    HospitalRole.SYSTEM_SUPER_ADMIN: {
        Permission.MANAGE_TENANTS,
        Permission.MANAGE_PHYSICIAN_SEATS,
        Permission.VIEW_TENANT_METRICS,
        Permission.MANAGE_BILLING,
        Permission.VIEW_AUDIT_LOGS,
        Permission.CONFIG_EHR_INTEGRATION,
        Permission.TRIGGER_EMERGENCY_OVERRIDE,
    },
    HospitalRole.ATTENDING_PHYSICIAN: {
        Permission.VIEW_PATIENT_RECORDS,
        Permission.EDIT_PATIENT_RECORDS,
        Permission.SIGN_CLINICAL_ORDERS,
        Permission.TRIGGER_EMERGENCY_OVERRIDE,
        Permission.ACCESS_AI_COPILOT,
        Permission.VIEW_TENANT_METRICS,
    },
    HospitalRole.RESIDENT_PHYSICIAN: {
        Permission.VIEW_PATIENT_RECORDS,
        Permission.EDIT_PATIENT_RECORDS,
        Permission.ACCESS_AI_COPILOT,
        Permission.TRIGGER_EMERGENCY_OVERRIDE,
    },
    HospitalRole.TRIAGE_NURSE: {
        Permission.VIEW_PATIENT_RECORDS,
        Permission.EDIT_PATIENT_RECORDS,
        Permission.TRIGGER_EMERGENCY_OVERRIDE,
        Permission.ACCESS_AI_COPILOT,
    },
    HospitalRole.BEDSIDE_NURSE: {
        Permission.VIEW_PATIENT_RECORDS,
        Permission.ADMINISTER_MEDICATION,
        Permission.TRIGGER_EMERGENCY_OVERRIDE,
        Permission.ACCESS_AI_COPILOT,
    },
    HospitalRole.HOSPITAL_ADMINISTRATOR: {
        Permission.MANAGE_PHYSICIAN_SEATS,
        Permission.VIEW_TENANT_METRICS,
        Permission.MANAGE_BILLING,
        Permission.CONFIG_EHR_INTEGRATION,
        Permission.VIEW_AUDIT_LOGS,
    },
    HospitalRole.COMPLIANCE_OFFICER: {
        Permission.VIEW_AUDIT_LOGS,
        Permission.VIEW_TENANT_METRICS,
    },
    HospitalRole.PATIENT: {
        Permission.VIEW_PATIENT_RECORDS,
        Permission.ACCESS_AI_COPILOT,
    },
    HospitalRole.CAREGIVER: {
        Permission.VIEW_PATIENT_RECORDS,
        Permission.ACCESS_AI_COPILOT,
    },
}


class TenantRBAC:
    """Enforces role-based permissions scoped to a specific tenant."""

    @staticmethod
    def get_permissions(role: HospitalRole) -> Set[Permission]:
        return ROLE_PERMISSIONS.get(role, set())

    @staticmethod
    def has_permission(role: HospitalRole, required_permission: Permission) -> bool:
        allowed = ROLE_PERMISSIONS.get(role, set())
        return required_permission in allowed

    @staticmethod
    def authorize(role: HospitalRole, required_permission: Permission) -> bool:
        if not TenantRBAC.has_permission(role, required_permission):
            raise PermissionError(
                f"Role '{role.value}' lacks required permission: '{required_permission.value}'"
            )
        return True
