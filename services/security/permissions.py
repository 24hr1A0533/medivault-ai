"""
Enterprise Security Permissions and Clinical Scopes.
Defines fine-grained authorization primitives for hospital operations.
"""

from enum import Enum


class SecurityPermission(str, Enum):
    # Patient Data
    READ_PHI = "phi:read"
    WRITE_PHI = "phi:write"
    DELETE_PHI = "phi:delete"
    EXPORT_PHI = "phi:export"

    # Clinical Actions
    ORDER_MEDICATION = "clinical:order:medication"
    ADMINISTER_MEDICATION = "clinical:administer:medication"
    SIGN_NOTE = "clinical:sign:note"
    OVERRIDE_EMERGENCY = "clinical:emergency:break_glass"

    # AI & Intelligence
    QUERY_AI_COPILOT = "ai:copilot:query"
    VIEW_AI_CITATIONS = "ai:citations:view"
    OVERRIDE_GUARDRAILS = "ai:guardrails:override"

    # Administration
    MANAGE_USERS = "admin:users:manage"
    MANAGE_KEYS = "admin:kms:manage"
    VIEW_AUDIT_LOGS = "admin:audit:view"


class ClinicalScope(str, Enum):
    EMERGENCY_DEPARTMENT = "ED"
    INTENSIVE_CARE_UNIT = "ICU"
    INPATIENT_WARD = "INPATIENT"
    OUTPATIENT_CLINIC = "OUTPATIENT"
    SURGICAL_SUITE = "OR"
    REMOTE_TELEHEALTH = "TELEHEALTH"
